"""Reproduce the V15 greener derived albedo of the CC0 Poly Haven crystalline_iceplant (1K)."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageEnhance
src = Path(sys.argv[1] if len(sys.argv) > 1 else 'references/assets/crystalline_iceplant/textures/crystalline_iceplant_diff_1k.jpg')
a = np.asarray(Image.open(src).convert('RGB')).astype(np.float32) / 255.0 * np.array([0.80, 1.0, 0.74])
im = ImageEnhance.Color(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))).enhance(1.15)
out = src.with_name(src.name.replace('_diff_1k.jpg', '_diff_1k_v15green.jpg'))
im.save(out, quality=95)
print(out)
