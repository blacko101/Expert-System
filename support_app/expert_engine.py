# support_app/expert_engine.py
"""
Data-driven rule engine for Network Fault Diagnosis & Computer Troubleshooting.
Rules are dictionaries. Use run_diagnosis(facts) to get ranked diagnoses.
"""

from typing import Any, Dict, List, Callable
import operator
import math

# Operator mapping
_OPS = {
    '==': operator.eq,
    '!=': operator.ne,
    '>=': operator.ge,
    '<=': operator.le,
    '>': operator.gt,
    '<': operator.lt,
    'in': lambda a, b: a in b if a is not None else False,
    'contains': lambda a, b: (b in a) if (isinstance(a, str) and isinstance(b, str)) else False,
    'is_true': lambda a, b: bool(a) is True,
    'is_false': lambda a, b: bool(a) is False,
}

def _check_condition(facts: Dict[str, Any], cond: Dict[str, Any]) -> bool:
    """
    cond keys: type, op, value
    """
    t = cond.get('type')
    op = cond.get('op', '==')
    val = cond.get('value')
    # handle missing fact
    if t not in facts:
        return False
    fact_val = facts[t]
    if op not in _OPS:
        return False
    try:
        # coerce simple numeric strings to numbers for comparison
        if isinstance(fact_val, str) and isinstance(val, (int, float)):
            try:
                if '.' in fact_val:
                    fact_val = float(fact_val)
                else:
                    fact_val = int(fact_val)
            except Exception:
                pass
        return _OPS[op](fact_val, val)
    except Exception:
        return False

def _match_rule(rule: Dict[str, Any], facts: Dict[str, Any]) -> bool:
    """
    Legacy boolean matcher kept for compatibility. New scoring engine uses
    evaluate_rule to compute partial matches. This returns True only when all
    conditions match (same semantics as before).
    """
    conds = rule.get('conditions', [])
    for c in conds:
        if not _check_condition(facts, c):
            return False
    # optional negations
    negs = rule.get('not_conditions', [])
    for c in negs:
        if _check_condition(facts, c):
            return False
    return True


def _normalize_confidence(c: Any) -> float:
    """Normalize confidence into 0.0-1.0 range. Accepts percentages too."""
    try:
        cf = float(c)
    except Exception:
        return 0.5
    if cf <= 0:
        return 0.0
    if cf > 1.0 and cf <= 100.0:
        return cf / 100.0
    if cf > 100.0:
        return 1.0
    return cf


def evaluate_rule(rule: Dict[str, Any], facts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute a weighted match score for a rule given facts.
    Returns a dict with matched_conditions, unmatched_conditions, total_weight,
    matched_weight and score (0..1 scaled by rule confidence).
    Condition schema supports optional 'weight' (defaults to 1.0).
    """
    conds = rule.get('conditions', [])
    total_weight = 0.0
    matched_weight = 0.0
    matched = []
    unmatched = []
    for c in conds:
        w = float(c.get('weight', 1.0))
        total_weight += w
        ok = _check_condition(facts, c)
        if ok:
            matched_weight += w
            matched.append(c)
        else:
            unmatched.append(c)
    # negations: if any not_conditions match, penalize heavily (treat as full mismatch)
    negs = rule.get('not_conditions', [])
    neg_triggered = False
    for c in negs:
        if _check_condition(facts, c):
            neg_triggered = True
            break
    if total_weight == 0:
        match_ratio = 0.0
    else:
        match_ratio = matched_weight / total_weight
    # apply negation: if any negation triggered, set ratio to 0
    if neg_triggered:
        match_ratio = 0.0

    confidence = _normalize_confidence(rule.get('confidence', 0.5))
    score = confidence * match_ratio

    return {
        'matched_conditions': matched,
        'unmatched_conditions': unmatched,
        'total_weight': total_weight,
        'matched_weight': matched_weight,
        'match_ratio': match_ratio,
        'confidence': confidence,
        'score': score,
        'negation_triggered': neg_triggered,
    }


# ---------------------------
# RULES (100 rules)
# ---------------------------
# Each rule has: id, name, confidence (0-1), evidence, remedy, conditions (list)
RULES: List[Dict] = []

# We'll append 100 rules explicitly (network + computer). For clarity they are grouped.
# NETWORK: rules 1-55
RULES.extend([
    # 1
    {"id": 1, "name": "Slow Network — High Latency",
     "confidence": 0.65,
     "evidence": "High ping latency detected",
     "remedy": "Restart router, test wired connection, check ISP congestion.",
     "conditions": [{"type": "ping_latency", "op": ">=", "value": 200}]},
    # 2
    {"id": 2, "name": "Slow Network — Low Throughput",
     "confidence": 0.7,
     "evidence": "Low measured throughput (Mbps)",
     "remedy": "Run speedtest, close background downloads, contact ISP if persist.",
     "conditions": [{"type": "speed_mbps", "op": "<", "value": 1.0}]},
    # 3
    {"id": 3, "name": "Router/Gateway Failure",
     "confidence": 0.95,
     "evidence": "Cannot ping gateway while connected to network",
     "remedy": "Power-cycle router, check modem-to-router link and cables.",
     "conditions": [{"type": "gateway_ping", "op": "==", "value": "fail"},
                    {"type": "wifi_connected", "op": "==", "value": True}]},
    # 4
    {"id": 4, "name": "DNS Resolution Failure",
     "confidence": 0.95,
     "evidence": "IP pings succeed but domain names fail",
     "remedy": "Change DNS to public DNS (8.8.8.8), flush DNS cache.",
     "conditions": [{"type": "ping_ip", "op": "==", "value": "success"},
                    {"type": "ping_domain", "op": "==", "value": "fail"}]},
    # 5
    {"id": 5, "name": "IP Address Conflict",
     "confidence": 0.95,
     "evidence": "OS reports IP conflict message",
     "remedy": "Enable DHCP or assign unique static IP addresses.",
     "conditions": [{"type": "ip_conflict_msg", "op": "==", "value": True}]},
    # 6
    {"id": 6, "name": "Wi-Fi Authentication Failure",
     "confidence": 0.9,
     "evidence": "User can't authenticate to SSID",
     "remedy": "Verify SSID/password, check RADIUS server if used.",
     "conditions": [{"type": "wifi_auth_fail", "op": "==", "value": True}]},
    # 7
    {"id": 7, "name": "DHCP Server Issue",
     "confidence": 0.9,
     "evidence": "Devices receive no IP or 169.254.x.x address",
     "remedy": "Restart DHCP server or router; check DHCP scope settings.",
     "conditions": [{"type": "ip_address", "op": "contains", "value": "169.254"}]},
    # 8
    {"id": 8, "name": "Cable/Link Fault",
     "confidence": 0.9,
     "evidence": "Ethernet link down or flapping",
     "remedy": "Replace cable; test port; check switch port LED.",
     "conditions": [{"type": "eth_link", "op": "==", "value": "down"}]},
    # 9
    {"id": 9, "name": "High Packet Loss",
     "confidence": 0.85,
     "evidence": "Packet loss above acceptable threshold",
     "remedy": "Check Wi-Fi interference, change channel, test wired path.",
     "conditions": [{"type": "packet_loss", "op": ">", "value": 5}]},
    # 10
    {"id": 10, "name": "ISP Outage",
     "confidence": 0.9,
     "evidence": "Multiple users report no internet; external checks fail",
     "remedy": "Contact ISP; check outage map/status.",
     "conditions": [{"type": "multiple_users_down", "op": "==", "value": True},
                    {"type": "internet_status_external", "op": "==", "value": "down"}]},
    # 11
    {"id": 11, "name": "Wi-Fi Interference (Low RSSI)",
     "confidence": 0.8,
     "evidence": "Low RSSI/signal strength",
     "remedy": "Move closer to AP; reduce interference; change channel.",
     "conditions": [{"type": "rssi", "op": "<", "value": -75}]},
    # 12
    {"id": 12, "name": "Too Many Connected Clients",
     "confidence": 0.7,
     "evidence": "AP reports high client count",
     "remedy": "Balance load; add another AP; use wired connections.",
     "conditions": [{"type": "ap_client_count", "op": ">", "value": 50}]},
    # 13
    {"id": 13, "name": "NAT or Port Forwarding Problem",
     "confidence": 0.75,
     "evidence": "Inbound services unreachable",
     "remedy": "Check NAT/port mappings and firewall rules.",
     "conditions": [{"type": "inbound_unreachable", "op": "==", "value": True}]},
    # 14
    {"id": 14, "name": "Proxy Misconfiguration",
     "confidence": 0.7,
     "evidence": "Browser cannot access web but ping works",
     "remedy": "Disable proxy or correct settings.",
      "conditions": [{"type": "browser_err", "op": "==", "value": "proxy_required"},
                     {"type": "ping_domain", "op": "==", "value": "success"}]},
    # 15
    {"id": 15, "name": "Switch Port Disabled",
     "confidence": 0.9,
     "evidence": "Device connected but no carrier; switch port shows disabled",
     "remedy": "Enable port; check VLAN membership.",
     "conditions": [{"type": "switch_port_status", "op": "==", "value": "disabled"}]},
    # 16
    {"id": 16, "name": "Misconfigured VLAN",
     "confidence": 0.85,
     "evidence": "Device in wrong VLAN; cannot reach internal resources",
     "remedy": "Check VLAN tagging and switch config.",
     "conditions": [{"type": "vlan_mismatch", "op": "==", "value": True}]},
    # 17
    {"id": 17, "name": "DNS Cache Poisoning Suspected",
     "confidence": 0.65,
     "evidence": "Unexpected domain resolution to incorrect IP",
     "remedy": "Flush caches, check DNS servers, run diagnostics.",
     "conditions": [{"type": "unexpected_dns_ip", "op": "==", "value": True}]},
    # 18
    {"id": 18, "name": "MTU Mismatch",
     "confidence": 0.6,
     "evidence": "Large packets fail or fragment",
     "remedy": "Adjust MTU, test Path MTU discovery.",
     "conditions": [{"type": "mtu_fail", "op": "==", "value": True}]},
    # 19
    {"id": 19, "name": "VPN Tunnel Down",
     "confidence": 0.9,
     "evidence": "VPN client cannot establish tunnel",
     "remedy": "Check credentials, check VPN server and logs.",
     "conditions": [{"type": "vpn_status", "op": "==", "value": "down"}]},
    # 20
    {"id": 20, "name": "Slow DNS Response (High Latency)",
     "confidence": 0.7,
     "evidence": "DNS queries take long to resolve",
     "remedy": "Use alternative DNS or check DNS server load.",
     "conditions": [{"type": "dns_latency_ms", "op": ">", "value": 200}]},
    # 21
    {"id": 21, "name": "Router CPU High Load",
     "confidence": 0.7,
     "evidence": "Router CPU near 100%",
     "remedy": "Reboot device; check for attack or misconfiguration.",
     "conditions": [{"type": "router_cpu", "op": ">", "value": 90}]},
    # 22
    {"id": 22, "name": "ISP Throttling Detected",
     "confidence": 0.6,
     "evidence": "Speed varies with service type/time",
     "remedy": "Contact ISP, test at different times/services.",
     "conditions": [{"type": "speed_variance", "op": "==", "value": True},
                    {"type": "speed_mbps", "op": "<", "value": 5}]},
    # 23
    {"id": 23, "name": "IPv6 Misconfiguration",
     "confidence": 0.6,
     "evidence": "IPv6 DNS or routing errors",
     "remedy": "Check IPv6 addressing and prefix settings.",
     "conditions": [{"type": "ipv6_error", "op": "==", "value": True}]},
    # 24
    {"id": 24, "name": "Broken ARP Cache",
     "confidence": 0.6,
     "evidence": "ARP entries wrong or stale",
     "remedy": "Clear ARP cache, check duplicates.",
     "conditions": [{"type": "arp_conflict", "op": "==", "value": True}]},
    # 25
    {"id": 25, "name": "Captive Portal Blocking",
     "confidence": 0.85,
     "evidence": "User must sign into captive portal",
     "remedy": "Open browser to sign in to captive portal.",
     "conditions": [{"type": "captive_portal", "op": "==", "value": True}]},
    # 26
    {"id": 26, "name": "Misconfigured Firewall Blocking",
     "confidence": 0.9,
     "evidence": "Firewall denies required traffic",
     "remedy": "Adjust rules to allow required ports/services.",
     "conditions": [{"type": "firewall_block", "op": "==", "value": True}]},
    # 27
    {"id": 27, "name": "Proxy Authentication Required",
     "confidence": 0.8,
     "evidence": "Browser error requiring proxy authentication",
     "remedy": "Provide credentials, configure browser or disable proxy.",
     "conditions": [{"type": "browser_err", "op": "==", "value": "proxy_auth"}]},
    # 28
    {"id": 28, "name": "Slow Wireless Roaming",
     "confidence": 0.6,
     "evidence": "Clients roam between APs causing brief disconnects",
     "remedy": "Tune roaming aggressiveness or AP placement.",
      "conditions": [{"type": "roam_count", "op": ">", "value": 10}]},
    # 29
    {"id": 29, "name": "Switch Overloaded (High Errors)",
     "confidence": 0.7,
     "evidence": "High interface error counters",
     "remedy": "Check cabling, replace faulty NIC/switch module.",
     "conditions": [{"type": "switch_errors", "op": ">", "value": 1000}]},
    # 30
    {"id": 30, "name": "Mis-set Default Gateway",
     "confidence": 0.8,
     "evidence": "Default gateway incorrect",
     "remedy": "Set correct gateway in network config.",
     "conditions": [{"type": "gateway_correct", "op": "==", "value": False}]},
    # 31
    {"id": 31, "name": "External Backhaul Congestion",
     "confidence": 0.6,
     "evidence": "High latency to internet but low to intranet",
     "remedy": "Contact ISP; measure peering issues.",
     "conditions": [{"type": "latency_internet", "op": ">", "value": 200},
                    {"type": "latency_intranet", "op": "<", "value": 50}]},
    # 32
    {"id": 32, "name": "DNS TTL Too Low/High",
     "confidence": 0.5,
     "evidence": "Frequent DNS changes or stale results",
     "remedy": "Tune TTL values appropriately.",
     "conditions": [{"type": "dns_ttl", "op": ">", "value": 86400}]},
    # 33
    {"id": 33, "name": "Routing Loop Detected",
     "confidence": 0.9,
     "evidence": "Traceroute shows loop",
     "remedy": "Fix routing configuration to remove loop.",
     "conditions": [{"type": "traceroute_loop", "op": "==", "value": True}]},
    # 34
    {"id": 34, "name": "ARP Flood / DDoS Suspected",
     "confidence": 0.8,
     "evidence": "Excessive ARP traffic or broadcast storms",
     "remedy": "Isolate offending host; inspect traffic with switch mirroring.",
     "conditions": [{"type": "arp_flood", "op": "==", "value": True}]},
    # 35
    {"id": 35, "name": "Poor Wi-Fi Security (Open SSID)",
     "confidence": 0.5,
     "evidence": "Open Wi-Fi allowing unauthorized access",
     "remedy": "Enable WPA2/WPA3 security.",
     "conditions": [{"type": "ssid_secure", "op": "==", "value": False}]},
    # 36
    {"id": 36, "name": "Corrupted Network Adapter Driver",
     "confidence": 0.8,
     "evidence": "Driver errors in event logs",
     "remedy": "Reinstall/update NIC drivers.",
     "conditions": [{"type": "driver_error_count", "op": ">", "value": 3}]},
    # 37
    {"id": 37, "name": "IPv4 Routing Missing",
     "confidence": 0.8,
     "evidence": "Cannot reach networks beyond local segment",
     "remedy": "Add static routes or fix OSPF/BGP config.",
     "conditions": [{"type": "route_missing", "op": "==", "value": True}]},
    # 38
    {"id": 38, "name": "AP Power Issue",
     "confidence": 0.85,
     "evidence": "AP shows no power or frequent reboots",
     "remedy": "Check PoE injector/switch and power supply.",
     "conditions": [{"type": "ap_reboot", "op": "==", "value": True}]},
    # 39
    {"id": 39, "name": "Misconfigured NAT Translation",
     "confidence": 0.7,
     "evidence": "Internal host cannot reach external services",
     "remedy": "Review NAT rules and mappings.",
     "conditions": [{"type": "nat_mismatch", "op": "==", "value": True}]},
    # 40
    {"id": 40, "name": "Windows Network Profile Blocked",
     "confidence": 0.6,
     "evidence": "Windows network set to Public blocking sharing",
     "remedy": "Set to Private or adjust firewall rules.",
     "conditions": [{"type": "windows_profile", "op": "==", "value": "Public"}]},
    # 41
    {"id": 41, "name": "SSL Interception/Proxy Issue",
     "confidence": 0.7,
     "evidence": "HTTPS pages show certificate errors",
     "remedy": "Install trusted CA or disable SSL interception for that site.",
     "conditions": [{"type": "https_cert_err", "op": "==", "value": True}]},
    # 42
    {"id": 42, "name": "ISP DNS Hijack",
     "confidence": 0.6,
     "evidence": "Known-good domain resolves to ISP ad server",
     "remedy": "Use trusted DNS or VPN.",
     "conditions": [{"type": "dns_hijack", "op": "==", "value": True}]},
    # 43
    {"id": 43, "name": "QoS Misconfiguration",
     "confidence": 0.6,
     "evidence": "Critical traffic deprioritized",
     "remedy": "Adjust QoS policies to prioritize important flows.",
     "conditions": [{"type": "qos_issues", "op": "==", "value": True}]},
    # 44
    {"id": 44, "name": "Cable Duplex Mismatch",
     "confidence": 0.7,
     "evidence": "Errors and collisions on interface",
     "remedy": "Set matching duplex settings or use auto-negotiation.",
     "conditions": [{"type": "duplex_mismatch", "op": "==", "value": True}]},
    # 45
    {"id": 45, "name": "Network MTU Black Hole",
     "confidence": 0.7,
     "evidence": "Certain protocols fail with large packets",
     "remedy": "Lower MTU or enable PMTUD.",
     "conditions": [{"type": "mtu_blackhole", "op": "==", "value": True}]},
    # 46
    {"id": 46, "name": "ARP Spoofing Attempt",
     "confidence": 0.8,
     "evidence": "Conflicting ARP entries",
     "remedy": "Isolate attacker, enable port security.",
     "conditions": [{"type": "arp_spoof_detected", "op": "==", "value": True}]},
    # 47
    {"id": 47, "name": "Time Synchronization Error",
     "confidence": 0.5,
     "evidence": "NTP out of sync causing auth issues",
     "remedy": "Sync time via NTP.",
     "conditions": [{"type": "ntp_ok", "op": "==", "value": False}]},
    # 48
    {"id": 48, "name": "SSDP/UPnP Flood",
     "confidence": 0.55,
     "evidence": "Excessive SSDP traffic",
     "remedy": "Disable UPnP where unnecessary.",
     "conditions": [{"type": "ssdp_flood", "op": "==", "value": True}]},
    # 49
    {"id": 49, "name": "Port Scan Detected",
     "confidence": 0.85,
     "evidence": "Multiple ports probed from same IP",
     "remedy": "Block scanner and investigate source.",
     "conditions": [{"type": "port_scan", "op": "==", "value": True}]},
    # 50
    {"id": 50, "name": "Router Configuration Corruption",
     "confidence": 0.9,
     "evidence": "Config fails to load correctly",
     "remedy": "Restore from backup; reconfigure router.",
      "conditions": [{"type": "router_config_good", "op": "==", "value": False}]},
    # 51
    {"id": 51, "name": "Slow Wireless Encryption Overhead",
     "confidence": 0.5,
     "evidence": "Weak hardware struggling with encryption",
     "remedy": "Upgrade AP hardware; use faster encryption modes.",
     "conditions": [{"type": "old_ap_hw", "op": "==", "value": True}]},
    # 52
    {"id": 52, "name": "Mobile Carrier Data Fallback",
     "confidence": 0.6,
     "evidence": "Client using mobile data instead of Wi-Fi",
     "remedy": "Disable mobile data or connect to Wi-Fi correctly.",
     "conditions": [{"type": "client_online_via", "op": "==", "value": "mobile"}]},
    # 53
    {"id": 53, "name": "Blocked by Content Filter",
     "confidence": 0.7,
     "evidence": "Access blocked by content filter or web filter",
     "remedy": "Request unblock or adjust filter policy.",
     "conditions": [{"type": "content_filter_block", "op": "==", "value": True}]},
    # 54
    {"id": 54, "name": "ISP Peering Problem",
     "confidence": 0.6,
     "evidence": "High latency to specific AS paths",
     "remedy": "Contact ISP to report peering issues.",
     "conditions": [{"type": "as_path_latency", "op": ">", "value": 200}]},
    # 55
    {"id": 55, "name": "Low Wi-Fi Channel Width / Legacy Rates",
     "confidence": 0.6,
     "evidence": "AP using legacy rates reducing throughput",
     "remedy": "Change channel width and disable legacy rates.",
     "conditions": [{"type": "legacy_rate_enabled", "op": "==", "value": True}]},
])

# COMPUTER (hardware + software): rules 56-100
RULES.extend([
    # 56
    {"id": 56, "name": "No Power — PSU Fault",
     "confidence": 0.98,
     "evidence": "PC shows no signs of power",
     "remedy": "Check mains, PSU connectors, test/replace PSU.",
     "conditions": [{"type": "pc_power", "op": "==", "value": False}]},
    # 57
    {"id": 57, "name": "No Display — GPU/Monitor Issue",
     "confidence": 0.9,
     "evidence": "Power on but no display, external monitor fails",
     "remedy": "Check monitor, cables, reseat GPU.",
     "conditions": [{"type": "pc_power", "op": "==", "value": True},
                    {"type": "display", "op": "==", "value": "no"}]},
    # 58
    {"id": 58, "name": "BIOS Beep Memory Error",
     "confidence": 0.95,
     "evidence": "Beep codes consistent with RAM error",
     "remedy": "Reseat RAM, run memtest, replace defective stick.",
     "conditions": [{"type": "beep_codes", "op": "contains", "value": "mem"}]},
    # 59
    {"id": 59, "name": "BIOS Beep GPU Error",
     "confidence": 0.95,
     "evidence": "Beep codes indicate GPU/graphics failure",
     "remedy": "Reseat GPU, test with known-good card.",
     "conditions": [{"type": "beep_codes", "op": "contains", "value": "gpu"}]},
    # 60
    {"id": 60, "name": "Overheating — Fan/Heatsink Fault",
     "confidence": 0.92,
     "evidence": "CPU temp dangerously high",
     "remedy": "Clean dust, reapply thermal paste, replace fan.",
     "conditions": [{"type": "cpu_temp", "op": ">", "value": 80}]},
    # 61
    {"id": 61, "name": "Thermal Throttling",
     "confidence": 0.85,
     "evidence": "High temps causing low performance",
     "remedy": "Improve cooling, check background processes.",
     "conditions": [{"type": "cpu_temp", "op": ">", "value": 70},
                    {"type": "slow_performance", "op": "==", "value": True}]},
    # 62
    {"id": 62, "name": "Failing HDD/SSD",
     "confidence": 0.95,
     "evidence": "SMART disk health low or many bad sectors",
     "remedy": "Backup immediately and replace drive.",
     "conditions": [{"type": "disk_health", "op": "<", "value": 50}]},
    # 63
    {"id": 63, "name": "Corrupted OS Bootloader",
     "confidence": 0.9,
     "evidence": "No OS boot, bootloader errors",
     "remedy": "Repair bootloader or restore OS from backup.",
     "conditions": [{"type": "boot_error", "op": "contains", "value": "NTLDR"},
                    {"type": "os_present", "op": "==", "value": True}]},
    # 64
    {"id": 64, "name": "Slow Boot — Disk or Startup Bloat",
     "confidence": 0.8,
     "evidence": "Slow boot with high disk usage",
     "remedy": "Disable startup apps, check disk health.",
     "conditions": [{"type": "slow_boot", "op": "==", "value": True},
                    {"type": "disk_usage_startup", "op": ">", "value": 90}]},
    # 65
    {"id": 65, "name": "Application Crash — Memory Leak",
     "confidence": 0.85,
     "evidence": "App crashes with RAM near 100%",
     "remedy": "Restart app, update/reinstall, increase RAM.",
     "conditions": [{"type": "app_crash", "op": "==", "value": True},
                    {"type": "ram_usage", "op": ">", "value": 90}]},
    # 66
    {"id": 66, "name": "Application Crash — Corrupted Install",
     "confidence": 0.8,
     "evidence": "Crash across runs with different inputs",
     "remedy": "Reinstall application or check logs.",
     "conditions": [{"type": "app_crash", "op": "==", "value": True},
                    {"type": "app_reinstall_attempted", "op": "==", "value": False}]},
    # 67
    {"id": 67, "name": "Possible Malware — Suspicious Popups & Idle CPU",
     "confidence": 0.9,
     "evidence": "Frequent popups with high idle CPU",
     "remedy": "Disconnect network, run offline antivirus, restore from known good backup.",
     "conditions": [{"type": "popups", "op": "==", "value": True},
                    {"type": "idle_cpu", "op": ">", "value": 80}]},
    # 68
    {"id": 68, "name": "Ransomware Suspected",
     "confidence": 0.95,
     "evidence": "Files encrypted or ransom note detected",
     "remedy": "Isolate host, preserve logs, restore from backups; do not pay ransom.",
     "conditions": [{"type": "files_encrypted", "op": "==", "value": True}]},
    # 69
    {"id": 69, "name": "Driver Conflict",
     "confidence": 0.85,
     "evidence": "Driver crashes or mismatched driver versions",
     "remedy": "Roll back or update driver; use vendor driver.",
     "conditions": [{"type": "driver_conflict", "op": "==", "value": True}]},
    # 70
    {"id": 70, "name": "GPU Driver Crash/Black Screen",
     "confidence": 0.9,
     "evidence": "Display resets when launching GPU-heavy apps",
     "remedy": "Update GPU drivers, check power connectors.",
     "conditions": [{"type": "gpu_reset", "op": "==", "value": True}]},
    # 71
    {"id": 71, "name": "Battery Failure (Laptop)",
     "confidence": 0.9,
     "evidence": "Battery not charging or holds no charge",
     "remedy": "Replace battery or AC adapter.",
     "conditions": [{"type": "battery_health", "op": "<", "value": 20}]},
    # 72
    {"id": 72, "name": "Thermal Paste Degraded",
     "confidence": 0.6,
     "evidence": "High temps despite fan functioning",
     "remedy": "Reapply thermal paste and reseat cooler.",
     "conditions": [{"type": "fan_speed_ok", "op": "==", "value": True},
                    {"type": "cpu_temp", "op": ">", "value": 85}]},
    # 73
    {"id": 73, "name": "Loose Power Connector",
     "confidence": 0.85,
     "evidence": "Intermittent power or sudden shutdowns",
     "remedy": "Check cables and connectors.",
     "conditions": [{"type": "sudden_shutdown", "op": "==", "value": True},
                    {"type": "power_bad_report", "op": "==", "value": True}]},
    # 74
    {"id": 74, "name": "Corrupted System Files",
     "confidence": 0.8,
     "evidence": "SFC or system repair detects corruption",
     "remedy": "Run system file checker and repair tools.",
     "conditions": [{"type": "sfc_errors", "op": ">", "value": 0}]},
    # 75
    {"id": 75, "name": "Windows Update Caused Regression",
     "confidence": 0.6,
     "evidence": "Issue started after recent Windows update",
     "remedy": "Uninstall problematic update or use restore point.",
     "conditions": [{"type": "recent_update", "op": "==", "value": True},
                    {"type": "issue_started_after_update", "op": "==", "value": True}]},
    # 76
    {"id": 76, "name": "File System Corruption",
     "confidence": 0.9,
     "evidence": "CHKDSK finds errors",
     "remedy": "Repair filesystem and restore backups.",
     "conditions": [{"type": "chkdsk_errors", "op": ">", "value": 0}]},
    # 77
    {"id": 77, "name": "Malfunctioning Peripheral (USB)",
     "confidence": 0.8,
     "evidence": "USB device disconnects or errors",
     "remedy": "Try different port, check power, update drivers.",
     "conditions": [{"type": "usb_error", "op": "==", "value": True}]},
    # 78
    {"id": 78, "name": "BIOS Settings Corrupt",
     "confidence": 0.85,
     "evidence": "Wrong boot order or system settings reset",
     "remedy": "Reset BIOS/UEFI to defaults and reconfigure.",
     "conditions": [{"type": "bios_reset_detected", "op": "==", "value": True}]},
    # 79
    {"id": 79, "name": "Windows Activation/License Problem",
     "confidence": 0.6,
     "evidence": "Activation errors",
     "remedy": "Reactivate Windows or check license keys.",
     "conditions": [{"type": "win_activate_err", "op": "==", "value": True}]},
    # 80
    {"id": 80, "name": "Insufficient RAM for Workload",
     "confidence": 0.85,
     "evidence": "High memory usage under expected workload",
     "remedy": "Add RAM or optimize apps.",
     "conditions": [{"type": "ram_usage", "op": ">", "value": 85},
                    {"type": "expected_workload", "op": "==", "value": "normal"}]},
    # 81
    {"id": 81, "name": "Corrupted Browser Profile",
     "confidence": 0.7,
     "evidence": "Browser crashes or misbehaves across sites",
     "remedy": "Reset profile or reinstall browser.",
     "conditions": [{"type": "browser_crash", "op": "==", "value": True},
                    {"type": "browser_profile_old", "op": "==", "value": True}]},
    # 82
    {"id": 82, "name": "System Overloaded by Background Tasks",
     "confidence": 0.75,
     "evidence": "High CPU/disk caused by background process",
     "remedy": "Identify and stop background tasks; schedule jobs off-hours.",
     "conditions": [{"type": "background_cpu", "op": ">", "value": 60}]},
    # 83
    {"id": 83, "name": "Heat Sink Not Properly Mounted",
     "confidence": 0.9,
     "evidence": "High temps + uneven core temps",
     "remedy": "Reseat heatsink and reapply thermal paste.",
     "conditions": [{"type": "core_temp_delta", "op": ">", "value": 20}]},
    # 84
    {"id": 84, "name": "SSD TRIM Disabled",
     "confidence": 0.6,
     "evidence": "SSD performance degradation",
     "remedy": "Enable TRIM and optimize filesystem.",
     "conditions": [{"type": "ssd_trim_enabled", "op": "==", "value": False}]},
    # 85
    {"id": 85, "name": "Corrupted User Profile",
     "confidence": 0.7,
     "evidence": "User-specific settings missing or corrupted",
     "remedy": "Create new profile and migrate data.",
     "conditions": [{"type": "profile_corrupt", "op": "==", "value": True}]},
    # 86
    {"id": 86, "name": "Power Management Bug",
     "confidence": 0.6,
     "evidence": "Sleep/wake issues",
     "remedy": "Update power drivers and BIOS.",
     "conditions": [{"type": "sleep_wake_fail", "op": "==", "value": True}]},
    # 87
    {"id": 87, "name": "Thermal Sensor Fault",
     "confidence": 0.5,
     "evidence": "Temperature readings inconsistent",
     "remedy": "Validate with external sensor or BIOS reading.",
     "conditions": [{"type": "temp_sensor_err", "op": "==", "value": True}]},
    # 88
    {"id": 88, "name": "Firmware Bug (Device)",
     "confidence": 0.7,
     "evidence": "Device malfunction solved by firmware update",
     "remedy": "Update firmware to latest stable release.",
     "conditions": [{"type": "firmware_old", "op": "==", "value": True}]},
    # 89
    {"id": 89, "name": "Corrupted Application Cache",
     "confidence": 0.6,
     "evidence": "App misbehavior resolved by clearing cache",
     "remedy": "Clear application cache and restart.",
     "conditions": [{"type": "app_cache_corrupt", "op": "==", "value": True}]},
    # 90
    {"id": 90, "name": "Incompatible Peripheral Driver",
     "confidence": 0.85,
     "evidence": "Peripheral causes kernel errors",
     "remedy": "Install vendor-supplied driver or remove device.",
     "conditions": [{"type": "kernel_panic_device", "op": "==", "value": True}]},
    # 91
    {"id": 91, "name": "Slow System Due to Fragmented Disk",
     "confidence": 0.55,
     "evidence": "HDD fragmented and slow I/O",
     "remedy": "Defragment HDD (not SSD).",
     "conditions": [{"type": "hdd_fragmentation", "op": ">", "value": 30}]},
    # 92
    {"id": 92, "name": "Corrupted Boot Sector",
     "confidence": 0.9,
     "evidence": "Bootloader missing or sector corrupted",
     "remedy": "Repair boot sector using recovery tools.",
     "conditions": [{"type": "boot_sector_ok", "op": "==", "value": False}]},
    # 93
    {"id": 93, "name": "Security Policy Blocking Action",
     "confidence": 0.7,
     "evidence": "Group policy prevents action",
     "remedy": "Adjust group policy or use admin override.",
     "conditions": [{"type": "gpo_block", "op": "==", "value": True}]},
    # 94
    {"id": 94, "name": "Unpatched Vulnerability Detected",
     "confidence": 0.8,
     "evidence": "Known vulnerable version detected",
     "remedy": "Patch OS/software and mitigate exposure.",
     "conditions": [{"type": "vuln_found", "op": "==", "value": True}]},
    # 95
    {"id": 95, "name": "Corrupted Network Stack (OS)",
     "confidence": 0.8,
     "evidence": "Winsock or equivalent corruption symptoms",
     "remedy": "Reset network stack (e.g., netsh winsock reset).",
     "conditions": [{"type": "network_stack_corrupt", "op": "==", "value": True}]},
    # 96
    {"id": 96, "name": "Background Update Causing Slowdown",
     "confidence": 0.6,
     "evidence": "Auto-updates consuming CPU/disk",
     "remedy": "Schedule updates at off-hours or pause updates.",
     "conditions": [{"type": "auto_update_running", "op": "==", "value": True}]},
    # 97
    {"id": 97, "name": "Insufficient Disk Space",
     "confidence": 0.9,
     "evidence": "Very low free disk space",
     "remedy": "Clean up disk, remove temp files, extend partition.",
     "conditions": [{"type": "disk_free_percent", "op": "<", "value": 5}]},
    # 98
    {"id": 98, "name": "Corrupted Registry (Windows)",
     "confidence": 0.75,
     "evidence": "Registry errors reported in logs",
     "remedy": "Repair registry from backup or reinstall OS.",
     "conditions": [{"type": "registry_errors", "op": ">", "value": 0}]},
    # 99
    {"id": 99, "name": "Unresponsive System — Kernel Hang",
     "confidence": 0.9,
     "evidence": "System becomes unresponsive and requires hard reset",
     "remedy": "Collect memory dump and analyze; update kernel/drivers.",
     "conditions": [{"type": "kernel_hang", "op": "==", "value": True}]},
    # 100
    {"id": 100, "name": "Insufficient Data to Diagnose",
     "confidence": 0.2,
     "evidence": "Not enough facts supplied to identify root cause",
     "remedy": "Collect more diagnostics (ping, speedtest, temps, logs).",
     "conditions": []}
])

# ---------------------------
# Engine runner
# ---------------------------

def run_diagnosis(facts: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Evaluate all rules against the given facts and return sorted diagnoses.
    facts: e.g. {'ping_latency': 250, 'speed_mbps': 0.3, 'wifi_connected': True}
    Returns list of dicts with keys: id,name,confidence,evidence,remedy,matched_conditions
    """
    matches = []
    # scoring threshold: return fallback only if no rule meets this score
    SCORE_THRESHOLD = 0.25

    for r in RULES:
        if r.get('id') == 100:
            continue
        try:
            eval_res = evaluate_rule(r, facts)
            # include rule if it has any positive score
            if eval_res['score'] > 0:
                matches.append({
                    'id': r['id'],
                    'name': r['name'],
                    'confidence': eval_res['confidence'],
                    'evidence': r.get('evidence', ''),
                    'remedy': r.get('remedy', ''),
                    'match_ratio': eval_res['match_ratio'],
                    'score': eval_res['score'],
                    'matched_conditions': eval_res['matched_conditions'],
                    'unmatched_conditions': eval_res['unmatched_conditions'],
                })
        except Exception:
            continue

    # Filter matches above threshold and sort by score desc
    matches_above = [m for m in matches if m.get('score', 0) >= SCORE_THRESHOLD]
    if matches_above:
        sorted_matches = sorted(matches_above, key=lambda x: x['score'], reverse=True)
        return sorted_matches

    # no rule met threshold: if there are lower-scoring matches, return top 3
    if matches:
        sorted_low = sorted(matches, key=lambda x: x['score'], reverse=True)[:3]
        return sorted_low

    # If truly no matches, return fallback rule 100
    fallback = next((x for x in RULES if x['id'] == 100), None)
    if fallback:
        return [{
            'id': fallback['id'],
            'name': fallback['name'],
            'confidence': _normalize_confidence(fallback.get('confidence', 0.2)),
            'evidence': fallback.get('evidence', ''),
            'remedy': fallback.get('remedy', ''),
            'match_ratio': 0.0,
            'score': 0.0,
            'matched_conditions': [],
            'unmatched_conditions': [],
        }]
    return []
