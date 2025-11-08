import os
import time
from typing import Dict, List

from client_detector import get_connected_clients
from tc_controller import TcController


def compute_allocations(
    clients: List[dict],
    total_mbit: int,
    priorities: Dict[str, int] | None = None,
) -> Dict[str, int]:
    ips = [c["ip"] for c in clients]
    if not ips:
        return {}
    if not priorities:
        per = max(1, total_mbit // len(ips))
        return {ip: per for ip in ips}
    s = sum(priorities.values()) or len(ips)
    alloc: Dict[str, int] = {}
    for ip in ips:
        pr = priorities.get(ip, 1)
        alloc[ip] = max(1, int(total_mbit * (pr / s)))
    return alloc


def run_controller(
    iface: str = os.environ.get("IFACE", "eth0"),
    total_mbit: int = int(os.environ.get("TOTAL_MBIT", "50")),
    interval_sec: int = int(os.environ.get("INTERVAL", "10")),
):
    print(
        f"Starting controller on iface={iface}, total={total_mbit}Mbit, "
        f"interval={interval_sec}s"
    )
    tc = TcController(iface=iface, default_rate=f"{total_mbit}mbit")
    tc.ensure_root_qdisc()

    priorities: Dict[str, int] = {}
    while True:
        clients = get_connected_clients()
        print(f"Detected {len(clients)} clients")
        for c in clients:
            print(f" - {c['ip']} {c.get('mac', '')} ({c.get('iface', '')})")

        allocations = compute_allocations(clients, total_mbit, priorities)
        for ip, rate in allocations.items():
            tc.set_limit(ip, rate_mbit=rate, ceil_mbit=rate)
            print(f"Applied limit {rate}mbit to {ip}")

        time.sleep(interval_sec)


if __name__ == "__main__":
    run_controller()
