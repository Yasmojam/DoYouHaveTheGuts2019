from .state import State
from utils import heading_from_to, within_degrees, calculate_distance
import math
import numpy as np
from enemy import Enemy
from time import time
from roles import Roles

BULLET_SPEED = 40
RED_GOAL_COORDS = (0, -100)
BLUE_GOAL_COORDS = (0, 100)

class AttackState(State):
    def __init__(self, turret_controls, body_controls, status, priority):
        super().__init__(turret_controls, body_controls, status, priority)
        self.target = None
        self.fireNext = 0
        self.lastFireTime = 0.0

    def predict_enemy_position(self, enemy):
        if not isinstance(enemy, Enemy):
            return enemy
        player_position = np.array(list(self.status.position))
        enemy_pos = np.array(list(enemy.current_pos()))
        if enemy.previous_pos() is None:
            return enemy_pos
        enemy_prev = np.array(list(enemy.previous_pos()))

        diff = enemy_pos - enemy_prev

        enemy_pos_time = enemy.current_pos_time()
        enemy_prev_time = enemy.previous_pos_time()

        distance = calculate_distance(player_position, enemy_pos)
        time = distance / BULLET_SPEED

        diff = diff * time / (enemy_pos_time - enemy_prev_time)
        return (enemy.current_pos() + diff).tolist()


    def perform(self):
        if self.target is None:
            if self.status.role == Roles.BLUE_SNIPER:
                enemy = RED_GOAL_COORDS
                next_heading = heading_from_to(self.status.position, RED_GOAL_COORDS)
            elif self.status.role == Roles.RED_SNIPER:
                enemy = BLUE_GOAL_COORDS
                next_heading = heading_from_to(self.status.position, BLUE_GOAL_COORDS)
        else:
            (enemy, next_heading) = self.getEnemyAndHeading()
        self.turret_controls.aim_at_heading(next_heading)

        if self.isReadyToFire(enemy, next_heading):
            if self.fireNext > 0:
                if self.fireNext == 1:
                    self.turret_controls.fire()
                    self.lastFireTime = time()
                self.fireNext -= 1
            else:
                self.fireNext = 3

    def getEnemyAndHeading(self) -> (Enemy, float):
        if not self.target:
            self.target = self.status.find_best_enemy_target()
        enemy = self.target
        position = self.status.position



        target_pos = self.predict_enemy_position(enemy)

        next_heading = heading_from_to(position, target_pos)
        return (enemy, next_heading)

    def isReadyToFire(self, enemy, target_heading) -> bool:
        heading = self.status.turret_heading

        predicted_enemy_position = self.predict_enemy_position(enemy)        

        distance = calculate_distance(self.status.position, predicted_enemy_position)
        angle_allowed = (105 - distance) / 5
        if distance > 70 and self.status.role in [Roles.RED_SNIPER, Roles.BLUE_SNIPER]:
            angle_allowed = 10

        time_since_last = time() - self.lastFireTime

        return within_degrees(angle_allowed, heading, target_heading) and (time_since_last > 2)


    def calculate_priority(self, is_current_state: bool) -> float:
        enemy = self.status.find_best_enemy_target()
        if self.status.ammo <= 0:
            return 0
        if enemy is not None:
            self.target = enemy
            return 0.5 + self.base_priority  # Default as only 2 attacking priorities
        elif enemy is None:
            if self.status.role == Roles.BLUE_SNIPER:
                self.target = RED_GOAL_COORDS
                return 0.5 + self.base_priority
            elif self.status.role == Roles.RED_SNIPER:
                self.target = BLUE_GOAL_COORDS
                return 0.5 + self.base_priority
        self.target = None
        return 0