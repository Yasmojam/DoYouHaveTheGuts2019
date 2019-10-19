from .state import State
from utils import heading_from_to, within_degrees, calculate_distance
import math
import numpy as np

BULLET_SPEED = 40

class AttackState(State):
    def __init__(self, turret_controls, body_controls, status):
        super().__init__(turret_controls, body_controls, status)
        self.target = None

    def predict_enemy_position(self, enemy):
        player_position = np.array(list(self.status.position))
        distance = np.sqrt( (player_position[0] - enemy.current_pos()[0])**2 + (player_position[1] - enemy.current_pos()[1])**2 )

        time = np.divide(distance, BULLET_SPEED)
        
        delta_distance = np.array([10 * math.cos(90 * enemy.heading) * time, 10 * math.sin(90 * enemy.heading)])

        return (player_position + delta_distance).tolist()


    def perform(self):
        enemy = self.target if self.target else self.status.find_best_enemy_target()
        position = self.status.position

        predicted_enemy_position = self.predict_enemy_position(enemy)

        next_heading = heading_from_to(position, predicted_enemy_position)
        # self.turret_controls.aim_left()
        self.turret_controls.aim_at_heading(next_heading)

        heading = self.status.turret_heading

        distance = calculate_distance(position, predicted_enemy_position)
        angle_allowed = (105 - distance) / 5



        if within_degrees(angle_allowed, heading, next_heading):
            self.turret_controls.fire()

    def calculate_priority(self, is_current_state: bool) -> float:
        enemy = self.status.find_best_enemy_target()
        if enemy is not None and self.status.ammo > 0:
            self.target = enemy
            return 0.5  # Default as only 2 attacking priorities
        self.target = None
        return 0
