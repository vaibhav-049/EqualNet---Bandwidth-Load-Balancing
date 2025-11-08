import re
import subprocess
from typing import List, Dict


def _read_proc_arp() -> List[Dict[str, str]]:
    entries: List[Dict[str, str]] = []
    try:
        with open("/proc/net/arp", "r", encoding="utf-8") as f:
            lines = f.read().strip().splitlines()
    except Exception:
        return entries

    for line in lines[1:]:
        parts = re.split(r"\s+", line.strip())
        if len(parts) < 6:
            continue
        ip, hw_type, flags, mac, mask, iface = parts[:6]
        if flags != "0x2":
            continue
        entries.append({"ip": ip, "mac": mac, "iface": iface})
    return entries


def _hostapd_clients() -> List[Dict[str, str]]:
    try:
        proc = subprocess.run(
            ["hostapd_cli", "all_sta"],
            capture_output=True,
            text=True,
            check=False
        )
    except FileNotFoundError:
        return []

    macs = set()
    cur_mac = None
    for line in proc.stdout.splitlines():
        line = line.strip()
        if re.fullmatch(r"[0-9a-f]{2}(:[0-9a-f]{2}){5}", line, re.IGNORECASE):
            cur_mac = line.lower()
            macs.add(cur_mac)
    arp = _read_proc_arp()
    results: List[Dict[str, str]] = []
    for e in arp:
        if e["mac"].lower() in macs:
            results.append(e)
    return results


def get_connected_clients(prefer_hostapd: bool = True) -> List[Dict[str, str]]:
    entries: List[Dict[str, str]] = []
    if prefer_hostapd:
        entries = _hostapd_clients()
    if not entries:
        entries = _read_proc_arp()

    filtered: List[Dict[str, str]] = []
    for e in entries:
        ip = e.get("ip", "")
        if not ip:
            continue
        if (ip.startswith("224.") or
                ip.startswith("239.") or
                ip == "255.255.255.255"):
            continue
        if ip.endswith(".255"):
            continue
        filtered.append(e)
    seen = set()
    unique: List[Dict[str, str]] = []
    for e in filtered:
        if e["ip"] in seen:
            continue
        seen.add(e["ip"])
        unique.append(e)
    return unique


if __name__ == "__main__":
    for c in get_connected_clients():
        print(c)
