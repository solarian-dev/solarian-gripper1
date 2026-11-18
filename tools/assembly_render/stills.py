import sys, json, numpy as np; sys.path.insert(0,'.')
import anim
from anim import world, MESH, COL, P, F, trans
M=world(0.0)
def parts(Mx, keys=None, offsets=None):
    out=[]
    for k in (keys or [k for k in list(P)+list(F) if not k.startswith('iron_')]):
        T=Mx[k] if offsets is None else trans(offsets.get(k,[0,0,0]))@Mx[k]
        out.append(dict(mesh=MESH[k],M=[float(x) for x in T.ravel()],col=list(COL[k])))
    return out
shots=[]
shots.append(dict(file='hero.png',cam=dict(target=[0,-55,15],yaw=-58,pitch=24,dist=430,fov=30),parts=parts(M),bg=[1,1,1]))
shots.append(dict(file='hero_back.png',cam=dict(target=[0,-40,20],yaw=135,pitch=22,dist=430,fov=30),parts=parts(M),bg=[1,1,1]))
# exploded view
off={}
for k in anim.LINKS: off[k]=[0,-45,0]
for k in anim.FINGERS: off[k]=[0,-70,-10]
for k in anim.sel('fing_scr'): off[k]=[0,-70,15]
for k in anim.sel('fing_nut'): off[k]=[0,-70,-30]
for k in anim.HOLDERS: off[k]=[0,-35,0]
for k in ['rail <1>']+anim.RAILSCR: off[k]=[0,-15,0]
for k in anim.SERVO_MOD: off[k]=[0,55,0]
for k in anim.CRANK: off[k]=[0,-20,-60]
for k in anim.sel('rack_nut'): off[k]=[0,55,0]
for k in anim.ADAPTER: off[k]=[0,110,0]
for k in anim.CAMMOUNT: off[k]=[0,55,55]
for k in ['camera holder v3 <1>']+[k for k in P if k.startswith('Raspberry')]+anim.sel('cam_scr'): off[k]=[0,55,85]
# separate left/right sides further
for k in anim.LEFT+[f for f in F if F[f]['group']=='L']: off[k]=list(np.array(off.get(k,[0,0,0]))+[35,0,0])
for k in anim.RIGHT+[f for f in F if F[f]['group']=='R']: off[k]=list(np.array(off.get(k,[0,0,0]))+[-35,0,0])
shots.append(dict(file='exploded.png',cam=dict(target=[0,-20,45],yaw=-50,pitch=22,dist=780,fov=30),parts=parts(M,offsets=off),bg=[1,1,1]))
json.dump(shots,open('stills.json','w'))
