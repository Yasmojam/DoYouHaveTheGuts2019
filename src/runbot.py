#!/usr/bin/python
import logging
import argparse
import threading
from multiprocessing import Process
from server import ServerMessageTypes, ServerComms
from statemachine import StateMachine
import time
from roles import Roles


# Parse command line args
parser = argparse.ArgumentParser()
parser.add_argument('-e', '--eight', action='store_true',
                    help='Spawn enemy team')
parser.add_argument('-d', '--debug', action='store_true',
                    help='Enable debug output')
parser.add_argument('-H', '--hostname', default='127.0.0.1',
                    help='Hostname to connect to')
parser.add_argument('-p', '--port', default=8052,
                    type=int, help='Port to connect to')
parser.add_argument('-n', '--name', default='PYJIN:TimScorer', help='Name of bot')
args = parser.parse_args()

# Set up console logging
if args.debug:
    logging.basicConfig(format="[%(asctime)s] %(message)s", level=logging.DEBUG)
else:
    logging.basicConfig(format="[%(asctime)s] %(message)s", level=logging.INFO)


num_bots = 1


def run_bot(teamname, name, role):

    # Connect to game server
    GameServer = ServerComms(args.hostname, args.port)

    # Spawn our tank
    logging.info("Creating tank with name '{}':'{}' and role '{}'".format(teamname,name,role))
    GameServer.sendMessage(ServerMessageTypes.CREATETANK, {'Name': name})

    state_machine = StateMachine(GameServer=GameServer, teamname=teamname, name=name, role=role)



    lock = threading.Lock()


    def recieve_messages():
        while True:
            message = GameServer.readMessage()
            lock.acquire()
            state_machine.update(message)
            lock.release()


    def run_state_machine():
        while True:
            lock.acquire()
            state_machine.choose_state()
            state_machine.perform_current_state()
            lock.release()
            time.sleep(0.2)

    message_thread = threading.Thread(target=recieve_messages)
    message_thread.start()

    state_machine_thread = threading.Thread(target=run_state_machine)
    state_machine_thread.start()



TEAM_NAME = 'PYJIN'
PLAYERS = ['Pidgey', 'Taillow', 'Starly', 'Pidove']
ROLES = [Roles.BLUE_ATTACKER, Roles.BLUE_KEEPER, Roles.RED_ATTACKER, Roles.RED_KEEPER]

ENEMY_NAME = 'NIN'
ENEMY_PLAYERS = ['Mario', 'Luigi', 'Yoshi', 'Peach']
ENEMY_ROLES = [Roles.BLUE_ATTACKER, Roles.BLUE_KEEPER, Roles.RED_ATTACKER, Roles.RED_KEEPER]

if __name__ == '__main__':
    processes = [Process(target=run_bot, args=(f"{TEAM_NAME}",f"{TEAM_NAME}:{player}",role,)) for player, role in zip(PLAYERS,ROLES)]
    for process in processes:
        process.start()

    if args.eight:
        enemy_processes = [Process(target=run_bot, args=(f"{ENEMY_NAME}",f"{ENEMY_NAME}:{player}",role,)) for player, role in zip(ENEMY_PLAYERS,ENEMY_ROLES)]
        for process in enemy_processes:
            process.start()
        
        for process in enemy_processes:
            process.join()

    for process in processes:
        process.join()
