#!/usr/bin/env python3
"""Make the website's images from the app repo's real captures and art.

    python3 -I _ops/make_assets.py

Reads  ~/indie/SeaWindow/Tools/Website/captures/*.png   real 1320x2868 simulator captures
       ~/indie/SeaWindow/Tools/AppStore/art/backdrop-moon.png   ChatGPT/Codex ocean art
       ~/indie/SeaWindow/SeaWindow/Resources/Assets.xcassets/AppIcon.appiconset/AppIcon.png
Writes assets/screens/*.webp, assets/hero-ocean.webp, assets/app-icon*.png,
       assets/favicon-32.png, assets/og.png

Captures are only resized, never edited, so the site shows what the app does.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SITE = Path(__file__).resolve().parents[1]
APP = Path.home() / 'indie/SeaWindow'
CAPS = APP / 'Tools/Website/captures'
OUT = SITE / 'assets'
SCREENS = OUT / 'screens'
SCREENS.mkdir(parents=True, exist_ok=True)

SHOTS = {
    '01-today': 'today',
    '02-forecast': 'forecast',
    '03-forecast-scrolled': 'charts',
    '04-sky': 'sky',
    '05-places': 'places',
    '07-tables': 'tables',
}
W = 660  # 2x for a ~330 px phone

for src, name in SHOTS.items():
    im = Image.open(CAPS / f'{src}.png').convert('RGB')
    h = round(im.height * W / im.width)
    im.resize((W, h), Image.LANCZOS).save(SCREENS / f'{name}.webp', 'WEBP', quality=82, method=6)

# Hero ocean: the lower part of the moon backdrop (horizon, moon, waves), wide crop.
art = Image.open(APP / 'Tools/AppStore/art/backdrop-moon.png').convert('RGB')
crop = art.crop((0, 420, 1024, 1536))  # 1024 x 1116
crop.save(OUT / 'hero-ocean.webp', 'WEBP', quality=72, method=6)

icon = Image.open(APP / 'SeaWindow/Resources/Assets.xcassets/AppIcon.appiconset/AppIcon.png').convert('RGB')
icon.resize((256, 256), Image.LANCZOS).save(OUT / 'app-icon.png', optimize=True)
icon.resize((180, 180), Image.LANCZOS).save(OUT / 'apple-touch-icon.png', optimize=True)
# Favicon: the icon inside a rounded square so it reads at 32 px.
fav = icon.resize((64, 64), Image.LANCZOS)
mask = Image.new('L', (64, 64), 0)
ImageDraw.Draw(mask).rounded_rectangle((0, 0, 63, 63), 14, fill=255)
f = Image.new('RGBA', (64, 64))
f.paste(fav, (0, 0), mask)
f.resize((32, 32), Image.LANCZOS).save(OUT / 'favicon-32.png', optimize=True)

# Open Graph card, 1200 x 630.
FONT = '/Library/Fonts/SF-Pro-Display-{}.otf'
og = Image.new('RGB', (1200, 630), (7, 16, 31))
bg = art.crop((0, 500, 1024, 1038)).resize((1200, 630), Image.LANCZOS)
og.paste(bg, (0, 0))
shade = Image.new('RGBA', (1200, 630))
d = ImageDraw.Draw(shade)
for x in range(1200):  # darken the left side for the text
    a = int(max(0, 215 - x * 0.28))
    d.line([(x, 0), (x, 630)], fill=(7, 16, 31, a))
og.paste(shade, (0, 0), shade)
d = ImageDraw.Draw(og)
ic = icon.resize((96, 96), Image.LANCZOS)
m = Image.new('L', (96, 96), 0)
ImageDraw.Draw(m).rounded_rectangle((0, 0, 95, 95), 22, fill=255)
og.paste(ic, (64, 64), m)
d.text((180, 78), 'SeaWindow', font=ImageFont.truetype(FONT.format('Bold'), 44), fill=(255, 255, 255))
d.text((182, 130), 'for iPhone', font=ImageFont.truetype(FONT.format('Medium'), 24), fill=(178, 204, 212))
head = ImageFont.truetype(FONT.format('Heavy'), 66)
d.text((64, 230), 'Know the tide', font=head, fill=(255, 255, 255))
d.text((64, 306), 'before you go.', font=head, fill=(89, 224, 240))
d.text((64, 410), 'Tide times, charts, coastal weather,', font=ImageFont.truetype(FONT.format('Medium'), 30), fill=(205, 225, 230))
d.text((64, 450), 'sun and moon for your coast.', font=ImageFont.truetype(FONT.format('Medium'), 30), fill=(205, 225, 230))
# Phone with the real Today capture.
shot = Image.open(CAPS / '01-today.png').convert('RGB')
pw = 300
ph = round(shot.height * pw / shot.width)
shot = shot.resize((pw, ph), Image.LANCZOS)
frame = Image.new('RGBA', (pw + 20, ph + 20), (0, 0, 0, 0))
ImageDraw.Draw(frame).rounded_rectangle((0, 0, pw + 19, ph + 19), 52, fill=(9, 14, 20, 255))
sm = Image.new('L', (pw, ph), 0)
ImageDraw.Draw(sm).rounded_rectangle((0, 0, pw - 1, ph - 1), 44, fill=255)
frame.paste(shot, (10, 10), sm)
glow = Image.new('RGBA', og.size, (0, 0, 0, 0))
ImageDraw.Draw(glow).rounded_rectangle((812, 70, 1132, 760), 60, fill=(89, 224, 240, 70))
glow = glow.filter(ImageFilter.GaussianBlur(40))
og.paste(glow, (0, 0), glow)
og.paste(frame, (812, 60), frame)
og.save(OUT / 'og.jpg', quality=86, optimize=True, progressive=True)
print('assets written')
