"""Ядро фирменного стиля COLLEGE RECORDS.

Единый источник правды для всех брендовых материалов:
  • палитра (кремовый «ink» на чёрном — как на карточках),
  • векторный логотип-глобус (та же геометрия, что и на макете карточки),
  • фон-текстура «тёмная бумага»,
  • типографика (Jura + Barlow Condensed, оба с кириллицей).

Всё, что рисуется, должно брать цвета и шрифты отсюда, чтобы баннер,
аватар, пост и макет карточки выглядели как один проект.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE = Path(__file__).resolve().parent
FONTS = BASE / "fonts"
BRAND = BASE / "brand"

# ─────────────────────────────── ПАЛИТРА ───────────────────────────────
# Цвета скопированы напрямую с макета template_grunge.png:
# доминирующие оливковые оттенки (96, 96, 48), (140, 140, 96), (64, 64, 32).
INK = (96, 96, 48)        # основной текст — оливковый с макета
INK_BRIGHT = (140, 140, 96)  # заголовки, акценты
INK_DIM = (64, 64, 32)     # подписи, второстепенные строки
OLIVE = (96, 96, 48)       # фирменная оливка (как на макете)
OLIVE_DIM = (64, 64, 32)   # приглушённая оливка
BLACK = (12, 13, 9)           # фон
BLACK_SOFT = (22, 23, 17)     # фон вторичных плашек

# Год бренда — единый для всех материалов.
YEAR = "2026"
WORDMARK = "COLLEGE RECORDS"
TAGLINE = "ONE COLLEGE — MANY SOUNDS"


# ─────────────────────────────── ШРИФТЫ ───────────────────────────────
def font(size: int, weight: int = 700, family: str = "barlow") -> ImageFont.FreeTypeFont:
    """Шрифт бренда. Barlow Condensed — узкий, современный, сливается со стилем макета."""
    if family == "barlow":
        path = FONTS / "BarlowCondensed-SemiBold.ttf"
    elif family == "titillium":
        path = FONTS / "TitilliumWeb-SemiBold.ttf"
    else:
        path = FONTS / "Jura.ttf"
    f = ImageFont.truetype(str(path), size)
    try:  # вариативный вес доступен только у Jura
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


def track_text(draw, xy, text, fnt, fill, anchor="la", track=0):
    """Текст с разрядкой (letter-spacing). anchor: la/ms/rs по левому краю."""
    x, y = xy
    widths = [draw.textlength(c, font=fnt) for c in text]
    total = sum(widths) + track * (len(text) - 1)
    if anchor == "ms":
        x -= total / 2
    elif anchor == "rs":
        x -= total
    for c, w in zip(text, widths):
        draw.text((x, y), c, font=fnt, fill=fill, anchor="ls")
        x += w + track
    return total


def text_width(draw, text, fnt, track=0) -> float:
    return draw.textlength(text, font=fnt) + track * max(len(text) - 1, 0)


# ─────────────────────────────── ЛОГОТИП ───────────────────────────────
def globe(target, cx, cy, rx, ry, color, width=6, seed=0):
    """Глобус-логотип COLLEGE RECORDS.

    Геометрия повторяет макет карточки: эллипс, вертикальный меридиан,
    боковые полумеридианы, две параллели и прямая линия экватора.
    Обводка чуть неровная — чтобы линия выглядела нарисованной, а не
    сгенерированной.

    target — Image или ImageDraw.
    """
    rng = random.Random(seed)
    j = lambda a: rng.uniform(-a, a)  # noqa: E731
    d = target if isinstance(target, ImageDraw.ImageDraw) else ImageDraw.Draw(target)

    # внешний эллипс — рисуем дугами, чтобы получить лёгкую неровность
    steps = 96
    for i in range(steps):
        t0 = 2 * math.pi * i / steps
        t1 = 2 * math.pi * (i + 1) / steps
        p0 = (cx + rx * math.cos(t0) + j(1.2), cy + ry * math.sin(t0) + j(1.2))
        p1 = (cx + rx * math.cos(t1) + j(1.2), cy + ry * math.sin(t1) + j(1.2))
        d.line([p0, p1], fill=color, width=width)

    # меридианы: центральный + два боковых эллипса
    for frac in (0.46,):
        w2 = rx * frac
        d.ellipse([cx - w2, cy - ry, cx + w2, cy + ry], outline=color, width=max(2, width - 2))
    d.line([(cx, cy - ry), (cx, cy + ry)], fill=color, width=max(2, width - 2))

    # параллели: две дуги сверху и снизу от экватора
    for sign in (-1, 1):
        fy = 0.5 * sign
        y = cy + ry * fy
        half = rx * math.sqrt(max(0.02, 1 - fy ** 2))
        pts = []
        for i in range(steps + 1):
            t = 2 * math.pi * i / steps
            # рисуем только «внешнюю» половину параллели
            if math.sin(t) * sign <= 0:
                continue
            pts.append((cx + half * math.cos(t), y + ry * 0.16 * math.sin(t) * -sign))
        if len(pts) > 2:
            d.line(pts, fill=color, width=max(2, width - 2), joint="curve")

    # экватор — прямая линия через весь глобус
    d.line([(cx - rx, cy + j(1.0)), (cx + rx, cy + j(1.0))], fill=color, width=width)


# ─────────────────────────────── ФОН-ТЕКСТУРА ───────────────────────────────
def paper(w: int, h: int, seed: int = 7) -> Image.Image:
    """Тёмная «бумага»: почти чёрный фон, мягкое зерно и редкие царапины.

    Принцип: текстура должна быть почти незаметной. Раньше она съедала
    буквы — теперь работает только на фоне, а текст рисуется поверх и
    остаётся чистым.
    """
    rng = np.random.default_rng(seed)
    base = np.full((h, w, 3), 0.0)
    base[:] = BLACK
    base += rng.normal(0, 1.6, (h, w, 1))
    # мягкие пятна — «неравномерность света» на бумаге
    low = rng.random((max(2, h // 40), max(2, w // 40)))
    low_img = np.asarray(
        Image.fromarray((low * 255).astype("uint8")).resize((w, h), Image.Resampling.BICUBIC)
    ).astype(float) / 255.0
    base += (low_img - 0.5)[..., None] * 7.0
    img = Image.fromarray(base.clip(0, 255).astype("uint8"))

    # редкие царапины — только в фоне, тонкие и полупрозрачные
    d = ImageDraw.Draw(img, "RGBA")
    for _ in range(int(w * h / 26000) + 4):
        x = rng.integers(0, w)
        y = rng.integers(0, h)
        ang = rng.uniform(0, 2 * math.pi)
        ln = rng.integers(30, 190)
        g = int(rng.integers(26, 60))
        d.line(
            [(x, y), (x + ln * math.cos(ang), y + ln * math.sin(ang))],
            fill=(g, g, int(g * 0.92), int(rng.integers(30, 70))),
            width=1,
        )
    # мелкая крупа — «пыль на плёнке»
    for _ in range(int(w * h / 5200)):
        x = rng.integers(0, w)
        y = rng.integers(0, h)
        g = int(rng.integers(30, 75))
        d.point((x, y), fill=(g, g, int(g * 0.9), int(rng.integers(20, 60))))

    a = np.asarray(img).astype(float)
    # мягкая виньетка: центр светлее краёв
    yy, xx = np.ogrid[:h, :w]
    dx, dy = (xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2)
    vig = 1 - 0.22 * (dx ** 2 + dy ** 2).clip(0, 1)
    a = a * vig[..., None]
    return Image.fromarray(a.clip(0, 255).astype("uint8"))


def grain(img: Image.Image, amount: int = 6, seed: int = 3) -> Image.Image:
    """Финальное зерно поверх всей картинки (после текста — не портит буквы,
    только слегка «живит» плоскость)."""
    rng = np.random.default_rng(seed)
    a = np.asarray(img).astype(float)
    a += rng.normal(0, amount, a.shape)
    return Image.fromarray(a.clip(0, 255).astype("uint8"))


def rule(draw, x1, y, x2, color=INK_DIM, width=2, gap=10, dash=18):
    """Пунктирная линейка-разделитель."""
    x = x1
    while x < x2:
        draw.line([(x, y), (min(x + dash, x2), y)], fill=color, width=width)
        x += dash + gap


# ─────────────────────────────── КОМПОЗИЦИЯ ───────────────────────────────
def wordmark(draw, x, y, size=90, color=INK_BRIGHT, track=6, anchor="ls", weight=700):
    """Логотип-надпись COLLEGE RECORDS с разрядкой."""
    return track_text(draw, (x, y), WORDMARK, font(size, weight), color, anchor, track)


def lockup(draw, cx, top, logo_w=180, text_size=76, track=5, color=INK_BRIGHT):
    """Вертикальный логотип-лок-ап: глобус над надписью.

    Возвращает высоту занятого блока.
    """
    ry = logo_w * 202 / 333  # пропорции глобуса из макета карточки
    globe(draw, cx, top + ry, logo_w / 2, ry, OLIVE, width=max(3, int(logo_w * 0.035)), seed=7)
    base = top + ry * 2 + int(text_size * 1.25)
    wordmark(draw, cx, base, text_size, color, track, anchor="ms")
    return base - top


# ─────────────────────────────── 1. АВАТАР ───────────────────────────────
def build_avatar() -> Image.Image:
    """1000×1000 — аватар профиля бота.

    Крупный глобус, под ним слово-марка и одна короткая строка.
    Никаких мелких надписей: в кружке аватара они нечитаемы.
    """
    S = 1000
    img = paper(S, S, seed=11)
    d = ImageDraw.Draw(img)

    # тонкая рамка по краю — «плёнка»/афиша
    d.rectangle([38, 38, S - 39, S - 39], outline=(92, 88, 66), width=2)
    d.rectangle([52, 52, S - 53, S - 53], outline=(58, 56, 42), width=1)

    # глобус — крупно, в верхней части
    ry = 190
    globe(d, S // 2, 300, 285, ry, OLIVE, width=13, seed=5)

    # надпись под глобусом
    base = 590
    wordmark(d, S // 2, base, 84, INK_BRIGHT, 6, anchor="ms")

    # тонкий разделитель
    rule(d, 250, base + 40, S - 250, (92, 88, 66), width=2, gap=12, dash=16)

    # слоган — единственная вторая строка
    f = font(30, 400)
    track_text(d, (S // 2, base + 92), TAGLINE, f, INK_DIM, "ms", 3)

    # подпись внизу: CR — 2026
    f2 = font(26, 500)
    track_text(d, (S // 2, S - 78), f"CR  ·  {YEAR}", f2, (120, 114, 88), "ms", 4)

    return grain(img, 5, seed=12)


# ─────────────────────────────── 2. БАННЕР ───────────────────────────────
def build_banner() -> Image.Image:
    """1592×400 — шапка, которую бот шлёт в /start.

    Горизонтальная композиция: логотип слева, текстовый блок справа.
    """
    W, H = 1592, 400
    img = paper(W, H, seed=21)
    d = ImageDraw.Draw(img)

    # вертикальный разделитель между логотипом и текстом
    d.line([(352, 96), (352, 304)], fill=(78, 75, 57), width=2)

    # глобус
    globe(d, 178, 200, 118, 72, OLIVE, width=7, seed=8)

    # подпись под глобусом (компактная, две строки)
    f_logo = font(34, 700)
    track_text(d, (178, 320), "COLLEGE", f_logo, INK_BRIGHT, "ms", 3)
    track_text(d, (178, 360), "RECORDS", f_logo, INK_BRIGHT, "ms", 3)

    # основной текстовый блок
    wordmark(d, 416, 152, 74, INK_BRIGHT, 7, anchor="ls")

    rule(d, 416, 186, 1500, (78, 75, 57), width=2, gap=12, dash=18)

    f_tag = font(31, 400)
    track_text(d, (416, 232), TAGLINE, f_tag, OLIVE, "ls", 4)

    f_info = font(27, 400)
    track_text(d, (416, 292), "15 МАКЕТОВ · КАРТОЧКА ЗА 2 МИНУТЫ", f_info, INK_DIM, "ls", 3)

    # год в правом нижнем углу
    f_year = font(24, 500)
    track_text(d, (1552, 348), YEAR, f_year, (118, 112, 86), "rs", 4)

    return grain(img, 5, seed=22)


# ─────────────────────────────── 3. ПОСТ-АНОНС ───────────────────────────────
def build_post() -> Image.Image:
    """1080×1350 — афиша открытого набора.

    Строгая модульная сетка: рамка, логотип, заголовок, инфо-блок.
    """
    W, H = 1080, 1350
    img = paper(W, H, seed=33)
    d = ImageDraw.Draw(img)

    # двойная рамка
    d.rectangle([48, 48, W - 49, H - 49], outline=(96, 92, 70), width=3)
    d.rectangle([64, 64, W - 65, H - 65], outline=(58, 56, 42), width=1)

    # верхний колонтитул
    f_top = font(22, 500)
    track_text(d, (W // 2, 122), f"OPEN CALL  ·  {YEAR}", f_top, (128, 121, 92), "ms", 6)

    # логотип-лок-ап
    globe(d, W // 2, 300, 215, 130, OLIVE, width=9, seed=12)
    wordmark(d, W // 2, 508, 76, INK_BRIGHT, 6, anchor="ms")

    rule(d, 300, 556, W - 300, (78, 75, 57), width=2, gap=14, dash=20)

    # заголовок
    f_h1 = font(72, 700)
    track_text(d, (W // 2, 664), "ТВОЙ ДЕБЮТНЫЙ", f_h1, INK_BRIGHT, "ms", 3)
    track_text(d, (W // 2, 754), "РЕЛИЗ", f_h1, INK_BRIGHT, "ms", 3)

    f_sub = font(30, 400)
    track_text(d, (W // 2, 826), "КАЖДЫЙ СТУДЕНТ — ОТДЕЛЬНЫЙ ТРЕК", f_sub, OLIVE, "ms", 3)

    # инфо-блок на плашке
    d.rectangle([150, 892, W - 150, 1078], fill=(24, 25, 18), outline=(84, 80, 60), width=2)
    f_i1 = font(40, 600)
    track_text(d, (W // 2, 962), "ОТПРАВЬ /start В БОТ", f_i1, INK_BRIGHT, "ms", 3)
    f_i2 = font(32, 400)
    track_text(d, (W // 2, 1024), "ЗА 2 МИНУТЫ · 15 МАКЕТОВ", f_i2, INK_DIM, "ms", 3)

    # подпись внизу
    f_foot = font(24, 500)
    track_text(d, (W // 2, 1150), f"{WORDMARK}  ·  {TAGLINE}", f_foot, (120, 114, 88), "ms", 4)
    track_text(d, (W // 2, 1216), YEAR, font(26, 600), (140, 133, 102), "ms", 8)

    return grain(img, 5, seed=34)


# ─────────────────────────────── СБОРКА ───────────────────────────────
def main() -> None:
    BRAND.mkdir(exist_ok=True)

    avatar = build_avatar()
    avatar.save(BRAND / "avatar.jpg", quality=94, subsampling=0, optimize=True)
    print("avatar", avatar.size)

    banner = build_banner()
    banner.save(BRAND / "banner.jpg", quality=93, subsampling=0, optimize=True)
    print("banner", banner.size)

    post = build_post()
    post.save(BRAND / "post_announce.jpg", quality=93, subsampling=0, optimize=True)
    print("post", post.size)

    print("DONE")


if __name__ == "__main__":
    main()
