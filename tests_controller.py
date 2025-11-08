import unittest
from controller_service import compute_allocations


class TestAllocations(unittest.TestCase):
    def test_equal_share(self):
        clients = [
            {"ip": "192.168.1.2"},
            {"ip": "192.168.1.3"},
            {"ip": "192.168.1.4"},
        ]
        alloc = compute_allocations(clients, total_mbit=60)
        self.assertEqual(alloc["192.168.1.2"], 20)
        self.assertEqual(sum(alloc.values()), 60)

    def test_priority_share(self):
        clients = [{"ip": "192.168.1.2"}, {"ip": "192.168.1.3"}]
        pr = {"192.168.1.2": 1, "192.168.1.3": 2}
        alloc = compute_allocations(clients, total_mbit=30, priorities=pr)
        self.assertEqual(alloc["192.168.1.2"], 10)
        self.assertEqual(alloc["192.168.1.3"], 20)
        self.assertEqual(sum(alloc.values()), 30)


if __name__ == "__main__":
    unittest.main()
