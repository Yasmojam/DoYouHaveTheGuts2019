from .state import State
from utils import heading_from_to, within_degrees, calculate_distance
from enemy import Enemy
from time import time


class AttackState(State):
    def __init__(self, turret_controls, body_controls, status, priority):
        super().__init__(turret_controls, body_controls, status, priority)
        self.target = None
        self.fireNext = 0
        self.lastFireTime = 0.0

    def perform(self):
        (enemy, next_heading) = self.getEnemyAndHeading()
        # self.turret_controls.aim_left()
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
        enemy = self.target if self.target else self.status.find_best_enemy_target()
        position = self.status.position

        next_heading = heading_from_to(position, enemy.current_pos())
        return (enemy, next_heading)

    def isReadyToFire(self, target, target_heading) -> bool:
        heading = self.status.turret_heading

        distance = calculate_distance(self.status.position, target.current_pos())
        angle_allowed = (105 - distance) / 5

        time_since_last = time() - self.lastFireTime

        return within_degrees(angle_allowed, heading, target_heading) and (time_since_last > 2)


    def calculate_priority(self, is_current_state: bool) -> float:
        enemy = self.status.find_best_enemy_target()
        if enemy is not None and self.status.ammo > 0:
            self.target = enemy
            return 0.5 + self.base_priority  # Default as only 2 attacking priorities
        self.target = None
        return 0
