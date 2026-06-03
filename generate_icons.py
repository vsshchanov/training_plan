"""Генерирует PNG-иконки для PWA из SVG через встроенный модуль."""
import struct
import zlib
import os

def make_png(size, bg=(26, 29, 35), fg=(76, 175, 80)):
    """Создаёт простой PNG с логотипом (штанга) нужного размера."""
    w = h = size
    img = []
    for y in range(h):
        row = []
        for x in range(w):
            # Фон
            r, g, b = bg
            # Гриф (горизонтальная полоса по центру, 8% высоты)
            bar_h = max(4, h // 12)
            bar_y = (h - bar_h) // 2
            if bar_y <= y < bar_y + bar_h:
                r, g, b = fg
            # Левый блин
            pl_w = max(6, w // 14)
            pl_h = max(20, h // 3)
            pl_y = (h - pl_h) // 2
            pl_x = max(8, w // 10)
            if pl_y <= y < pl_y + pl_h and pl_x <= x < pl_x + pl_w:
                r, g, b = 255, 255, 255
            # Правый блин
            if pl_y <= y < pl_y + pl_h and (w - pl_x - pl_w) <= x < (w - pl_x):
                r, g, b = 255, 255, 255
            row += [r, g, b, 255]
        img.append(bytes([0] + row))

    def crc(data):
        return struct.pack('>I', zlib.crc32(data) & 0xffffffff)

    def chunk(name, data):
        return struct.pack('>I', len(data)) + name + data + crc(name + data)

    raw = zlib.compress(b''.join(img))
    png = (b'\x89PNG\r\n\x1a\n'
           + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
           + chunk(b'IDAT', raw)
           + chunk(b'IEND', b''))
    return png


os.makedirs('static/icons', exist_ok=True)
for size in (192, 512):
    with open(f'static/icons/icon-{size}.png', 'wb') as f:
        f.write(make_png(size))
print('[INFO] Иконки PWA сгенерированы')
