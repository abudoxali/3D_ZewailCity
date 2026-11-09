"""Label and tile captures for review: contact_sheet.py OUT.jpg COLS W img1 img2 ..."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
out, cols, w = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
files = sys.argv[4:]
h = w * 9 // 16
F = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', max(12, w // 32))
rows = (len(files) + cols - 1) // cols
sheet = Image.new('RGB', (cols * w, rows * h), '#111')
d = ImageDraw.Draw(sheet)
for i, f in enumerate(files):
    im = Image.open(f).convert('RGB').resize((w, h))
    x, y = (i % cols) * w, (i // cols) * h
    sheet.paste(im, (x, y))
    d.rectangle([x, y, x + w, y + F.size + 6], fill='#000')
    d.text((x + 4, y + 2), Path(f).stem, font=F, fill='#ffd75e')
sheet.save(out, quality=90)
print(out)
