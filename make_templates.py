"""Генератор макетов COLLEGE RECORDS (запускать не обязательно: готовые файлы уже лежат в templates/).

Берёт исходный макет template_grunge.png и перекрашивает его по цветовой схеме,
сохраняя всю графику, рамку, линии и «гранж»-фактуру. Геометрия у всех макетов одинаковая,
поэтому один и тот же код вёрстки работает для любого.

Запуск (из папки бота):  python3 make_templates.py
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE = Path(__file__).resolve().parent
SRC = BASE / "template_grunge.png"
OUT = BASE / "templates"

# Схема: цвет фона, цвет «среднего тона» (рамка по краю), цвет чернил (текст/линии/рисунки),
# самый яркий цвет. glow — свечение, scan — «строки монитора».
THEMES = {
    2: dict(name="НЕОН",      bg=(5, 8, 26),    mid=(26, 62, 125),  ink=(58, 224, 255),  hi=(225, 255, 255), glow=0.40),
    3: dict(name="ПАНК",      bg=(14, 4, 4),    mid=(112, 24, 20),  ink=(236, 66, 52),   hi=(255, 228, 205), glow=0.0),
    4: dict(name="БУМАГА",    bg=(233, 225, 204), mid=(168, 152, 112), ink=(36, 30, 24), hi=(8, 6, 4),       glow=0.0),
    5: dict(name="ВЕЙПОРВЕЙВ", bg=(15, 6, 32),  mid=(112, 38, 138), ink=(255, 118, 214), hi=(255, 232, 250), glow=0.35),
    6: dict(name="ТЕРМИНАЛ",  bg=(2, 10, 4),    mid=(18, 92, 42),   ink=(92, 255, 124),  hi=(224, 255, 228), glow=0.30, scan=0.16),
    # ── 20 новых (7–26) ──
    7: dict(name="ЗАКАТ",     bg=(24, 8, 8),    mid=(128, 48, 24),  ink=(255, 122, 48),  hi=(255, 240, 210), glow=0.35),
    8: dict(name="ОКЕАН",     bg=(3, 12, 24),   mid=(16, 72, 120),  ink=(64, 170, 255),   hi=(220, 245, 255), glow=0.30),
    9: dict(name="ЛАВАНДА",   bg=(16, 10, 28),  mid=(86, 60, 140),  ink=(178, 132, 255), hi=(245, 235, 255), glow=0.30),
    10: dict(name="МЯТА",     bg=(4, 16, 14),   mid=(24, 110, 96),  ink=(64, 230, 190),   hi=(225, 255, 248), glow=0.25),
    11: dict(name="ЗОЛОТО",   bg=(18, 12, 4),   mid=(120, 88, 28),  ink=(232, 186, 72),   hi=(255, 248, 225), glow=0.30),
    12: dict(name="РОЗА",     bg=(22, 6, 14),   mid=(130, 34, 80),  ink=(255, 92, 152),   hi=(255, 230, 240), glow=0.30),
    13: dict(name="ЛЕС",      bg=(4, 12, 6),    mid=(34, 84, 40),   ink=(120, 200, 110),   hi=(235, 255, 235), glow=0.15),
    14: dict(name="ПУСТЫНЯ",  bg=(26, 18, 10),  mid=(140, 108, 62), ink=(222, 184, 120),  hi=(255, 248, 230), glow=0.10),
    15: dict(name="ЛЬДИНА",   bg=(10, 18, 28),  mid=(80, 130, 170), ink=(190, 225, 250),  hi=(255, 255, 255), glow=0.20),
    16: dict(name="СЛИВА",    bg=(18, 6, 20),   mid=(100, 36, 110), ink=(210, 110, 230),   hi=(250, 230, 255), glow=0.30),
    17: dict(name="КОФЕ",     bg=(14, 10, 8),   mid=(92, 64, 44),   ink=(196, 152, 110),   hi=(250, 240, 225), glow=0.10),
    18: dict(name="ГРАФИТ",   bg=(10, 10, 12),  mid=(70, 70, 80),   ink=(180, 180, 195),   hi=(245, 245, 250), glow=0.10),
    19: dict(name="КИСЛОТА",  bg=(10, 18, 4),   mid=(80, 140, 20),  ink=(190, 255, 60),    hi=(250, 255, 225), glow=0.35),
    20: dict(name="ВИШНЯ",    bg=(20, 4, 10),   mid=(120, 22, 48),  ink=(255, 70, 110),    hi=(255, 225, 235), glow=0.25),
    21: dict(name="ПЕПЕЛ",    bg=(16, 16, 18),  mid=(96, 96, 104),  ink=(150, 150, 160),   hi=(240, 240, 245), glow=0.0),
    22: dict(name="БИРЮЗА",   bg=(4, 16, 20),   mid=(20, 100, 120), ink=(70, 220, 230),    hi=(230, 255, 255), glow=0.25),
    23: dict(name="АМЕТИСТ",  bg=(12, 6, 24),   mid=(70, 40, 130),  ink=(150, 110, 250),   hi=(240, 230, 255), glow=0.30),
    24: dict(name="ПЕРСИК",   bg=(24, 12, 10),  mid=(140, 84, 60),  ink=(255, 170, 130),   hi=(255, 240, 230), glow=0.20),
    25: dict(name="МОХ",      bg=(8, 14, 8),    mid=(60, 96, 48),   ink=(150, 200, 120),   hi=(240, 255, 235), glow=0.15),
    26: dict(name="НОЧЬ",     bg=(4, 4, 10),    mid=(36, 36, 70),   ink=(130, 130, 220),   hi=(235, 235, 255), glow=0.25),
}
# Яркость текста исходного макета (по ней берётся цвет текста для каждой схемы)
TEXT_LUMA = 200


def lut(theme):
    xs = [0, 12, 80, 165, 255]
    cols = [theme["bg"], theme["bg"], theme["mid"], theme["ink"], theme["hi"]]
    return np.stack([np.interp(np.arange(256), xs, [c[k] for c in cols]) for k in range(3)], axis=1)


def recolor(img: Image.Image, theme) -> Image.Image:
    a = np.asarray(img.convert("RGB")).astype(np.float32)
    luma = (0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]).clip(0, 255)
    table = lut(theme)
    idx = luma.astype(np.int32)
    out = table[idx]
    if theme.get("glow"):
        bright = Image.fromarray(((luma > 120) * luma).clip(0, 255).astype(np.uint8))
        halo = np.asarray(bright.filter(ImageFilter.GaussianBlur(16))).astype(np.float32) / 255.0
        tint = np.array(theme["ink"], dtype=np.float32)
        out = out + halo[..., None] * tint * theme["glow"]
    if theme.get("scan"):
        rows = np.ones(out.shape[0], dtype=np.float32)
        rows[::5] = 1 - theme["scan"]
        out = out * rows[:, None, None]
    return Image.fromarray(out.clip(0, 255).astype(np.uint8))


def text_color(theme):
    return tuple(int(round(v)) for v in lut(theme)[TEXT_LUMA])


def main():
    OUT.mkdir(exist_ok=True)
    src = Image.open(SRC).convert("RGB")
    names = {1: "ОРИГИНАЛ"}
    previews = {1: src.copy()}
    for n, th in THEMES.items():
        img = recolor(src, th)
        img.save(OUT / f"template_{n}.jpg", quality=95, subsampling=0, optimize=True)
        previews[n] = img
        names[n] = th["name"]
        print(n, th["name"], "цвет текста:", text_color(th))

    # Коллаж для выбора в боте: 3 колонки, строк сколько нужно, с номерами
    tw, th_ = 560, 791
    pad, cap = 24, 70
    cols = 3
    keys = sorted(previews)
    rows_n = (len(keys) + cols - 1) // cols
    W, H = pad + cols * (tw + pad), pad + rows_n * (th_ + cap + pad)
    sheet = Image.new("RGB", (W, H), (16, 16, 16))
    d = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(str(BASE / "card_font.ttf"), 40)
    for i, n in enumerate(keys):
        col, row = i % cols, i // cols
        x = pad + col * (tw + pad)
        y = pad + row * (th_ + cap + pad)
        sheet.paste(previews[n].resize((tw, th_), Image.Resampling.LANCZOS), (x, y))
        d.text((x + 4, y + th_ + 14), f"{n} · {names[n]}", font=font, fill=(235, 235, 235))
    sheet.save(OUT / "choose.jpg", quality=88, optimize=True)
    print("коллаж:", sheet.size)


if __name__ == "__main__":
    main()
