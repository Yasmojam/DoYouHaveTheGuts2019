from server import ObjectUpdate
from time import time
from typing import Tuple
from utils import within_degrees, heading_from_to, calculate_distance

Vector = Tuple[float, float]


class Enemy:
    def __init__(self, payload: ObjectUpdate) -> None:
        self.name = payload.name
        self.id = payload.id
        self.type = payload.type
        self.last_seen = time()
        self.position = [(payload.x, payload.y)]
        self.payload_times = [time()]
        self.heading = payload.heading
        self.turret_heading = payload.turret_heading
        self.health = payload.health
        self.ammo = payload.ammo

    def update(self, payload: ObjectUpdate) -> None:
        if payload.id == self.id:
            self.last_seen = time()
            self.position = self.position[-4:] + [(payload.x, payload.y)]
            self.payload_times = self.payload_times[-4:] + [time()]
            self.heading = payload.heading
            self.turret_heading = payload.turret_heading
            self.health = payload.health
            self.ammo = payload.ammo

    def has_ammo(self) -> bool:
        return self.ammo > 0

    def current_pos(self) -> Tuple[float, float]:
        return self.position[-1]

    def previous_pos(self) -> Tuple[float, float]:
        return self.position[-2] if len(self.position) > 1 else None
    
    def current_pos_time(self) -> float:
        return self.payload_times[-1]
    
    def previous_pos_time(self) -> float:
        return self.payload_times[-2] if len(self.payload_times) > 1 else None

    def is_aiming_at(self, position: Vector) -> bool:
        """
        Returns true if the enemy tank is aiming at the given position
        """
        heading_to_player = heading_from_to(self.current_pos(), position)
        return within_degrees(10, self.turret_heading, heading_to_player)

    def has_vision_of(self, position: Vector) -> bool:
        """
        Returns true if the given position is in the enemy tanks FOV
        """
        heading_to_player = heading_from_to(self.current_pos(), position)
        distance_from_player = calculate_distance(self.current_pos(), position)
        return within_degrees(90, self.turret_heading, heading_to_player) and (distance_from_player <= 100)
