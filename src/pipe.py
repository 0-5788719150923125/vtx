import logging

import ray
from ray.util.queue import Empty, Queue

queue = Queue(maxsize=100)


@ray.remote
class Broker:
    def __init__(self):
        self.refs = {}

    def get_event(self, queue, event):
        self.refs[event] = [] if event not in self.refs else self.refs[event]
        if len(self.refs[event]) > 0:
            item = self.refs[event].pop(0)
            return item

        try:
            item = queue.get(block=True, timeout=1)
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

    def queue_event(self, queue, item):
        queue.put(item)


broker = Broker.remote()


def producer(queue, item):
    broker.queue_event.remote(queue, item)


def consumer(queue, event):
    ref = broker.get_event.remote(queue, event)
    item = ray.get(ref)
    if item:
        return item
