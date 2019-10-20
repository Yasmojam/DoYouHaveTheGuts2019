from .state import State
from utils import calculate_distance
from roles import Roles

# Patrol coords for goalkeepers
BLUE_GOAL_PATROL = [(20, 80), (-20, 80)]
RED_GOAL_PATROL  = [(20, -80), (-20, -80)]

# Patrol coords for snipers
BLUE_SNIPER_PATROL = [(25, 0), (-25, 0)]
RED_SNIPER_PATROL = [(25, 0), (-25, 0)]

class PatrolState(State):
    def __init__(self, turret_controls, body_controls, status, priority):
        super().__init__(turret_controls, body_controls, status, priority)
        self.patrol_index = 0

    def perform(self) -> None:
        target_position = (0, 0)

        if self.status.role == Roles.RED_KEEPER:
            target_position = RED_GOAL_PATROL[self.patrol_index]
            self.get_next_waypoint(target_position, RED_GOAL_PATROL)
        elif self.status.role == Roles.BLUE_KEEPER:
            target_position = BLUE_GOAL_PATROL[self.patrol_index]
            self.get_next_waypoint(target_position, BLUE_GOAL_PATROL)
        elif self.status.role == Roles.RED_SNIPER:
            target_position = RED_SNIPER_PATROL[self.patrol_index]
            self.get_next_waypoint(target_position, RED_SNIPER_PATROL)
        elif self.status.role == Roles.BLUE_SNIPER:
            target_position = BLUE_SNIPER_PATROL[self.patrol_index]
            self.get_next_waypoint(target_position, BLUE_SNIPER_PATROL)

        
        self.body_controls.movetopoint(target_position)

    def calculate_priority(self, is_current_state: bool) -> None:
        if self.status.role in [Roles.RED_KEEPER, Roles.BLUE_KEEPER, Roles.RED_SNIPER, Roles.BLUE_SNIPER]:
            return self.base_priority + 0.5
        return 0

    def  get_next_waypoint(self, target_position, patrol_route):
        if calculate_distance(self.status.position, target_position) < 5:
            if (self.patrol_index + 1) % len(patrol_route) == 0:
                self.patrol_index = 0
            else:
                self.patrol_index += 1
