import sys,math,json
from PIL import Image
PPM=16
def load(n):
    im=Image.open(n).convert('L').resize((640,640),Image.LANCZOS); return im.load()
def region_ok(x,z):
    r=math.hypot(x,z)
    if r<12.5 or r>17.5: return False
    if x<-5 and z>3: return False       # dais/altar quadrant
    if z>11: return False               # north wall objects, pillars, arch
    if abs(x)>17.5 or abs(z)>17.5: return False
    return True
def patch(px,cx,cz):  # 2x2 m patch (32x32 px) centred on world (cx,cz)
    u0=int((cx+20)*PPM)-16; v0=int((20-cz)*PPM)-16
    return [px[u0+i,v0+j] for j in range(0,32,2) for i in range(0,32,2)]
def pear(a,b):
    n=len(a); ma=sum(a)/n; mb=sum(b)/n; sa=sum((x-ma)**2 for x in a); sb=sum((y-mb)**2 for y in b)
    return 0 if sa<1e-9 or sb<1e-9 else sum((x-ma)*(y-mb) for x,y in zip(a,b))/math.sqrt(sa*sb)
def metrics(n):
    px=load(n); out={}
    # tile-mean luminance CV (2 m tiles on odd-metre centres), central vs outer
    ins=[];outs=[]
    for tx in range(-19,20,2):
        for tz in range(-19,20,2):
            r=math.hypot(tx,tz)
            if not (r<10 or 12<r<17): continue
            if tx<-5 and tz>3 or tz>11: continue
            p=patch(px,tx,tz); m=sum(p)/len(p)/255
            (ins if r<10 else outs).append(m)
    cv=lambda v:(math.sqrt(sum((x-sum(v)/len(v))**2 for x in v)/len(v))/(sum(v)/len(v)) if v else 0)
    out['tileCV_in']=round(cv(ins),4); out['tileCV_out']=round(cv(outs),4)
    # neighbour-patch correlation at lags (m) along x and z, region = outer ring floor
    for L in (2,4,6,8,10):
        cs=[]
        for cx in range(-17,18,1):
            for cz in range(-17,18,1):
                if not (region_ok(cx,cz) and region_ok(cx+L,cz)): continue
                if (cx*7+cz*3)%3: continue
                cs.append(pear(patch(px,cx,cz),patch(px,cx+L,cz)))
        out['corr_lag%dm'%L]=round(sum(cs)/len(cs),3) if cs else None
    return out
if __name__=='__main__':
    res={}
    for n in sys.argv[1:]:
        res[n]=metrics(n); print(n.split('plan_')[1][:-4].ljust(24),res[n])
    json.dump(res,open('/Users/landerstudio/MythicRoguelite/Assets/ArtTest/VisualFoundation/Reports/i2_repetition.json','w'),indent=1)
