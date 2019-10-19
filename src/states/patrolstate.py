from .state import State
from utils import calculate_distance
from roles import Roles

BLUE_PATROL = [(20, 80), (-20, 80)]
RED_PATROL  = [(20, -80), (-20, -80)]

class PatrolState(State):
    def __init__(self, turret_controls, body_controls, status, priority):
        super().__init__(turret_controls, body_controls, status, priority)
        self.patrol_index = 0

    def perform(self) -> None:
        target_position = (0, 0)

        if self.status.role == Roles.RED_KEEPER:
            target_position = RED_PATROL[self.patrol_index]
        elif self.status.role == Roles.BLUE_KEEPER:
            target_position = BLUE_PATROL[self.patrol_index]

        if calculate_distance(self.status.position, target_position) < 5:
            if (self.patrol_index + 1) % len(RED_PATROL) == 0:
                self.patrol_index = 0
            else:
                self.patrol_index += 1
        
        self.body_controls.movetopoint(target_position)

    def calculate_priority(self, is_current_state: bool) -> None:
        return self.base_priority + 0.4
