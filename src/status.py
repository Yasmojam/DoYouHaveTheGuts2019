from server import ServerMessageTypes, ObjectUpdate, Message
from enemy import Enemy
from typing import List
from collectable import COLLECTABLE_TYPES, Collectable
from time import time
from utils import closest_point, calculate_distance, count_within_radius, count_not_within_radius


GOAL_UNSAFE_TIME = 20
BLUE_GOAL = (0, 100)
RED_GOAL = (0, -100)

class Status:
    def __init__(self, teamname: str, name: str, role, on_minute_change) -> None:
        self.teamname = teamname
        self.name = name
        self.id = None
        self.role = role
        self.overridden_role = None
        self.keep_override = None
        self.position = (0, 0)
        self.heading = 0
        self.turret_heading = 0
        self.max_health = 3
        self.health = self.max_health
        self.max_ammo = 10
        self.ammo = self.max_health
        self.points = 0
        self.banked_points = 0
        self.banked_before_this_minute = 0
        self.on_minute_change = on_minute_change
        self.minute = 0
        self.start_time = time()
        self.other_tanks = dict()
        self.collectables = dict()
        self.snitch_available = False
        self.snitch_carrier_id = None
        self.blue_goal_camped_recently = False
        self.red_goal_camped_recently = False
        self.blue_goal_camped_since = 0
        self.red_goal_camped_since = 0

    def update(self, message: Message) -> None:
        """ Process an incoming server message """
        if message.type == ServerMessageTypes.OBJECTUPDATE:
            payload = ObjectUpdate(message.payload)
            if payload.type == "Tank":
                if payload.name == self.name:
                    self.update_self(payload)
                else:
                    self.update_enemy(payload)
            elif payload.type in COLLECTABLE_TYPES:
                self.update_collectable(payload)
                if payload.type == "Snitch":
                    self.snitch_carrier_id = None
        elif message.type == ServerMessageTypes.KILL:
            self.kill()
        elif message.type == ServerMessageTypes.ENTEREDGOAL:
            self.reached_goal()
        elif message.type == ServerMessageTypes.SNITCHAPPEARED:
            self.snitch_spawned()
        elif message.type == ServerMessageTypes.SNITCHPICKUP:
            if message.payload["Id"] == self.id:
                self.points += 5
                self.snitch_carrier_id = None
            else:
                self.snitch_carrier_id = message.payload["Id"]
        elif message.type == ServerMessageTypes.DESTROYED:
            self.respawn()

    def kill(self) -> None:
        """ Killed an enemy """
        self.points += 1

    def reached_goal(self) -> None:
        self.banked_points += self.points
        self.points = 0

    def snitch_spawned(self) -> None:
        self.snitch_available = True

    def respawn(self) -> None:
        """ We died :( so reset our stats """
        self.points = 0
        self.health = self.max_health
        self.ammo = self.max_health

    def update_self(self, payload: ObjectUpdate) -> None:
        """
        Update status based on an ObjectUpdate for our own tank
        """
        self.position = (payload.x, payload.y)
        self.id = payload.id
        self.heading = payload.heading
        self.turret_heading = payload.turret_heading
        self.health = payload.health
        self.ammo = payload.ammo

    def update_enemy(self, payload: ObjectUpdate) -> None:
        if payload.id not in self.other_tanks:
            self.other_tanks[payload.id] = Enemy(payload)
        else:
            self.other_tanks[payload.id].update(payload)

    def update_collectable(self, payload: ObjectUpdate) -> None:
        if payload.id not in self.collectables:
            self.collectables[payload.id] = Collectable(payload)
        else:
            self.collectables[payload.id].update(payload)

    def find_nearest_ammo(self) -> Collectable:
        recently_seen = self.recently_seen_collectables(5, typ="AmmoPickup")
        if len(recently_seen) == 0:
            return None
        positions = list(map(lambda t: t.position, recently_seen))
        i = positions.index(closest_point(self.position, positions))
        return recently_seen[i]

    def find_nearest_health(self) -> Collectable:
        recently_seen = self.recently_seen_collectables(5, typ="HealthPickup")
        if len(recently_seen) == 0:
            return None
        positions = list(map(lambda t: t.position, recently_seen))
        i = positions.index(closest_point(self.position, positions))
        return recently_seen[i]

    def find_best_enemy_target(self) -> Enemy:
        def score(enemy):
            if enemy is None:
                return 1 # don't target
            dist_score = calculate_distance(self.position, enemy.current_pos()) / 100
            hp_score = enemy.health * 0.1
            return dist_score * hp_score

        snitch_carrier = self.find_snitch_carrier()
        if snitch_carrier:
            return snitch_carrier

        lowest = self.find_lowest_enemy()
        lowest_friendly = self.find_lowest_friendly()
        nearest = self.find_nearest_enemy()

        possible_targets = [lowest, lowest_friendly, nearest]
        scores = list(map(score, possible_targets))
        lowest_score = min(scores)

        for i, target in enumerate(possible_targets):
            if scores[i] == lowest_score:
                return target
        return lowest

    def find_snitch_carrier(self) -> Enemy:
        if self.snitch_carrier_id is None:
            return None
        recently_seen = self.recently_seen_enemies(3)
        for tank in recently_seen:
            if tank.id == self.snitch_carrier_id:
                return tank
        return None

    def find_nearest_enemy(self) -> Enemy:
        """ Find the nearest enemy tank """
        recently_seen = self.recently_seen_enemies(3)
        if len(recently_seen) == 0:
            return None
        positions = list(map(lambda t: t.current_pos(), recently_seen))
        i = positions.index(closest_point(self.position, positions))
        return recently_seen[i]

    def find_lowest_enemy(self) -> Enemy:
        """ Find the lowest enemy tank """
        recently_seen = self.recently_seen_enemies(5)
        if len(recently_seen) == 0:
            return None
        healths = list(map(lambda t: t.health, recently_seen))
        healths = list(filter(lambda h: h != 0, healths))
        if len(healths) == 0:
            return None
        i = healths.index(min(healths))
        return recently_seen[i]
    
    def find_lowest_friendly(self) -> Enemy:
        """ Find the lowest friendly tank """
        recently_seen = self.recently_seen_friendlies(5)
        if len(recently_seen) == 0:
            return None
        healths = list(map(lambda t: t.health, recently_seen))
        healths = list(filter(lambda h: h != 0, healths))
        if len(healths) == 0:
            return None
        i = healths.index(min(healths))
        if healths[i] == 1:
            return recently_seen[i]
        return None

    def find_snitch(self) -> Collectable:
        """ Find the snitch """
        if not self.snitch_available:
            return None
        recently_seen = self.recently_seen_collectables(5, typ="Snitch")
        if len(recently_seen) == 0:
            return None
        return recently_seen[0]

    def recently_seen_all(self, seconds) -> List[Enemy]:
        current_time = time()
        recently_seen = []
        for tank in self.other_tanks.values():
            if current_time - tank.last_seen < seconds:
                recently_seen.append(tank)
        return recently_seen

    def recently_seen_enemies(self, seconds) -> List[Enemy]:
        current_time = time()
        recently_seen = []
        for tank in self.other_tanks.values():
            if current_time - tank.last_seen < seconds:
                tank_team = tank.name.split(":")[0]
                if tank_team != self.teamname:
                    recently_seen.append(tank)
        return recently_seen

    def recently_seen_friendlies(self, seconds) -> List[Enemy]:
        current_time = time()
        recently_seen = []
        for tank in self.other_tanks.values():
            if current_time - tank.last_seen < seconds:
                tank_team = tank.name.split(":")[0]
                if tank_team == self.teamname:
                    recently_seen.append(tank)
        return recently_seen

    def recently_seen_collectables(self, seconds, typ) -> List[Collectable]:
        recently_seen = []
        for collectable_id, collectable in self.collectables.items():
            if collectable.time_since_last() < seconds and collectable.type == typ:
                recently_seen.append(collectable)
        return recently_seen
    
    def current_minute(self) -> int:
        return self.seconds_since_start() // 60

    def seconds_since_start(self) -> float:
        return time() - self.start_time
    
    def update_minute(self) -> None:
        if self.current_minute() > self.minute:
            self.on_minute_change()
            self.banked_before_this_minute = self.banked_points
            self.minute = self.current_minute()

    def banked_this_minute(self) -> int:
        return self.banked_points - self.banked_before_this_minute

    def check_blue_goal_unsafe(self) -> bool:
        if self.area_is_unsafe(BLUE_GOAL):
            self.blue_goal_camped_recently = True
            self.blue_goal_camped_since = time()
        elif time() - self.blue_goal_camped_recently > GOAL_UNSAFE_TIME:
            self.blue_goal_camped_recently = False
        return self.blue_goal_camped_recently

    def check_red_goal_unsafe(self) -> bool:
        if self.area_is_unsafe(RED_GOAL):
            self.red_goal_camped_recently = True
            self.red_goal_camped_since = time()
        elif time() - self.red_goal_camped_since > GOAL_UNSAFE_TIME:
            self.red_goal_camped_recently = False
        return self.red_goal_camped_recently

    def check_blue_goal_safe_again(self) -> bool:
        safe_again = self.area_is_safe(BLUE_GOAL)
        if safe_again:
            self.blue_goal_camped_recently = False
        return safe_again

    def check_red_goal_safe_again(self) -> bool:
        safe_again = self.area_is_safe(RED_GOAL)
        if safe_again:
            self.red_goal_camped_recently = False
        return safe_again

    def area_is_unsafe(self, point) -> bool:
        enemies = self.recently_seen_enemies(5)
        positions = list(map(lambda e: e.current_pos(), enemies))
        number_in_area = count_within_radius(positions, point, 40)
        return number_in_area >= 3
    
    def area_is_safe(self, point) -> bool:
        enemies = self.recently_seen_enemies(5)
        positions = list(map(lambda e: e.current_pos(), enemies))
        number_out_area = count_not_within_radius(positions, point, 40)
        return number_out_area >= 2
    
    def override_role(self, role, keep_override_condition) -> None:
        if not self.overridden_role:
            self.overridden_role = self.role
        self.role = role
        self.keep_override = keep_override_condition

    def finished_override(self) -> bool:
        if not self.keep_override:
            return False
        return self.keep_override()

    def remove_override(self):
        if self.overridden_role:
            self.role = self.overridden_role
        self.overridden_role = None

    def __str__(self):
        return (
            f"<{self.name}> Position: {self.position} Heading: {self.heading} "
            f"Turret: {self.turret_heading} Health: {self.health} Ammo: {self.ammo}"
        )
