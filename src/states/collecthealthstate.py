from .state import State
from .constants import COLLECTABLE_CHECKPOINTS
from utils import closest_point


class CollectHealthState(State):
    def perform(self) -> None:
        if self.closest_health is not None:
            self.body_controls.movetopoint(self.closest_health.position)
        else:
            self.body_controls.movetopoint(
                closest_point(self.status.position, COLLECTABLE_CHECKPOINTS)
            )

    def calculate_priority(self, is_current_state: bool) -> None:
        '''
        If full health and no health packs nearby -> dont collect health pack
        
        '''
        self.closest_health = self.status.find_nearest_health()
        if self.status.health == self.status.max_health or self.closest_health is None:
            return 0.02 # can go to the possible checkpoints
        return 0.5 - ((self.status.health - 1)/((self.status.max_health-1)*2)) + self.base_priority 
        #hard coded priority + base priority
