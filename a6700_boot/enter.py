"""Fixed read-payload injection; default is offline validation, never flashing."""
import argparse
import time

from .pico import Pico
from .records import boot_records, verified_payload


def transmit(device, records, timeout, *, clock=time.monotonic, sleep=time.sleep, say=print):
    device.ping()
    try:
        device.carrier(False)
        device.disable_pull()
        device.carrier(True)
        sleep(0.01)
        if device.sense():
            raise RuntimeError('Baseline already HIGH. Disconnect breakout from camera and cold-start again; nothing sent.')
        say('ARMED: baseline LOW. Now insert breakout, install battery, switch camera ON.', flush=True)
        started = clock()
        while not device.sense():
            if clock() - started >= timeout:
                raise TimeoutError('Camera activation not detected; no records sent')
            device.carrier(True)  # Keep the Pico 1200 ms starvation guard alive.
            sleep(0.02)
        say('Camera release HIGH detected. Sending the ordered stream once.', flush=True)
        sleep(0.5)
        for index, record in enumerate(records, 1):
            device.send_record(record)
            say(f'RECORD {index}/{len(records)} ACK', flush=True)
            if index < len(records):
                sleep(0.0144)
    finally:
        # Release GP28 also on timeout, cancellation or a failed ACK. Never
        # resend a stream automatically. Pico's starvation guard is additional.
        try:
            device.carrier(False)
        finally:
            device.disable_pull()
    say('Complete stream sent once. Keep battery/ON, detach the entire breakout FIRST.', flush=True)
    say('Then move the Pico data cable to the camera. Verify USB identity and partition table.', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--payload', help='Locally built fastboot-read.bin with the published SHA-256')
    parser.add_argument('--port', help='Explicit Pico serial port; never auto-selects another device')
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--ping', action='store_true', help='Check Pico version only; no carrier')
    modes.add_argument('--arm', action='store_true', help='Transmit fixed RAM read payload after cold-boot detection')
    parser.add_argument('--activation-timeout', type=float, default=900)
    args = parser.parse_args()
    if not 1 <= args.activation_timeout <= 3600:
        parser.error('activation-timeout must be 1..3600 seconds')
    if not args.ping and not args.payload:
        parser.error('Offline validation/arming needs --payload; --ping only needs --port')
    records = boot_records(verified_payload(args.payload)) if args.payload else None
    if not args.ping and not args.arm:
        print(f'Offline validation passed: {len(records)} records. No serial/USB access.')
        return
    if not args.port:
        parser.error('--ping/--arm needs an explicit --port')
    if args.arm:
        print('Read docs/WIRING.md first. Camera OFF, battery removed >=5s, breakout OUT of camera.')
        input('Keep Pico data + USB-A power connected. Press Enter to arm; only power camera after ARMED: ')
    import serial  # Optional dependency, imported only for explicit device access.
    with serial.Serial(args.port, 115200, timeout=5, write_timeout=5, exclusive=True) as port:
        device = Pico(port)
        if args.ping:
            device.ping()
            print('PING a6700_pio_od 2; carrier not started.')
        else:
            transmit(device, records, args.activation_timeout)


if __name__ == '__main__':
    main()
