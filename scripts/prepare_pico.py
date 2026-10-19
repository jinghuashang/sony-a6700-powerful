"""Apply our small v2 adaptation to a user's separate, pinned upstream checkout.

This script does not download, compile, flash or redistribute upstream code.
The generated local sketch retains upstream licensing status; root GPL applies
to this adapter only, not to material supplied by the upstream checkout.
"""
import argparse
import hashlib
from pathlib import Path
import shutil

from upstream import checked_upstream

ADDITIONS = '''  case 0x07: // Isolated bench pull-up, only while idle.
    if (mode != MODE_IDLE || len != 1) { send_text(EVT_ERR, "bench requires idle"); break; }
    gpio_set_pulls(MULTI_TX, d[0] != 0, false);
    send_pkt(EVT_ACK, NULL, 0);
    break;

  case 0x08: { // Read existing TX pin only; do not change the PIO or direction.
    uint8_t high = 0;
    const uint32_t start = time_us_32();
    while ((uint32_t)(time_us_32() - start) < 2000) {
      if (gpio_get(MULTI_TX)) high = 1;
    }
    send_pkt(EVT_ACK, &high, 1);
    break;
  }

'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--upstream', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=Path('build/uart_boot_upstream_pio'))
    args = parser.parse_args()
    source = checked_upstream(args.upstream) / 'tools/uart_boot'
    if args.output.exists():
        parser.error('Output exists; choose a new directory')
    text = (source / 'uart_boot.ino').read_text()
    text = text.replace('#define VERSION "uart_boot 1"',
                        '#define VERSION "a6700_pio_od 2"\n#ifndef OPEN_DRAIN\n#error This derived build requires OPEN_DRAIN\n#endif')
    text = text.replace('  case CMD_UART:', ADDITIONS + '  case CMD_UART:')
    text = text.replace('  pinMode(MULTI_RST, INPUT);',
                        '  pinMode(MULTI_RST, INPUT);\n  gpio_disable_pulls(MULTI_TX);')
    expected = 'acc13bfc67e78534ffcb1ec5164a1e45b43ce572a51f71d89b9bb489cee2cfd7'
    if hashlib.sha256(text.encode()).hexdigest() != expected:
        raise ValueError('Generated sketch differs from the locally verified v2 source')
    args.output.mkdir(parents=True)
    (args.output / (args.output.name + '.ino')).write_text(text)
    for name in ('serialboot.pio', 'serialboot.pio.h'):
        shutil.copyfile(source / name, args.output / name)
    print('Prepared v2 sources; no USB/serial access. Compile with -DOPEN_DRAIN, without UART_TX.')


if __name__ == '__main__':
    main()
