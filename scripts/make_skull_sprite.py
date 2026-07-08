#!/usr/bin/env python3
"""Convert the skull PNG into a single 24x21 hires sprite (skull.spr).
Bright pixels (the white skull, not the grey drop shadow) become set bits;
everything else is transparent so the field colour shows through the eyes."""
import struct, sys, zlib

IMG = sys.argv[1] if len(sys.argv) > 1 else '.context/attachments/RulTsq/image.png'
OUT = 'src/assets/skull.spr'

d = open(IMG, 'rb').read(); pos, W, H, ct, idat = 8, None, None, None, b''
while pos < len(d):
    ln = struct.unpack('>I', d[pos:pos+4])[0]; typ = d[pos+4:pos+8]
    data = d[pos+8:pos+8+ln]
    if typ == b'IHDR': W, H, ct = *struct.unpack('>II', data[:8]), data[9]
    elif typ == b'IDAT': idat += data
    elif typ == b'IEND': break
    pos += 12 + ln
bpp = 4 if ct == 6 else 3
raw = zlib.decompress(idat); stride = W*bpp
img = bytearray(); prev = bytearray(stride); p = 0
def paeth(a,b,c):
    pa,pb,pc = abs(b-c), abs(a-c), abs(a+b-2*c)
    return a if pa <= pb and pa <= pc else (b if pb <= pc else c)
for y in range(H):
    f = raw[p]; p += 1; line = bytearray(raw[p:p+stride]); p += stride
    for i in range(stride):
        a = line[i-bpp] if i >= bpp else 0; b = prev[i]
        c = prev[i-bpp] if i >= bpp else 0; x = line[i]
        line[i] = (x if f == 0 else x+a if f == 1 else x+b if f == 2
                   else x+((a+b)>>1) if f == 3 else x+paeth(a,b,c)) & 255
    img += line; prev = line
def lum(x, y):
    o = (y*W + x)*bpp
    return (img[o] + img[o+1] + img[o+2]) // 3

# crop to bright content, then sample onto the 24x21 sprite grid
xs = [x for y in range(H) for x in range(W) if lum(x, y) > 200]
ys = [y for y in range(H) for x in (0,) if any(lum(x2, y) > 200 for x2 in range(0, W, 4))]
x0, x1, y0, y1 = min(xs), max(xs)+1, min(ys), max(ys)+1
CW, CH = x1-x0, y1-y0

out = bytearray()
rows = []
for ny in range(21):
    bits = 0
    for nx in range(24):
        sx0 = x0 + nx*CW//24; sx1 = max(sx0+1, x0 + (nx+1)*CW//24)
        sy0 = y0 + ny*CH//21; sy1 = max(sy0+1, y0 + (ny+1)*CH//21)
        n = lit = 0
        for yy in range(sy0, sy1):
            for xx in range(sx0, sx1):
                n += 1
                if lum(xx, yy) > 200: lit += 1
        if lit*2 >= n:
            bits |= 1 << (23 - nx)
    rows.append(bits)
    out += bits.to_bytes(3, 'big')
out.append(0)                       # pad to a 64-byte sprite block

open(OUT, 'wb').write(bytes(out))
print(f'wrote {OUT} {len(out)} bytes')
for r in rows:
    print(''.join('#' if r & (1 << (23-i)) else '.' for i in range(24)))
