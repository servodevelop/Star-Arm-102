"""Detect one leader's button board without moving or unlocking the arm."""

import argparse
import sys

import fashionstar_uart_sdk as uservo
import serial

from stararm102_dual import ButtonCommandUART, observe_button_commands, positive_int


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', required=True, help='leader serial port')
    parser.add_argument('--baudrate', type=int, default=1_000_000)
    parser.add_argument('--button-id', type=int, default=7, help='button board ID (default: 7)')
    parser.add_argument('--wait-seconds', type=positive_int, default=10,
                        help='time to wait for a new-board button press (default: 10)')
    args = parser.parse_args(argv)
    if args.baudrate <= 0 or not 7 <= args.button_id <= 253:
        parser.error('use a positive baud rate and a button ID from 7 to 253')
    try:
        with serial.Serial(args.port, baudrate=args.baudrate, timeout=0) as uart:
            button_uart = ButtonCommandUART(uart)
            bus = uservo.UartServoManager(button_uart)
            if not any(bus.ping(0) for _ in range(3)):
                print('Leader communication failed: check port, power, baud rate, and wiring.',
                      file=sys.stderr)
                return 2
            if any(bus.ping(args.button_id) for _ in range(3)):
                print(f'Button board detected: {args.port}, ID {args.button_id}.')
                return 0
            print(f'ID {args.button_id} did not respond. Press the new button board within '
                  f'{args.wait_seconds} seconds; it may lock or unlock the leader.', flush=True)
            if observe_button_commands(button_uart, args.wait_seconds):
                state = 'locked' if button_uart.locked else 'unlocked'
                print(f'Button board detected: {args.port}, command protocol, {state}.')
                return 0
    except (serial.SerialException, OSError) as exc:
        print(f'Connection error: {exc}', file=sys.stderr)
        return 2
    print(f'No button board response at ID {args.button_id} and no complete new-board '
          'button command was observed. Retry while pressing the button; '
          'check wiring before choosing button-disable.')
    return 1


if __name__ == '__main__':
    sys.exit(main())
