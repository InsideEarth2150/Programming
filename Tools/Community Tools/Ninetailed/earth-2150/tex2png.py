from PIL import Image

import os


def read_int(stream):
    return int.from_bytes(stream.read(4), byteorder='little')

def read_image(texfile, header):
    w = read_int(texfile)
    h = read_int(texfile)
    if header[0] in (0x06, 0x16, 0x26):
        mipmaps = read_int(texfile)
        img = Image.new('RGBA', (w + (w >> 1),h))
    else:
        mipmaps = 1
        img = Image.new('RGBA', (w,h))
    px = img.load()
    x = 0
    y = 0
    for i in range(mipmaps):
        img.paste(Image.frombytes('RGBA', (w, h), texfile.read(w * h * 4)), (x,y))
        if i == 0:
            x = w
        else:
            y += h
        w >>= 1
        h >>= 1
    return img


for filename in os.listdir():
    if not filename.lower().endswith('.tex'): continue
    with open(filename, 'rb') as texfile:
        magic = texfile.read(8)
        if magic != b'TEX\x00\x01\x00\x00\x00':
            raise ValueError('{filename}: No magic string in file header')
        header_a = texfile.read(4)
        a,b,c,d = header_a
        header_b = texfile.read(4)

        if header_b != b'\x88\x88\x00\x00':
            textures = int.from_bytes(header_b, 'little')
            if d == 0xc0:
                textures *= read_int(texfile)
            images = list()
            out = Image.new('RGBA', (0,0))
            for i in range(textures):
                magic = texfile.read(8)
                if magic != b'TEX\x00\x01\x00\x00\x00':
                    raise ValueError(f'{filename}: No magic string in sub header {i} {magic}')
                images.append(read_image(texfile, texfile.read(8)))
            w = sum(img.width for img in images)
            h = max(img.height for img in images)
            out = Image.new('RGBA', (w,h))
            x = 0
            for img in images:
                out.paste(img, (x, 0))
                x += img.width
        else:
            out = read_image(texfile, bytes([a,b,c,d]) + header_b)
        out.save(filename[:-4] + '.png')
