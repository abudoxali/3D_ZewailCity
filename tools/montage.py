"""Quick labelled contact sheet: montage.py "<glob>" out.jpg [cols]"""
import sys,glob,os
from PIL import Image,ImageDraw
files=sorted(glob.glob(sys.argv[1]));out=sys.argv[2];cols=int(sys.argv[3]) if len(sys.argv)>3 else 4
w,h=480,270
rows=(len(files)+cols-1)//cols
M=Image.new('RGB',(w*cols,h*rows),'black');d=ImageDraw.Draw(M)
for i,f in enumerate(files):
    im=Image.open(f).convert('RGB').resize((w,h));M.paste(im,((i%cols)*w,(i//cols)*h))
    d.text(((i%cols)*w+4,(i//cols)*h+4),os.path.basename(f),fill='yellow')
M.save(out)
