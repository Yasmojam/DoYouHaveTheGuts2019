from abc import ABC, abstractmethod
from status import Status


class State(ABC):
    def __init__(self, turret_controls, body_controls, status: Status, base_priority):
        self.turret_controls = turret_controls
        self.body_controls = body_controls
        self.status = status
        self.base_priority = base_priority

    @abstractmethod
    def perform(self):
        pass

    @abstractmethod
    def calculate_priority(self, is_current_state: bool):
        pass
