#!/usr/bin/env python3
"""Run a set of canonical test cases against the engine and print results.

This is a lightweight runner for development; not a replacement for unit tests.
"""
import json
from pathlib import Path
import sys

# ensure package path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from support_app.expert_engine import run_diagnosis

TEST_CASES = [
    # 1: High latency
    ({'ping_latency': 250, 'wifi_connected': True}, 'High Latency'),
    # 2: Low throughput
    ({'speed_mbps': 0.2}, 'Low Throughput'),
    # 3: Gateway fail
    ({'gateway_ping': 'fail', 'wifi_connected': True}, 'Router/Gateway Failure'),
    # 4: DNS domain fail
    ({'ping_ip': 'success', 'ping_domain': 'fail'}, 'DNS Resolution Failure'),
    # 5: IP conflict
    ({'ip_conflict_msg': True}, 'IP Address Conflict'),
    # 6: High packet loss
    ({'packet_loss': 12}, 'High Packet Loss'),
    # 7: Failing drive
    ({'disk_health': 30}, 'Failing HDD/SSD'),
    # 8: Overheating
    ({'cpu_temp': 86}, 'Overheating'),
    # 9: No power
    ({'pc_power': False}, 'No Power'),
    # 10: Insufficient data (empty)
    ({}, 'Insufficient Data'),
]


def run():
    for i, (facts, expect) in enumerate(TEST_CASES, start=1):
        res = run_diagnosis(facts)
        top = res[0] if res else None
        print(f"Case {i}: facts={json.dumps(facts)}")
        if top:
            print(f"  Top: {top.get('name')} (score={top.get('score')}, match_ratio={top.get('match_ratio')})")
        else:
            print("  No result")
        print()


if __name__ == '__main__':
    run()
