#!/usr/bin/env python3
"""xshot.py OUT.png [DISPLAY] -- a screenshot of the iPad's X server (M36:
XFCE on the GPU): xwd over ssh, written as a PNG here (no PIL needed).
xwd is on the iPad by tools/device-apk.sh xwd.  DEVICE=root@10.55.0.2.

    python3 tools/desktop/xshot.py /tmp/desktop.png
"""
import os, struct, subprocess, sys, zlib


def png(path, w, h, rows):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + \
            struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
    raw = b''.join(b'\0' + r for r in rows)
    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) +
                chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    display = sys.argv[2] if len(sys.argv) > 2 else ':0'
    d = subprocess.run(['ssh', os.environ.get('DEVICE', 'root@10.55.0.2'),
                        'DISPLAY=%s xwd -root -silent' % display],
                       capture_output=True, check=True).stdout
    # XWD's header: 25 big-endian words, then the window's name, the colours
    f = struct.unpack('>25I', d[:100])
    hs, w, h, bpp, bpl, ncolors = f[0], f[4], f[5], f[11], f[12], f[19]
    off = hs + 12 * ncolors
    step = bpp // 8             # (24: three bytes a pixel, rows of bpl bytes)
    rows = []
    for y in range(h):
        line = d[off + y * bpl:off + y * bpl + w * step]
        rgb = bytearray(3 * w)
        rgb[0::3] = line[2::step]
        rgb[1::3] = line[1::step]
        rgb[2::3] = line[0::step]
        rows.append(bytes(rgb))
    png(sys.argv[1], w, h, rows)
    print('%s: %d x %d' % (sys.argv[1], w, h))


if __name__ == '__main__':
    main()
