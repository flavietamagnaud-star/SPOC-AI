from __future__ import annotations

from pathlib import Path
from hashlib import md5
from typing import Iterable, Mapping
from PIL import Image, ImageDraw, ImageFont

ASSET_DIR = Path(__file__).with_name('assets')
ASSET_DIR.mkdir(exist_ok=True)

PALETTES = [
    ('#FFF2E2', '#F7A24A', '#B65C10'),
    ('#E9F7EF', '#59B87A', '#1D6B3F'),
    ('#EAF2FF', '#6D8BFF', '#3359D4'),
    ('#FFF0F5', '#E26A9F', '#A13A69'),
    ('#F6F0FF', '#9D74E8', '#5D39A8'),
    ('#F3FBFF', '#4DB7D7', '#11708C'),
    ('#FFF7E8', '#F0C04C', '#9E6A05'),
]


def _slugify(text: str) -> str:
    return ''.join(c.lower() if c.isalnum() else '_' for c in text).strip('_')[:80]


def _pick_palette(title: str):
    idx = int(md5(title.encode('utf-8')).hexdigest(), 16) % len(PALETTES)
    return PALETTES[idx]


def _font(size: int, bold: bool = False):
    font_candidates = [
        '/System/Library/Fonts/Supplemental/Arial Bold.ttf' if bold else '/System/Library/Fonts/Supplemental/Arial.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    ]
    for path in font_candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_width: int):
    words = text.split()
    lines, current = [], ''
    for word in words:
        trial = f'{current} {word}'.strip()
        if draw.textbbox((0, 0), trial, font=font)[2] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines[:3]


def _chip(draw, xy, text, fill, font, text_fill='white'):
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=18, fill=fill)
    bbox = draw.textbbox((0, 0), text, font=font)
    tx = x1 + (x2 - x1 - (bbox[2] - bbox[0])) / 2
    ty = y1 + (y2 - y1 - (bbox[3] - bbox[1])) / 2 - 1
    draw.text((tx, ty), text, font=font, fill=text_fill)


def create_recipe_card(title: str, ingredients: Iterable[str], tags: Iterable[str], minutes: int, out_path: Path):
    bg, accent, dark = _pick_palette(title)
    img = Image.new('RGB', (960, 560), bg)
    draw = ImageDraw.Draw(img)

    # background bands
    draw.rounded_rectangle((35, 35, 925, 525), radius=34, fill='white')
    draw.rounded_rectangle((35, 35, 925, 205), radius=34, fill=accent)
    draw.rectangle((35, 170, 925, 205), fill=accent)

    title_font = _font(42, bold=True)
    body_font = _font(22)
    chip_font = _font(18, bold=True)
    small_font = _font(16)

    title_lines = _wrap(draw, title, title_font, 500)
    ty = 78
    for line in title_lines:
        draw.text((80, ty), line, font=title_font, fill='white')
        ty += 48

    _chip(draw, (80, 160, 200, 196), f'{minutes} min', fill=dark, font=chip_font)
    if tags:
        first_tag = list(tags)[0].replace('-', ' ').title()
        _chip(draw, (215, 160, 390, 196), first_tag, fill='#ffffff', font=chip_font, text_fill=dark)

    # Stylized plate on the right
    cx, cy = 730, 260
    draw.ellipse((cx - 150, cy - 150, cx + 150, cy + 150), fill='#F4F4F4', outline='#E0E0E0', width=4)
    draw.ellipse((cx - 108, cy - 108, cx + 108, cy + 108), fill='#FFFFFF', outline='#EAEAEA', width=2)

    selected = list(ingredients)[:6]
    bubble_positions = [
        (cx - 70, cy - 50), (cx + 5, cy - 60), (cx - 20, cy + 5),
        (cx - 85, cy + 40), (cx + 45, cy + 35), (cx + 65, cy - 5)
    ]
    bubble_colors = ['#F6B26B', '#93C47D', '#E06666', '#76A5AF', '#FFD966', '#C27BA0']
    for idx, item in enumerate(selected):
        bx, by = bubble_positions[idx % len(bubble_positions)]
        draw.ellipse((bx, by, bx + 86, by + 86), fill=bubble_colors[idx % len(bubble_colors)], outline='white', width=4)
        text = item.replace('_', ' ').title()
        lines = _wrap(draw, text, small_font, 68)
        line_y = by + 27 - (len(lines)-1) * 9
        for ln in lines:
            bb = draw.textbbox((0, 0), ln, font=small_font)
            line_x = bx + 43 - (bb[2] - bb[0]) / 2
            draw.text((line_x, line_y), ln, font=small_font, fill='white')
            line_y += 18

    draw.text((80, 250), 'Main ingredients', font=_font(24, bold=True), fill=dark)
    ingredient_text = ', '.join(i.replace('_', ' ') for i in list(ingredients)[:10])
    lines = _wrap(draw, ingredient_text, body_font, 430)
    y = 292
    for line in lines:
        draw.text((80, y), line, font=body_font, fill='#36403B')
        y += 32

    draw.text((80, 410), 'FridgeChef AI', font=_font(28, bold=True), fill=accent)
    draw.text((80, 448), 'Cook smarter with what you already have', font=body_font, fill='#5F6B66')

    out_path.parent.mkdir(exist_ok=True)
    img.save(out_path, format='PNG')
    return out_path


def get_recipe_image(recipe: Mapping[str, object]) -> str:
    title = str(recipe.get('name', 'recipe'))
    slug = _slugify(title)
    out_path = ASSET_DIR / f'{slug}.png'
    if not out_path.exists():
        create_recipe_card(
            title=title,
            ingredients=list(recipe.get('ingredients', [])),
            tags=list(recipe.get('tags', [])),
            minutes=int(recipe.get('minutes', 0) or 0),
            out_path=out_path,
        )
    return str(out_path)
