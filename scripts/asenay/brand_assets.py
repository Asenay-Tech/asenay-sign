"""Asenay Sign brand assets (replaces the Documenso logos, favicons and social image).

Sources: the Asenay wordmark and mark from the Asenay website repo. Run from the repo root:
    python scripts/asenay/brand_assets.py
"""
from PIL import Image, ImageDraw, ImageFont

SITE = r"C:\Users\henok\Asenay website\public"
WORD = Image.open(SITE + r"\logo-wordmark.png").convert("RGBA")      # Asenay mark + "Asenay"
MARK = Image.open(SITE + r"\brand\asenay-icon-512.png").convert("RGBA")  # transparent mark
INK = (32, 41, 58, 255)
FONT = r"C:\Windows\Fonts\segoeuib.ttf"


def wordmark(height):
    """The Asenay wordmark followed by 'Sign', on a transparent background."""
    w = WORD.resize((round(WORD.width * height / WORD.height), height), Image.LANCZOS)
    font = ImageFont.truetype(FONT, round(height * 0.78))
    pad = round(height * 0.22)
    tw = font.getbbox("Sign")[2]
    out = Image.new("RGBA", (w.width + pad + tw + 4, height), (0, 0, 0, 0))
    out.paste(w, (0, 0), w)
    ImageDraw.Draw(out).text((w.width + pad, height * 0.47), "Sign", font=font, fill=INK, anchor="lm")
    return out


def square(size, bg=None, scale=0.86):
    out = Image.new("RGBA", (size, size), bg or (0, 0, 0, 0))
    m = MARK.resize((round(size * scale),) * 2, Image.LANCZOS)
    out.paste(m, ((size - m.width) // 2, (size - m.height) // 2), m)
    return out


big = wordmark(320)
big.save("packages/assets/logo.png")
square(320).save("packages/assets/logo_icon.png")
small = wordmark(55)
for p in ("packages/assets/static/logo.png", "packages/email/static/logo.png", "apps/remix/public/static/logo.png"):
    small.save(p)
for base in ("packages/assets", "apps/remix/public"):
    square(192).save(f"{base}/android-chrome-192x192.png")
    square(512).save(f"{base}/android-chrome-512x512.png")
    square(180, (255, 255, 255, 255), 0.8).convert("RGB").save(f"{base}/apple-touch-icon.png")
    square(16, scale=1).save(f"{base}/favicon-16x16.png")
    square(32, scale=1).save(f"{base}/favicon-32x32.png")
    square(256, scale=1).save(f"{base}/favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    og = Image.new("RGB", (1200, 630), (255, 255, 255))
    wm = wordmark(150)
    og.paste(wm, ((1200 - wm.width) // 2, 200), wm)
    ImageDraw.Draw(og).text((600, 430), "Documents and e-signatures", font=ImageFont.truetype(FONT, 44), fill=(75, 85, 99), anchor="mm")
    og.save(f"{base}/opengraph-image.jpg", quality=90)
print("brand assets written")

# sign-up example profile: the Asenay mark instead of Documenso's founder photo
square(320, (255, 255, 255, 255), 0.7).convert("RGB").save("packages/assets/images/timur.png")

# background pattern: Documenso green -> Asenay blue (hue rotation of the coloured pixels)
import colorsys
pat = Image.open("packages/assets/images/background-pattern.png").convert("RGBA")
px = pat.load()
for y in range(pat.height):
    for x in range(pat.width):
        r, g, b, a = px[x, y]
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        if s > 0.05 and 0.15 < h < 0.45:            # greens only
            r2, g2, b2 = colorsys.hsv_to_rgb(0.6, s, v)
            px[x, y] = (round(r2 * 255), round(g2 * 255), round(b2 * 255), a)
pat.save("packages/assets/images/background-pattern.png")
print("profile + pattern written")
