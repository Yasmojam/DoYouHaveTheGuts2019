from .state import State
from .attackstate import AttackState


class StopState(State):
    def __init__(self, turret_controls, body_controls, status, priority):
        super().__init__(turret_controls, body_controls, status, priority)
        self.current_base_state = None
        self.current_turret_state = None

    def perform(self):
        pass

    def calculate_priority(self, is_current_state: bool):
        if isinstance(self.current_turret_state, AttackState):
            enemy, next_heading = self.current_turret_state.getEnemyAndHeading()
            if self.current_turret_state.isReadyToFire(enemy, next_heading):
                return 0.7 + self.base_priority
            else:
                return 0
        else:
            return 0

    def updateStates(self, base_state, turret_state):
        self.current_base_state = base_state
        self.current_turret_state = turret_state