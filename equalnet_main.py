from monitor import get_connected_devices
from load_balancer import LoadBalancer
from utils import get_bandwidth_usage
import time

print("=== EqualNet - Bandwidth Load Balancing System ===\n")

print("Step 1: Detecting connected clients...")
clients = get_connected_devices()
print(f"Found {len(clients)} clients: {clients}\n")

print("Step 2: Assigning priorities...")
max_priority = 5
priorities = {ip: min(i+1, max_priority) for i, ip in enumerate(clients)}
for ip, priority in priorities.items():
    print(f"  {ip} -> Priority {priority} (1=highest, {max_priority}=lowest)")
print()

total_bandwidth = 100
min_bandwidth_percent = 10
print(f"Step 3: Allocating bandwidth (Total: {total_bandwidth} Mbps)...")
print(f"  Max Priority Level: {max_priority}")
print(f"  Minimum Bandwidth Guarantee: {min_bandwidth_percent}%")
lb = LoadBalancer(total_bandwidth, max_priority, min_bandwidth_percent)
lb.register_clients(clients, priorities)
allocation = lb.distribute_bandwidth()

print("Initial Allocation:")
for ip, bw in allocation.items():
    print(f"  {ip}: {bw} Mbps")
print()

print("Step 4: Starting live monitoring loop (Press Ctrl+C to stop)...\n")
try:
    iteration = 1
    while True:
        print(f"--- Iteration {iteration} ---")
        sent, recv = get_bandwidth_usage()
        print(f"Network Usage - Sent: {sent:.2f} KB/s, Recv: {recv:.2f} KB/s")
        
        rebalanced = lb.rebalance_load()
        print("Current Allocation:")
        for ip, bw in rebalanced.items():
            print(f"  {ip}: {bw} Mbps (Usage: {lb.usage.get(ip, 0):.2f} Mbps)")
        print()
        
        iteration += 1
        time.sleep(3)
except KeyboardInterrupt:
    print("\n\nMonitoring stopped. EqualNet shutting down...")
