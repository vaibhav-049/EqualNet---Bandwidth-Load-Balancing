import random


class LoadBalancer:
    def __init__(self, total_bandwidth, max_priority=5, min_bandwidth_percent=10):
        self.total_bandwidth = total_bandwidth
        self.max_priority = max_priority
        self.min_bandwidth_percent = min_bandwidth_percent
        self.allocations = {}
        self.priorities = {}
        self.usage = {}

    def _validate_priority(self, priority):
        """Validate and clamp priority to allowed range (1 to max_priority)"""
        if priority < 1:
            return 1
        if priority > self.max_priority:
            return self.max_priority
        return priority

    def register_clients(self, clients, priorities):
        self.priorities = {
            ip: self._validate_priority(pr) 
            for ip, pr in priorities.items()
        }
        for ip in clients:
            self.allocations[ip] = 0
            self.usage[ip] = random.uniform(0.1, 1.0)

    def distribute_bandwidth(self):
        """Distribute bandwidth based on priority with minimum guarantees"""
        if not self.priorities:
            return self.allocations
        
        total_priority = sum(self.priorities.values())
        min_bandwidth = (self.min_bandwidth_percent / 100) * self.total_bandwidth
        num_clients = len(self.priorities)
        
        reserved_bandwidth = min_bandwidth * num_clients
        available_bandwidth = self.total_bandwidth - reserved_bandwidth
        
        if available_bandwidth < 0:
            available_bandwidth = self.total_bandwidth
            min_bandwidth = 0
        
        # Distribute bandwidth with minimum guarantees
        for ip, pr in self.priorities.items():
            weight = pr / total_priority
            priority_allocation = weight * available_bandwidth
            self.allocations[ip] = round(min_bandwidth + priority_allocation, 2)
        
        return self.allocations

    def update_usage(self, ip, usage):
        self.usage[ip] = usage

    def rebalance_load(self):
        """Rebalance with priority enforcement and limits"""
        total_usage = sum(self.usage.values())
        if total_usage == 0:
            return self.allocations

        if not self.priorities:
            return self.allocations

        temp_allocations = {}
        for ip in self.allocations:
            if ip not in self.priorities:
                temp_allocations[ip] = self.allocations[ip]
                continue
                
            usage_ratio = self.usage[ip] / total_usage
            total_prio = sum(self.priorities.values())
            priority_boost = self.priorities[ip] / total_prio
            new_alloc = (
                (0.6 * usage_ratio + 0.4 * priority_boost) * 
                self.total_bandwidth
            )
            temp_allocations[ip] = new_alloc

        # Enforce priority constraints: higher priority must get >= bandwidth
        sorted_clients = sorted(
            self.priorities.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        for i in range(len(sorted_clients)):
            current_ip, current_priority = sorted_clients[i]
            
            if current_ip not in temp_allocations:
                continue
            
            for j in range(i + 1, len(sorted_clients)):
                lower_ip, lower_priority = sorted_clients[j]
                
                if lower_ip not in temp_allocations:
                    continue
                
                # If lower priority has more bandwidth, redistribute
                if temp_allocations[lower_ip] > temp_allocations[current_ip]:
                    excess = temp_allocations[lower_ip] - temp_allocations[current_ip]
                    redistribute = excess * 0.5
                    temp_allocations[current_ip] += redistribute
                    temp_allocations[lower_ip] -= redistribute

        # Apply minimum bandwidth guarantee
        min_bandwidth = (self.min_bandwidth_percent / 100) * self.total_bandwidth
        for ip in temp_allocations:
            if temp_allocations[ip] < min_bandwidth:
                temp_allocations[ip] = min_bandwidth

        # Normalize to total bandwidth
        total_allocated = sum(temp_allocations.values())
        if total_allocated > 0:
            scale_factor = self.total_bandwidth / total_allocated
            for ip in temp_allocations:
                self.allocations[ip] = round(temp_allocations[ip] * scale_factor, 2)
        
        return self.allocations


if __name__ == "__main__":
    print("=== EqualNet Load Balancer Demo ===\n")
    
    lb = LoadBalancer(total_bandwidth=100)
    
    clients = ["192.168.1.101", "192.168.1.102", "192.168.1.103"]
    priorities = {
        "192.168.1.101": 3,
        "192.168.1.102": 2,
        "192.168.1.103": 1
    }
    
    lb.register_clients(clients, priorities)
    print("Registered Clients:", clients)
    print("Priorities:", priorities)
    print()
    
    print("Initial Bandwidth Distribution (based on priority):")
    allocations = lb.distribute_bandwidth()
    for ip, bw in allocations.items():
        print(f"  {ip}: {bw} Mbps (Priority: {priorities[ip]})")
    print()
    
    print("Current Usage (simulated):")
    for ip, usage in lb.usage.items():
        print(f"  {ip}: {usage:.2f} Mbps")
    print()
    
    print("Rebalanced Bandwidth (60% usage + 40% priority):")
    rebalanced = lb.rebalance_load()
    for ip, bw in rebalanced.items():
        print(f"  {ip}: {bw} Mbps")
    print()
    
    print("--- Updating usage for 192.168.1.103 to 5.0 Mbps ---")
    lb.update_usage("192.168.1.103", 5.0)
    rebalanced = lb.rebalance_load()
    print("\nNew Rebalanced Bandwidth:")
    for ip, bw in rebalanced.items():
        print(f"  {ip}: {bw} Mbps")
