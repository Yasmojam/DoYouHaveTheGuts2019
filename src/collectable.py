from server import ObjectUpdate
from time import time
from typing import Tuple

Vector = Tuple[float, float]
COLLECTABLE_TYPES = set(["AmmoPickup", "HealthPickup", "Snitch"])


class Collectable:
    def __init__(self, payload: ObjectUpdate) -> None:
        self.name = payload.name
        self.id = payload.id
        self.type = payload.type
        self.last_seen = time()
        self.position = (payload.x, payload.y)
        self.positions = [(payload.x, payload.y)]
        self.payload_times = [time()]

    def update(self, payload: ObjectUpdate) -> None:
        self.last_seen = time()
        self.position = (payload.x, payload.y)
        self.positions = self.positions[-4:] + [(payload.x, payload.y)]

    def current_pos(self) -> Tuple[float, float]:
        return self.positions[-1]

    def previous_pos(self) -> Tuple[float, float]:
        return self.positions[-2] if len(self.positions) > 1 else None
    
    def current_pos_time(self) -> float:
        return self.payload_times[-1]
    
    def previous_pos_time(self) -> float:
        return self.payload_times[-2] if len(self.payload_times) > 1 else None

    def time_since_last(self):
        timesincelastseen = time() - self.last_seen
        return timesincelastseen
