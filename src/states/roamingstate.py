from .state import State


class RoamingState(State):
    def perform(self) -> None:
        position = self.target.current_pos()
        self.body_controls.movetopoint(position)

    def calculate_priority(self, is_current_state: bool) -> None:
        '''
        Full health + full ammo = low priority
        '''
        self.target = self.status.find_best_enemy_target()
        if self.target is None:
            return 0
        if self.status.ammo == 0:
            return 0.1
<<<<<<< HEAD
        return ((0.25 - (self.status.ammo * 0.025)) +
                (0.25 - (self.status.health * 0.025)) + self.base_priority)
=======
        return (
            (0.25 - (self.status.ammo * 0.025))
            + (0.25 - (self.status.health * 0.025))
            + (1 * 0.125)
        )
>>>>>>> b84dca6ed54aef98ceab42bb4e9e2800cb863a3a
