import pygame
import sys
import argparse
from gigs import GIGS

def parse_arguments():
    parser = argparse.ArgumentParser(description='Samyang Pop Game Client')
    parser.add_argument('--tcp', action='store_true', help='Enable TCP connection')
    parser.add_argument('--type', type=int, choices=[1,2,3,4,5,6], default=1,
                      help='''Game type:
    1: Healthy Burger
    2: Sleep Disturbance
    3: Rowing Machine
    4: Pool Ball
    5: Air Siso
    6: Robot Basketball''')
    parser.add_argument('--enter', action='store_true', help='Show enter screen')
    parser.add_argument('--exit', action='store_true', help='Show exit screen')
    parser.add_argument('--score-wait-time', type=int, default=15, help='Wait time for the score screen (default: 15 seconds)')
    parser.add_argument('--countdown-time', type=int, default=10, help='Countdown time for the game start (default: 10 seconds)')
    parser.add_argument('--mqtt-broker', type=str, default=None, help='MQTT broker address')
    parser.add_argument('--mqtt-client-id', type=str, default='01', help='MQTT client ID')
    return parser.parse_args()



if __name__ == "__main__":
    args = parse_arguments()
    game = GIGS(
        use_tcp=args.tcp, 
        game_type=args.type,
        show_enter=args.enter,
        show_exit=args.exit,
        score_wait_time=args.score_wait_time,  # Pass the argument to the game
        countdown_time=args.countdown_time,    # Pass the argument to the game
        mqtt_broker=args.mqtt_broker,
        mqtt_client_id=args.mqtt_client_id
    )
    game.run()
