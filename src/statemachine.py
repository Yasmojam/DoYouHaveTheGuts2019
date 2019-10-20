from status import Status
from server import Message
from bodymovement import BodyMovement
from turretmovement import TurretMovement
import logging
from time import time
from states import (
    RoamingState,
    GoToGoalState,
    CollectHealthState,
    CollectAmmoState,
    ScanState,
    AttackState,
    RunAwayState,
    SnitchState,
    PatrolState,
    StopState
)
from roles import Roles

AVAILABLE_TURRET_STATES = [ScanState, AttackState]
AVAILABLE_BODY_STATES = [
    GoToGoalState,
    SnitchState,
    CollectHealthState,
    CollectAmmoState,
    RunAwayState,
    SnitchState,
    StopState,
    RoamingState,
    PatrolState
]

ROLE_ROTATION = {
    Roles.BLUE_KEEPER: Roles.RED_KEEPER,
    Roles.RED_KEEPER: Roles.BLUE_KEEPER,
}

SNIPER_TIME = 30
    

def index_to_priority(index,length_list):
    return 0.5 - index/((length_list - 1)*2)

body_base_priorities = list(
    map(lambda i: index_to_priority(i, len(AVAILABLE_BODY_STATES)), range(len(AVAILABLE_BODY_STATES)))
    )

turret_base_priorities = list(
    map(lambda i: index_to_priority(i, len(AVAILABLE_TURRET_STATES)), range(len(AVAILABLE_TURRET_STATES)))
    )
    

class StateMachine:
    def __init__(self, GameServer, teamname, name, role) -> None:
        self.status = Status(teamname=teamname, name=name, role=role, on_minute_change=lambda: self.update_role())
        self.GameServer = GameServer
        self.turret_controls = TurretMovement(GameServer=GameServer, status=self.status)
        self.body_controls = BodyMovement(GameServer=GameServer, status=self.status)
        self.turret_states = []
        for State, priority in zip(AVAILABLE_TURRET_STATES, turret_base_priorities):
            self.turret_states.append(State(self.turret_controls, self.body_controls, self.status, priority))
        self.body_states = []
        for State, priority in zip(AVAILABLE_BODY_STATES, body_base_priorities):
            self.body_states.append(State(self.turret_controls, self.body_controls, self.status, priority))
        self.current_turret_state_i = 0
        self.current_turret_state = self.turret_states[0]
        self.current_body_state_i = 0
        self.current_body_state = self.body_states[0]

    def update(self, message: Message) -> None:
        self.status.update(message=message)
        logging.info(f"Recieved message {message.type}: {message.payload}")

    def choose_state(self) -> None:
        self.status.update_minute()
        self.check_role_override()
        body_priorities = [
            self.body_states[i].calculate_priority(
                is_current_state=(i == self.current_body_state_i)
            )
            for i in range(len(self.body_states))
        ]
        turret_priorities = [
            self.turret_states[i].calculate_priority(
                is_current_state=(i == self.current_turret_state_i)
            )
            for i in range(len(self.turret_states))
        ]
        logging.info(f"Body: {body_priorities}\nTurret: {turret_priorities}")
        self.current_body_state_i = body_priorities.index(max(body_priorities))
        self.current_turret_state_i = turret_priorities.index(max(turret_priorities))
        self.current_body_state = self.body_states[self.current_body_state_i]
        self.current_turret_state = self.turret_states[self.current_turret_state_i]
        ## Update current states in StopState
        self.body_states[AVAILABLE_BODY_STATES.index(StopState)].updateStates(self.current_body_state, self.current_turret_state)

    def perform_current_state(self) -> None:
        logging.info(f"Performing states: {self.current_body_state} {self.current_turret_state}")
        logging.info(f"Base priorities: Body: {body_base_priorities}\nTurret:{turret_base_priorities}")
        self.current_body_state.perform()
        self.current_turret_state.perform()
    
    def update_role(self) -> None:
        if self.status.role in ROLE_ROTATION and self.status.banked_this_minute() == 0:
            self.status.role = ROLE_ROTATION[self.status.role]
    
    def check_role_override(self) -> None:
        if self.status.finished_override():
            self.status.remove_override()

        red_goal_unsafe = self.status.check_red_goal_unsafe()
        if red_goal_unsafe:
            enter_time = time()

            def keep_blue_sniper():
                return not self.status.check_red_goal_safe_again() and time() - enter_time < SNIPER_TIME
            self.status.override_role(Roles.BLUE_SNIPER, keep_blue_sniper)
        
        blue_goal_unsafe = self.status.check_blue_goal_unsafe()
        if blue_goal_unsafe:
            enter_time = time()

            def keep_red_sniper():
                return not self.status.check_blue_goal_safe_again() and time() - enter_time < SNIPER_TIME 

            self.status.override_role(Roles.RED_SNIPER, keep_red_sniper)
        
            

        