import psutil
import time


def get_bandwidth_usage(interval=1):
    before = psutil.net_io_counters()
    time.sleep(interval)
    after = psutil.net_io_counters()
    sent = (after.bytes_sent - before.bytes_sent) / 1024
    recv = (after.bytes_recv - before.bytes_recv) / 1024
    return sent, recv
