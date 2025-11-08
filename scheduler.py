import heapq


class PriorityScheduler:
    def __init__(self):
        self.queue = []

    def add_device(self, device_ip, priority):
        heapq.heappush(self.queue, (-priority, device_ip))

    def get_next_device(self):
        if self.queue:
            return heapq.heappop(self.queue)[1]
        return None


if __name__ == "__main__":
    s = PriorityScheduler()
    s.add_device("192.168.1.5", 3)
    s.add_device("192.168.1.8", 1)

    print("Next to allocate:", s.get_next_device())
