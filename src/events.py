import logging

import ray
from ray.util.queue import Empty, Queue


@ray.remote
class Broker:
    def __init__(self):
        self.refs = {}
        self.queue = Queue(maxsize=100)

    def get_event(self, event):
        self.refs[event] = [] if event not in self.refs else self.refs[event]
        if len(self.refs[event]) > 0:
            item = self.refs[event].pop(0)
            return item

        try:
            item = self.queue.get(block=True, timeout=1)
        except Empty:
            return False

        if item is None:
            return False
        if event == item["event"]:
            return item

        self.cache_event(item["event"], item)
        return False

    def cache_event(self, event, item):
        self.refs[event].append(item)

    def queue_event(self, item):
        self.queue.put(item)


broker = Broker.remote()


def producer(item):
    broker.queue_event.remote(item)


def consumer(event):
    ref = broker.get_event.remote(event)
    item = ray.get(ref)
    if item:
        return item
