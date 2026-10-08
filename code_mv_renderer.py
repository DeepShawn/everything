"""Deterministic frame renderer for the AI Universe MV.
Each frame is independently generated from (frame_index, FPS, fixed_seed).
"""
from fractions import Fraction
from pathlib import Path
import math, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FPS=30
W,H=960,540             # supersampled by ffmpeg to 1280x720
SEED=20261008
TOTAL=Fraction(31284,100)

# Fixed objects: initialized once; motion is a pure function of t.
rng=np.random.default_rng(SEED)
N=520
px=rng.random(N); py=rng.random(N)
ps=rng.uniform(0.25,1.4,N)
pv=rng.uniform(0.015,0.14,N)
pp=rng.uniform(0,math.tau,N)
ptype=rng.integers(0,4,N)
colors=np.array([[100,180,255],[193,120,255],[255,205,120],[116,240,215]],dtype=np.float32)

# Precomputed normalized fields.
yy,xx=np.mgrid[0:H,0:W]
xf=(xx-(W*.5))/(W*.72); yf=(yy-(H*.5))/(H*.72)
r=np.sqrt(xf*xf+yf*yf)
radial=np.clip(1-r,0,1)

font_dir='/usr/share/fonts/opentype/noto'
font_small=ImageFont.truetype(f'{font_dir}/NotoSansCJK-Regular.ttc',22)
font_tiny=ImageFont.truetype(f'{font_dir}/NotoSansCJK-Regular.ttc',16)

# section palettes: (dark, light)
PALETTES={
 'intro':((5,8,30),(62,28,95)),
 'verse1':((7,16,48),(30,96,120)),
 'orbit':((8,11,38),(64,35,112)),
 'verse2':((8,20,45),(130,45,100)),
 'interlude':((12,12,35),(72,40,96)),
 'verse3':((28,17,25),(132,75,45)),
 'finale':((7,20,47),(36,125,119)),
}

def section(t):
    if t<60: return 'intro'
    if t<102: return 'verse1'
    if t<156: return 'orbit'
    if t<174: return 'verse2'
    if t<203: return 'interlude'
    if t<225: return 'verse3'
    if t<254: return 'interlude'
    return 'finale'

def base_frame(t, sec):
    c0,c1=PALETTES[sec]
    # slow color breathing and radial bloom
    breathe=0.5+0.5*math.sin(t*0.24)
    mix=(0.18+0.22*breathe)*radial + 0.06*np.sin(xx/140+t*0.7)
    mix=np.clip(mix,0,1)[...,None]
    a=np.array(c0,dtype=np.float32); b=np.array(c1,dtype=np.float32)
    arr=a+(b-a)*mix
    # horizontal atmospheric glow
    horizon=np.exp(-((yy-H*.62)/(H*.18))**2)[...,None]
    arr += horizon*np.array([12,12,10],dtype=np.float32)
    return np.clip(arr,0,255).astype(np.uint8)

def draw_particles(arr,t,sec):
    # Deterministic orbital drift, no per-frame random calls.
    theta=pp+t*(0.45+ptype*0.08)
    x=(px + 0.035*np.sin(theta*1.7) + pv*t*0.12) % 1.0
    y=(py + 0.025*np.cos(theta*1.3) + 0.018*np.sin(t+pp)) % 1.0
    if sec in ('verse1','finale'):
        # draw particles into a shallow horizon band
        y=0.18+0.65*y
    xi=np.clip((x*W).astype(np.int32),0,W-1); yi=np.clip((y*H).astype(np.int32),0,H-1)
    twinkle=(0.35+0.65*(0.5+0.5*np.sin(t*(2.0+ptype*.7)+pp)))
    for rad in (2,1,0):
        if rad==2:
            xs=np.clip(xi+1,0,W-1); ys=yi
        elif rad==1:
            xs=xi; ys=np.clip(yi+1,0,H-1)
        else:
            xs=xi; ys=yi
        col=colors[ptype]*twinkle[:,None]
        if rad==2: col*=0.25
        elif rad==1: col*=0.55
        np.maximum.at(arr,(ys,xs),np.clip(col,0,255).astype(np.uint8))

def draw_geometry(im,t,sec):
    d=ImageDraw.Draw(im,'RGBA')
    cx,cy=W//2,int(H*.52)
    # orbital rings / network core
    phase=t*0.22
    if sec in ('intro','orbit','interlude'):
        for i in range(7):
            rx=80+i*56+18*math.sin(phase+i*.6); ry=26+i*23
            bbox=(cx-rx,cy-ry,cx+rx,cy+ry)
            d.ellipse(bbox,outline=(111,188,255,75-i*7),width=2)
        for i in range(12):
            a=phase+i*math.tau/12
            ex=cx+int((250+30*math.sin(t*.3))*math.cos(a)); ey=cy+int((130+18*math.cos(t*.25))*math.sin(a))
            d.line((cx,cy,ex,ey),fill=(113,192,255,35),width=1)
    elif sec=='verse1':
        # rising city-like light columns and perspective lines
        horizon=int(H*.66)
        for i in range(17):
            x=int((i/16)*W + 18*math.sin(t*.2+i))
            top=horizon-int(40+220*(0.5+0.5*math.sin(i*2.2+t*.25)))
            d.rectangle((x,top,x+5,horizon),fill=(92,225,255,130))
            d.line((x+2,top,x+2,horizon),fill=(160,236,255,100),width=2)
        for i in range(10):
            x=int(i*W/9)
            d.line((cx,horizon,x,H),fill=(95,185,240,40),width=1)
    elif sec=='verse2':
        for i in range(18):
            x=int((i/17)*W)
            y=int(H*.48+65*math.sin(t*.8+i*.7))
            d.line((0,y,W,y+int(35*math.sin(i+t))),fill=(230,126,224,70),width=2)
    elif sec=='verse3':
        # abstract hand / bridge gesture made from converging arcs
        for i in range(9):
            off=i*22
            d.arc((100-off,150-off,430+off,470+off),200,330,fill=(255,206,140,100),width=2)
            d.arc((530-off,160-off,860+off,480+off),210,340,fill=(130,220,255,90),width=2)
        d.ellipse((cx-48,cy-48,cx+48,cy+48),outline=(255,230,180,150),width=3)
    elif sec=='finale':
        for i in range(10):
            rx=100+i*65+25*math.sin(t*.2+i); ry=38+i*25
            d.ellipse((cx-rx,cy-ry,cx+rx,cy+ry),outline=(122,243,215,90-i*6),width=2)
    # central glow / node
    rr=int(18+8*math.sin(t*.9)**2)
    for k in range(3,0,-1):
        r0=rr*k
        d.ellipse((cx-r0,cy-r0,cx+r0,cy+r0),fill=(120,208,255,max(10,20//k)))
    d.ellipse((cx-rr,cy-rr,cx+rr,cy+rr),fill=(241,229,189,220),outline=(255,255,255,220),width=2)

def render_frame(n):
    t=n/FPS
    sec=section(t)
    arr=base_frame(t,sec)
    draw_particles(arr,t,sec)
    im=Image.fromarray(arr,'RGB')
    draw_geometry(im,t,sec)
    d=ImageDraw.Draw(im,'RGBA')
    # cinematic top labels are code-drawn, subtitles are burned later from the time contract
    d.text((42,28),'AI 大世界',font=font_small,fill=(248,238,220,230))
    d.text((44,56),'A I   U N I V E R S E',font=font_tiny,fill=(183,205,229,170))
    # vignette
    vig=np.clip((r-.35)*115,0,95).astype(np.uint8)
    overlay=np.zeros((H,W,4),dtype=np.uint8); overlay[...,3]=vig
    im=Image.alpha_composite(im.convert('RGBA'),Image.fromarray(overlay,'RGBA')).convert('RGB')
    return np.asarray(im,dtype=np.uint8)

def render_segment(start_frame,end_frame,out_path):
    out=Path(out_path); tmp=out.with_suffix(out.suffix+'.part')
    cmd=['ffmpeg','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-vf','scale=1280:720:flags=lanczos','-an','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-f','mp4',str(tmp)]
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.DEVNULL)
    try:
        for n in range(start_frame,end_frame): p.stdin.write(render_frame(n).tobytes())
        p.stdin.close(); rc=p.wait()
    except Exception:
        try: p.kill()
        except Exception: pass
        raise
    if rc!=0: raise RuntimeError(f'ffmpeg failed {rc}')
    # validation before atomic commit
    expected=end_frame-start_frame
    probe=subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames,width,height,pix_fmt','-of','default=nw=1','-f','mp4',str(tmp)],text=True)
    if f'nb_read_frames={expected}' not in probe or 'width=1280' not in probe or 'height=720' not in probe:
        raise RuntimeError('segment validation failed: '+probe)
    tmp.replace(out)

if __name__=='__main__':
    if len(sys.argv)!=4: raise SystemExit('usage: render_segment.py START_FRAME END_FRAME OUT_MP4')
    render_segment(int(sys.argv[1]),int(sys.argv[2]),sys.argv[3])
