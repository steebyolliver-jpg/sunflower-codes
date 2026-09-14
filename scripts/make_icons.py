"""Draw a small geometric sunflower/check icon with the Python standard library."""
import math
import struct
import zlib
from pathlib import Path

def chunk(kind, data):
    return struct.pack('!I', len(data)) + kind + data + struct.pack('!I', zlib.crc32(kind + data) & 0xffffffff)

def draw(size):
    data = bytearray()
    for y in range(size):
        data.append(0)
        for x in range(size):
            px, py = x / size * 100, y / size * 100
            color = (248, 203, 70)
            for i in range(8):
                a = i * math.pi / 4
                cx, cy = 50 + math.cos(a) * 23, 50 + math.sin(a) * 23
                if (px - cx)**2 + (py - cy)**2 < 13**2:
                    color = (255, 244, 186)
            if (px-50)**2 + (py-50)**2 < 20**2:
                color = (44, 87, 59)
            for ax, ay, bx, by in [(40, 50, 47, 57), (47, 57, 61, 42)]:
                t = max(0, min(1, ((px-ax)*(bx-ax)+(py-ay)*(by-ay))/((bx-ax)**2+(by-ay)**2)))
                if (px-(ax+t*(bx-ax)))**2+(py-(ay+t*(by-ay)))**2 < 2.5**2:
                    color = (255, 244, 186)
            data.extend(color)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('!2I5B', size, size, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(data)) + chunk(b'IEND', b'')

if __name__ == '__main__':
    for size in (192, 512):
        (Path(__file__).resolve().parents[1] / 'dist' / f'icon-{size}.png').write_bytes(draw(size))
