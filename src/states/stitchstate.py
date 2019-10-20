from .state import State
from .constants import COLLECTABLE_CHECKPOINTS
from utils import closest_point, calculate_distance
import numpy as np

TANK_SPEED = 10

class SnitchState(State):
    def perform(self) -> None:
        self.body_controls.movetopoint(self.predict_snitch_position(self.snitch))

    def predict_snitch_position(self, snitch):
        player_position = np.array(list(self.status.position))
        snitch_pos = np.array(list(snitch.current_pos()))
        if snitch.previous_pos() is None:
            return snitch_pos
        snitch_prev = np.array(list(snitch.previous_pos()))

        diff = snitch_pos - snitch_prev

        snitch_pos_time = snitch.current_pos_time()
        snitch_prev_time = snitch.previous_pos_time()

        distance = calculate_distance(player_position, snitch_pos)
        time = distance / TANK_SPEED

        diff = diff * time / (snitch_pos_time - snitch_prev_time)
        return (snitch.current_pos() + diff).tolist()

    def calculate_priority(self, is_current_state: bool) -> None:
        if not self.status.snitch_available:
            return 0
        self.snitch = self.status.find_snitch()
        if self.snitch == None:
            return 0
        distance = calculate_distance(self.status.position, self.snitch.position)
        return (0.5 - distance/200) + self.base_priority
        #if you cant see it then dont grab it plus base priority
