from server import ServerMessageTypes, ObjectUpdate, Message
from enemy import Enemy
from typing import List
from collectable import COLLECTABLE_TYPES, Collectable
from time import time
from utils import closest_point, calculate_distance


class Status:
    def __init__(self, teamname: str, name: str, role) -> None:
        self.teamname = teamname
        self.name = name
        self.id = None
        self.role = role
        self.position = (0, 0)
        self.heading = 0
        self.turret_heading = 0
        self.max_health = 3
        self.health = self.max_health
        self.max_ammo = 10
        self.ammo = self.max_health
        self.points = 0
        self.banked_points = 0
        self.other_tanks = dict()
        self.collectables = dict()
        self.snitch_available = False
        self.snitch_carrier_id = None

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
                self.points += 20
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

    def __str__(self):
        return (
            f"<{self.name}> Position: {self.position} Heading: {self.heading} "
            f"Turret: {self.turret_heading} Health: {self.health} Ammo: {self.ammo}"
        )
