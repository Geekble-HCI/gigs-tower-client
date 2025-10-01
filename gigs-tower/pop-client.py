import argparse
from gigs import GIGS
from Module.config.game_config import GameConfig

def parse_arguments():
    parser = argparse.ArgumentParser(description='Samyang Pop Game Client')
    parser.add_argument('--type', type=int, choices=[1,2,3,4,5,6,7,8], default=1,
                      help='''Game type:
    1: Healthy Burger
    2: Sleep Disturbance
    3: Rowing Machine
    4: Pool Ball
    5: Air Siso
    6: Robot Basketball''')
    parser.add_argument('--enter', action='store_true', help='Show enter screen')
    parser.add_argument('--exit', action='store_true', help='Show exit screen')
    parser.add_argument('--score-wait-time', type=int, default=GameConfig.SCORE_DISPLAY_WAIT, help='Wait time for the score screen (default: 15 seconds)')
    parser.add_argument('--countdown-time', type=int, default=GameConfig.COUNTDOWN_TIME, help='Countdown time for the game start (default: 10 seconds)')
    parser.add_argument('--mqtt-broker', type=str, default=None, help='MQTT broker address')
    parser.add_argument('--device_id', type=str, default=None, help='MQTT client ID (optional, auto-generated from type if not specified)')
    parser.add_argument('--test', action='store_true', help='Enable input handler test mode')
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    game_type = args.type
    if args.enter:
        game_type = 7
    elif args.exit:
        game_type = 8

    # device_id를 type 값으로 자동 설정 (명시적으로 지정되지 않은 경우)
    device_id = args.device_id
    if device_id is None:
        device_id = str(game_type)
        print(f"[INFO] Device ID auto-generated from type: {device_id}")

    game = GIGS(
        game_type=game_type,
        show_enter=args.enter,
        show_exit=args.exit,
        score_wait_time=args.score_wait_time,
        countdown_time=args.countdown_time,
        mqtt_broker=args.mqtt_broker,
        device_id=device_id,
        test_mode=args.test
    )
    game.run()
