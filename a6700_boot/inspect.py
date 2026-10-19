"""Query fixed RAM fastboot identity/table. No dump/download/flash commands."""
import argparse
import json
from pathlib import Path


def query(device, command):
    if command not in ('getvar:product', 'getvar:version', 'oem partition'):
        raise ValueError('Command outside the published query allowlist')
    encoded = command.encode('ascii')
    if device.write(0x01, encoded, timeout=5000) != len(encoded):
        raise IOError('Incomplete fastboot command write')
    info = []
    for _ in range(256):
        response = bytes(device.read(0x81, 64, timeout=15000))
        tag, body = response[:4], response[4:].decode(errors='replace')
        if tag == b'INFO':
            info.append(body)
        elif tag == b'OKAY':
            return {'info': info, 'okay': body}
        elif tag == b'FAIL':
            raise RuntimeError('RAM service rejected query: ' + body)
        else:
            raise ValueError('Unexpected fastboot response; query stopped')
    raise RuntimeError('Too many fastboot info responses')


def inspect(device, table=False):
    identity = query(device, 'getvar:product')
    if identity['okay'] != 'A6700-AP-read-candidate':
        raise ValueError('RAM payload identity mismatch; no partition query sent')
    result = {'product': identity['okay'], 'version': query(device, 'getvar:version')['okay']}
    if table:
        result['partitions'] = query(device, 'oem partition')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--partitions', action='store_true', help='Initialize eMMC and query the table after identity matches')
    parser.add_argument('--libusb', type=Path, help='Explicit system libusb path if automatic discovery fails')
    args = parser.parse_args()
    import usb.core
    import usb.util
    import usb.backend.libusb1
    if args.libusb and not args.libusb.is_file():
        parser.error('--libusb must name an existing system library')
    backend = usb.backend.libusb1.get_backend(find_library=(lambda _: str(args.libusb.resolve())) if args.libusb else None)
    if backend is None:
        raise RuntimeError('System libusb missing; see docs/FASTBOOT.md')
    devices = list(usb.core.find(find_all=True, idVendor=0x18D1, idProduct=0x4EE0, backend=backend))
    if len(devices) != 1:
        raise RuntimeError(f'Expected exactly one RAM fastboot device, found {len(devices)}')
    device = devices[0]
    claimed = False
    try:
        try:
            config = device.get_active_configuration()
        except usb.core.USBError:
            device.set_configuration()
            config = device.get_active_configuration()
        interface = config[(0, 0)]
        if (interface.bInterfaceClass, interface.bInterfaceSubClass, interface.bInterfaceProtocol) != (0xff, 0x42, 3):
            raise ValueError('Unexpected USB interface')
        endpoints = {endpoint.bEndpointAddress for endpoint in interface}
        if not {0x01, 0x81}.issubset(endpoints):
            raise ValueError('Expected bulk endpoints missing')
        usb.util.claim_interface(device, 0)
        claimed = True
        print(json.dumps(inspect(device, args.partitions), ensure_ascii=False, indent=2))
    finally:
        if claimed:
            usb.util.release_interface(device, 0)
        usb.util.dispose_resources(device)


if __name__ == '__main__':
    main()
