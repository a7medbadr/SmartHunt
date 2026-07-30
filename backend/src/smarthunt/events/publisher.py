from typing import Callable, Awaitable

from smarthunt.events.base import BaseEvent


Subscriber = Callable[[BaseEvent], Awaitable[None]]


class EventPublisher:
    def __init__(self):
        self.subscribers: list[Subscriber] = []

    def subscribe(self, subscriber: Subscriber):
        self.subscribers.append(subscriber)

    async def publish(self, event: BaseEvent):
        for subscriber in self.subscribers:
            await subscriber(event)


event_publisher = EventPublisher()
