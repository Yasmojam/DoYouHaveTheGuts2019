from status import Status
from server import Message
from bodymovement import BodyMovement
from turretmovement import TurretMovement
import logging
from states import (
    RoamingState,
    GoToGoalState,
    CollectHealthState,
    CollectAmmoState,
    ScanState,
    AttackState,
<<<<<<< HEAD
]
#in priority order important
=======
    RunAwayState,
    SnitchState,
    PatrolState,
    DummyState
)

AVAILABLE_TURRET_STATES = [ScanState, AttackState]
>>>>>>> b84dca6ed54aef98ceab42bb4e9e2800cb863a3a
AVAILABLE_BODY_STATES = [
    GoToGoalState,
    SnitchState,
    CollectHealthState,
    CollectAmmoState,
    RunAwayState,
<<<<<<< HEAD
    RoamingState
=======
    SnitchState,
    PatrolState
>>>>>>> b84dca6ed54aef98ceab42bb4e9e2800cb863a3a
]

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
        self.status = Status(teamname=teamname, name=name, role=role)
        self.GameServer = GameServer
        self.turret_controls = TurretMovement(GameServer=GameServer, status=self.status)
        self.body_controls = BodyMovement(GameServer=GameServer, status=self.status)
<<<<<<< HEAD
        self.turret_states = []
        for State, priority in zip(AVAILABLE_TURRET_STATES, turret_base_priorities):
            self.turret_states.append(State(self.turret_controls, self.body_controls, self.status, priority))
        self.body_states = []
        for State, priority in zip(AVAILABLE_BODY_STATES, body_base_priorities):
            self.body_states.append(State(self.turret_controls, self.body_controls, self.status, priority))
=======
        self.turret_states = list(
            map(
                lambda State: State(
                    self.turret_controls, self.body_controls, self.status
                ),
                AVAILABLE_TURRET_STATES,
            )
        )
        self.body_states = list(
            map(
                lambda State: State(
                    self.turret_controls, self.body_controls, self.status
                ),
                AVAILABLE_BODY_STATES,
            )
        )
>>>>>>> b84dca6ed54aef98ceab42bb4e9e2800cb863a3a
        self.current_turret_state_i = 0
        self.current_turret_state = self.turret_states[0]
        self.current_body_state_i = 0
        self.current_body_state = self.body_states[0]

    def update(self, message: Message) -> None:
        self.status.update(message=message)
        logging.info(f"Recieved message {message.type}: {message.payload}")

    def choose_state(self) -> None:
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
        self.current_turret_state = self.turret_states[self.current_turret_state_i]
        if isinstance(self.current_turret_state, AttackState):
            enemy, next_heading = self.current_turret_state.getEnemyAndHeading()
            if self.current_turret_state.isReadyToFire(enemy, next_heading):
                self.current_body_state = DummyState(self.turret_controls, self.body_controls, self.status)
            else:
                self.current_body_state = self.body_states[self.current_body_state_i]
        else:
            self.current_body_state = self.body_states[self.current_body_state_i]

    def perform_current_state(self) -> None:
<<<<<<< HEAD
        logging.info(f"Performing states: {self.current_body_state} {self.current_turret_state}")
        logging.info(f"Base priorities: Body: {body_base_priorities}\nTurret:{turret_base_priorities}")
=======
        logging.info(
            f"Performing states: {self.current_body_state} {self.current_turret_state}"
        )
>>>>>>> b84dca6ed54aef98ceab42bb4e9e2800cb863a3a
        self.current_body_state.perform()
        self.current_turret_state.perform()
