"""事件总线：记录 code/log/metric/status 事件，供回放与后续 WebSocket 推送。"""
from __future__ import annotations


class EventBus:
    """简单的事件总线，记录事件并广播给订阅者。"""

    def __init__(self):
        self.events: list[dict] = []
        self.subscribers: list = []

    def publish(self, event_type: str, execution_id: str, payload: dict) -> None:
        """发布一个事件。"""
        event = {"type": event_type, "execution_id": execution_id, "payload": payload}
        self.events.append(event)
        for sub in self.subscribers:
            sub(event)

    def subscribe(self, callback) -> None:
        """订阅事件，callback(event)。"""
        self.subscribers.append(callback)

    def clear(self) -> None:
        self.events.clear()


bus = EventBus()
