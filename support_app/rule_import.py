"""Rule import and validation utilities for support_app.

Provides:
- load_rules(path): loads YAML/JSON rules file
- validate_rules(rules): returns (normalized_rules, issues)
- merge_rules(existing, new): merge by id (new overrides existing)

CLI usage:
  python3 support_app/rule_import.py validate support_app/rules.yaml
  python3 support_app/rule_import.py merge support_app/rules.yaml

This is intentionally dependency-light and doesn't require external schema libraries.
"""
from typing import List, Dict, Tuple
import json
import os
import sys

try:
    import yaml
except Exception:
    yaml = None


def load_rules(path: str) -> List[Dict]:
    path = os.path.abspath(path)
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    txt = open(path, 'r', encoding='utf-8').read()
    # try YAML first
    if yaml is not None:
        try:
            loaded = yaml.safe_load(txt)
            if isinstance(loaded, dict) and 'rules' in loaded:
                return loaded['rules']
            if isinstance(loaded, list):
                return loaded
        except Exception:
            pass
    # fallback: try JSON
    try:
        return json.loads(txt)
    except Exception as e:
        raise ValueError(f'Could not parse rules file: {e}')


def _normalize_confidence_raw(c):
    try:
        cf = float(c)
    except Exception:
        return None
    # if 0..1 -> ok
    if 0.0 <= cf <= 1.0:
        return cf
    # if 1..100 -> treat as percent
    if 1.0 < cf <= 100.0:
        return cf / 100.0
    # if >100 treat as 1.0
    if cf > 100.0:
        return 1.0
    return None


def validate_rules(rules: List[Dict]) -> Tuple[List[Dict], List[str]]:
    """Validate and lightly normalize rules.
    Returns (normalized_rules, list_of_issues)
    """
    issues: List[str] = []
    seen_ids = set()
    normalized: List[Dict] = []
    for i, r in enumerate(rules):
        if not isinstance(r, dict):
            issues.append(f'rule[{i}] not a dict')
            continue
        rid = r.get('id')
        if rid is None:
            issues.append(f'rule[{i}] missing id')
            continue
        if rid in seen_ids:
            issues.append(f'duplicate id {rid}')
        seen_ids.add(rid)
        name = r.get('name')
        if not name:
            issues.append(f'rule id={rid} missing name')
        conf = r.get('confidence', 0.5)
        norm = _normalize_confidence_raw(conf)
        if norm is None:
            issues.append(f'rule id={rid} has invalid confidence: {conf}, defaulting to 0.5')
            norm = 0.5
        # ensure conditions list
        conds = r.get('conditions', [])
        if conds is None:
            conds = []
            issues.append(f'rule id={rid} conditions is None, set to []')
        if not isinstance(conds, list):
            issues.append(f'rule id={rid} conditions not a list')
            conds = []
        # validate each condition
        for j, c in enumerate(conds):
            if not isinstance(c, dict):
                issues.append(f'rule id={rid} condition[{j}] not a dict')
                continue
            if 'type' not in c:
                issues.append(f'rule id={rid} condition[{j}] missing type')
            if 'op' not in c:
                issues.append(f'rule id={rid} condition[{j}] missing op, defaulting to ==')
                c['op'] = '=='
            # weight default
            w = c.get('weight', 1.0)
            try:
                c['weight'] = float(w)
            except Exception:
                issues.append(f'rule id={rid} condition[{j}] invalid weight {w}, default 1.0')
                c['weight'] = 1.0
        nr = dict(r)
        nr['confidence'] = norm
        nr['conditions'] = conds
        normalized.append(nr)
    return normalized, issues


def merge_rules(existing: List[Dict], new: List[Dict]) -> List[Dict]:
    by_id = {r['id']: r for r in existing}
    for r in new:
        if not isinstance(r, dict) or 'id' not in r:
            continue
        by_id[r['id']] = r
    # return sorted by id for determinism
    return [by_id[k] for k in sorted(by_id.keys())]


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: python support_app/rule_import.py validate|merge <path_to_rules>')
        sys.exit(2)
    cmd = sys.argv[1]
    path = sys.argv[2]
    try:
        rules = load_rules(path)
    except Exception as e:
        print('Error loading rules:', e)
        sys.exit(1)
    normalized, issues = validate_rules(rules)
    if cmd == 'validate':
        print(f'Loaded {len(rules)} rules from {path}')
        if issues:
            print('Issues found:')
            for it in issues:
                print(' -', it)
            sys.exit(1)
        print('No issues found.')
        sys.exit(0)
    elif cmd == 'merge':
        # merge into current inline rules.yaml if exists
        out_path = os.path.join(os.path.dirname(__file__), 'rules.yaml')
        try:
            existing = load_rules(out_path)
        except Exception:
            existing = []
        merged = merge_rules(existing, normalized)
        # write YAML if possible, else JSON
        if yaml is not None:
            with open(out_path, 'w', encoding='utf-8') as fh:
                yaml.safe_dump(merged, fh, sort_keys=False)
            print('Wrote merged rules to', out_path)
        else:
            with open(out_path, 'w', encoding='utf-8') as fh:
                fh.write(json.dumps(merged, indent=2))
            print('Wrote merged (JSON) rules to', out_path)
        if issues:
            print('Validation issues (see above):')
            for it in issues:
                print(' -', it)
        sys.exit(0)
    else:
        print('Unknown command', cmd)
        sys.exit(2)
