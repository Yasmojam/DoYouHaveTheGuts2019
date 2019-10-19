from .state import State
from .constants import COLLECTABLE_CHECKPOINTS
from utils import closest_point, calculate_distance


class SnitchState(State):
    def perform(self) -> None:
        self.body_controls.movetopoint(self.snitch.position)

    def calculate_priority(self, is_current_state: bool) -> None:
        if not self.status.snitch_available:
            return 0
        self.snitch = self.status.find_snitch()
        if self.snitch == None:
            return 0
        distance = calculate_distance(self.status.position, self.snitch.position)
<<<<<<< HEAD
        return (0.5 - distance/200) + self.base_priority
        #if you cant see it then dont grab it plus base priority
=======
        return (0.5 - distance / 200) + (3 * 0.125)
>>>>>>> b84dca6ed54aef98ceab42bb4e9e2800cb863a3a
