from PIL import Image, ImageDraw, ImageFont
lines=open('../deck_assets/run_output.txt',encoding='utf-8').read().splitlines()
lines=[r"PS C:\UNI\CyberAI_H\local_run> python run_audit.py"]+lines
body=lines[:12+16]+["...  (23 more rows)"]
f=ImageFont.truetype("C:/Windows/Fonts/consola.ttf",22)
W=max(f.getlength(l) for l in body)+60; H=len(body)*30+70
im=Image.new("RGB",(int(W),H),(30,30,30)); d=ImageDraw.Draw(im)
d.rectangle([0,0,W,34],fill=(55,55,55))

y=50
for l in body:
    col=(220,220,220)
    if l.startswith("PS "): col=(120,200,255)
    elif "Not billed" in l: col=(255,140,130)
    d.text((30,y),l,font=f,fill=col); y+=30
im.save("../deck_assets/local_run.png"); print(im.size)
