import logging

import ray
from ray.util.queue import Empty, Queue

queue = Queue(maxsize=100)


@ray.remote
def producer(queue, item):
    queue.put(item)


@ray.remote
class Broker:
    def __init__(self):
        self.refs = {}

    def get_event(self, queue, event):
        self.refs[event] = [] if event not in locals() else self.refs[event]
        if len(self.refs[event]) > 0:
            item = self.refs[event].pop(0)
            return item

        try:
            item = queue.get(block=True, timeout=1)
        except Empty:
            return False

        if item is None:
            return False
        elif event == item["event"]:
            return item
        else:
            self.set_event(event, item)

    def set_event(self, event, item):
        self.refs[event] = item


broker = Broker.remote()


@ray.remote
def consumer(queue, event):
    ref = broker.get_event.remote(queue, event)
    item = ray.get(ref)
    if item:
        return item
