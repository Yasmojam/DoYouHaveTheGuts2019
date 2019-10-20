from .state import State
from utils import closest_point

BLUE_GOAL = (0, 100)
RED_GOAL = (0, -100)

class GoToGoalState(State):
    def perform(self):
        goals = [(0, 100), (0, -100)]

        if self.status.current_minute() < 4:
            if self.status.check_red_goal_safe_again():
                closestGoal = RED_GOAL
            elif self.status.check_blue_goal_safe_again():
                closestGoal = BLUE_GOAL
            else:
                closestGoal = closest_point(self.status.position, goals)
        else:
            closestGoal = closest_point(self.status.position, goals)

        self.body_controls.movetopoint(closestGoal)

    def calculate_priority(self, is_current_state: bool):
        if self.status.points == 0:
            return 0  # Even though highest priority, if no points, no action
        return 0.5 + self.base_priority
