import json, sys, numpy as np, copy
sys.path.insert(0,'.')
from scene import full_parts, tolist, PLA
from kin import pose, group_M, rot_xz, trans, LEFT, RIGHT, rot2, A0, XH0, ZH
FPS=30
P=full_parts()
P['Servo Horn <1>']['M']=rot_xz(np.radians(-35.1))@P['Servo Horn <1>']['M']
STEEL=(0.32,0.33,0.36); BRASS=(0.85,0.65,0.25); ORANGE=(0.98,0.6,0.2)
for k in ['crank <1>','link-1 <1>','link-2 <1>']: P[k]['col']=ORANGE
def place(seat, d, spin=0.0):
    d=np.asarray(d,float); d/=np.linalg.norm(d); z=-d
    a=np.array([1.,0,0]) if abs(z[0])<0.9 else np.array([0,1.,0])
    x=np.cross(a,z); x/=np.linalg.norm(x); y=np.cross(z,x)
    M=np.eye(4); M[:3,0]=x; M[:3,1]=y; M[:3,2]=z; M[:3,3]=seat; return M
F={}  # fastener key -> dict(mesh, M (rest pose, q=0), group, dir)
def addf(key, mesh, seat, d, group=None, col=None):
    F[key]=dict(mesh=mesh,M=place(seat,d),col=col or (BRASS if 'insert' in mesh else STEEL),group=group,dir=np.asarray(d,float)/np.linalg.norm(d))
# Fastener choice for the crank end of each link (link 5 mm + crank arm 5 mm, both Ø4.4 clearance).
LINK_CRANK_SCREW=('scr_M3x14', 14); LINK_CRANK_NUT='nylock_M3'
# rail -> rack: 2 per side
for x in (-75,-45,45,75): addf(f'rail_scr_{x}','scr_M2x6',[x,-57.0,0],[0,1,0])
# finger holders: heat-set inserts (+ the soldering iron that sets them), carriage screws
for s_,g in ((1,'L'),(-1,'R')):
    for x in (69.8,77.8):
        for z in (-6,6): addf(f'car_scr_{g}_{x}_{z}','scr_M2x5',[s_*x,-65.7,z],[0,1,0],g)
    addf(f'insert_{g}','insert_M3',[s_*74.6,-56.5,s_*-15.0],[0,-1,0],g)
    addf(f'iron_{g}','iron',[s_*74.6,-56.5,s_*-15.0],[0,-1,0],g,col=(0.2,0.2,0.22))
    for (x,y) in ((59.5,-73.8),(89.5,-74.3),(88.9,-109.3)):
        addf(f'fing_scr_{g}_{x}','scr_M3x25',[s_*x,y,16.0],[0,0,-1],g)
        addf(f'fing_nut_{g}_{x}','nut_M3',[s_*x,y,-8.3],[0,0,-1],g)
# gripper holder -> servo
for x in (-10.2,10.2):
    for z in (8.2,29.3): addf(f'hold_scr_{x}_{z}','scr_M2x6',[x,-38.0,z],[0,1,0])
addf('horn_scr','scr_M3x10',[0,-39.0,0],[0,1,0],'crank')
# rack -> gripper holder: 4 countersunk + nuts from the back
for (x,z) in ((-14.7,-14.7),(-14.7,14.7),(14.7,-14.7),(14.7,14.7)):
    addf(f'rack_scr_{x}_{z}','csk_M3x10',[x,-42.7,z],[0,1,0])
    addf(f'rack_nut_{x}_{z}','nut_M3',[x,-38.0,z],[0,1,0])
# crank -> horn: 4 countersunk M3x14 (crank frame, rotates with the crank)
for i,(x,z) in enumerate(((-5.7,4.0),(4.0,5.7),(5.7,-4.0),(-4.0,-5.7))): addf(f'crank_scr_{i}','csk_M3x14',[x,-48.6,z],[0,1,0],'crank')
# link joints
for side in ('L','R'):
    addf(f'linkA_scr_{side}',LINK_CRANK_SCREW[0],[0,-55.0,0],[0,1,0],'pinA'+side)
    if LINK_CRANK_NUT: addf(f'linkA_nut_{side}',LINK_CRANK_NUT,[0,-45.0,0],[0,1,0],'pinA'+side)
    addf(f'linkB_scr_{side}','scr_M3x10',[0,-50.0,0],[0,-1,0],'pinB'+side)
# arm adapter: M3 to the arm's wrist-roll horn, M2 to the gripper servo
for (x,z) in ((-7,0.2),(7,0.2),(0,-6.8),(0,7.2)): addf(f'arm_scr_{x}_{z}','scr_M3x10',[x,-0.8,z],[0,1,0])
for x in (-10.25,10.25):
    for z in (8.5,33.0): addf(f'adp_scr_{x}_{z}','scr_M2x6',[x,0.2,z],[0,-1,0])
addf('clevis_bolt','scr_M5x20',[-7.0,8.7,47.2],[1,0,0]); addf('clevis_nut','nut_M5',[7.0,8.7,47.2],[1,0,0])
for x in (-15.0,15.1):
    for z in (74.4,104.4): addf(f'cam_scr_{x}_{z}','scr_M2x8',[x,13.8,z],[0,1,0])

def world(q):
    """All part + fastener transforms for gripper state q (mm of closing)."""
    out,g=pose(P,q); g2,th,A,B=group_M(q)
    M={k:(out.get(k,p['M'])) for k,p in P.items()}
    for k,f in F.items():
        G=f['group']; T=f['M']
        if G in ('L','R','crank'): T=g[G]@T
        elif G and G.startswith('pinA'):
            a=A if G.endswith('L') else -A; T=trans([a[0],0,a[1]])@T
        elif G and G.startswith('pinB'):
            b=np.array([XH0-q,ZH]) if G.endswith('L') else -np.array([XH0-q,ZH]); T=trans([b[0],0,b[1]])@T
        M[k]=T
    return M
COL={k:p['col'] for k,p in P.items()}; COL.update({k:f['col'] for k,f in F.items()})
MESH={k:p['mesh'] for k,p in P.items()}; MESH.update({k:f['mesh'] for k,f in F.items()})
DIR={k:f['dir'] for k,f in F.items()}
def ease(t): t=min(max(t,0),1); return t*t*(3-2*t)
def lerp(a,b,t): return np.asarray(a)*(1-t)+np.asarray(b)*t
def sel(prefix): return [k for k in list(P)+list(F) if k.startswith(prefix)]

# Events are offset keyframes [(t, [dx,dy,dz]), ...] applied on top of the part's pose;
# a part appears at the first key (fading in) and, with 'hide', disappears after that time.
def ev(key, kf, hide=None): return dict(key=key, kf=[(float(t),list(map(float,o))) for t,o in kf], hide=hide)
def parts_in(keys, t0, t1, off): return [ev(k,[(t0,off),(t1,[0,0,0])]) for k in keys]
def fast_in(keys, t0, dt=0.5, stagger=0.12, dist=25, base=(0,0,0)):
    b=np.asarray(base,float)
    return [ev(k,[(t0+i*stagger,b-DIR[k]*dist),(t0+i*stagger+dt,b)]) for i,k in enumerate(keys)]

RAIL=['rail <1>','left_carriage <2>','right_carriage <1>']
RAILSCR=sel('rail_scr')
GRIP_BASE=['rack <1>']+RAIL+RAILSCR
HOLDERS=['finger_holder_left_n <1>','finger_holder_right_n <1>']+sel('insert_')
HOLDSCR=sel('car_scr')
FINGERS=['soft_gripper_finger <1>','soft_gripper_finger <2>','finger_pad <1>','finger_pad <2>']+sel('fing_')
SERVO_MOD=['Servo <1>','feetech_gripper_holder <1>','Servo Horn <1>','horn_scr']+sel('hold_scr')
RACKSCR=sel('rack_scr')+sel('rack_nut')
CRANK=['crank <1>']+sel('crank_scr')
LINKS=['link-1 <1>','link-2 <1>']+sel('linkA_')+sel('linkB_')
CAMMOUNT=['feetech_camera_mount_bottom <1>','camera holder v3 <1>','clevis_bolt','clevis_nut']
ADAPTER=['feetech_back_holder_to_horn <1>','horn spacer 3.5 mm <1>']+sel('arm_scr')+sel('adp_scr')
CAM=[k for k in P if k.startswith('Raspberry')]+sel('cam_scr')

STEPS=[]
def step(name,title,dur,base,events,cam0,cam1,q=0.0,qfn=None,camfn=None):
    STEPS.append(dict(name=name,title=title,dur=dur,base=base,events=events,cam0=cam0,cam1=cam1,q=q,qfn=qfn,camfn=camfn))
cam=lambda tgt,yaw,pitch,dist: dict(target=tgt,yaw=yaw,pitch=pitch,dist=dist,fov=30)
QPARK=50.0   # carriages pushed to the middle so the outer rail holes are free

# 1 carriages onto the rail
e=[ev('rail <1>',[(0.0,[0,0,30]),(0.6,[0,0,0])])]+parts_in(['left_carriage <2>'],0.8,2.3,[130,0,0])+parts_in(['right_carriage <1>'],0.8,2.3,[-130,0,0])
step('01_carriages','Slide the two carriages onto the rail',4.0,[],e,cam([0,-57,0],-62,30,300),cam([0,-57,0],-72,28,280),q=QPARK)
# 2 rail onto the rack
e=parts_in(['rack <1>'],0.0,0.6,[0,0,40])+parts_in(RAIL,0.8,1.9,[0,-70,0])+fast_in(RAILSCR,2.3,stagger=0.2)
step('02_rail','Fasten the rail to the rack (4× M2×6, two per side)',6.0,[],e,cam([0,-50,0],-64,32,340),cam([0,-50,0],-74,28,320),
     qfn=lambda t: QPARK*(1-ease((t-4.6)/1.1)))
# 3 heat-set inserts
e=parts_in(['finger_holder_left_n <1>','finger_holder_right_n <1>'],0.0,0.6,[0,0,30])
for i,g in enumerate(('L','R')):
    t0=0.9+i*1.9
    e+= [ev(f'insert_{g}',[(t0,[0,35,0]),(t0+0.5,[0,8,0]),(t0+1.2,[0,0,0])])]
    e+= [ev(f'iron_{g}',[(t0+0.3,[0,90,0]),(t0+0.6,[0,8,0]),(t0+1.2,[0,0,0]),(t0+1.5,[0,0,0]),(t0+1.9,[0,90,0])],hide=t0+1.9)]
step('03_inserts','Press the M3 heat-set inserts into the finger holders',5.0,[],e,cam([0,-80,0],-40,38,380),cam([0,-80,0],-52,40,370))
# 4 finger holders onto the carriages
e=parts_in(HOLDERS,0.2,1.4,[0,-60,0])+fast_in(HOLDSCR,1.8,stagger=0.08)
step('04_finger_holders','Bolt the finger holders to the carriages (8× M2×5)',4.5,GRIP_BASE,e,cam([0,-75,0],-58,36,400),cam([0,-75,0],-68,40,380))
# 5 fingers
e=parts_in(['soft_gripper_finger <1>','finger_pad <2>','soft_gripper_finger <2>','finger_pad <1>'],0.2,1.4,[0,-90,0])+fast_in(sel('fing_scr'),1.8,stagger=0.15,dist=40)+fast_in(sel('fing_nut'),4.0,stagger=0.15,dist=25)
step('05_fingers','Attach the TPU fingers (6× M3×25 + nuts)',6.5,GRIP_BASE+HOLDERS+HOLDSCR,e,cam([0,-110,0],-55,45,560),cam([78,-90,-8],-40,-35,240),
     camfn=lambda t: min(max((t-2.8)/1.2,0),1))
# 6 gripper holder onto the servo
e=parts_in(['Servo <1>'],0.0,0.6,[0,0,30])+parts_in(['feetech_gripper_holder <1>'],0.8,1.8,[0,-50,0])+fast_in(sel('hold_scr'),2.2,stagger=0.15)
step('06_servo_holder','Screw the gripper holder onto the servo (4× M2×6)',5.0,[],e,cam([0,-20,12],-55,22,240),cam([0,-20,12],-65,25,230))
# 7 horn
e=parts_in(['Servo Horn <1>'],0.6,1.6,[0,-40,0])+fast_in(['horn_scr'],2.0,dt=0.7)
step('07_horn','Centre the servo, then fit the horn and its centre screw',4.0,['Servo <1>','feetech_gripper_holder <1>']+sel('hold_scr'),e,cam([0,-20,12],-65,25,230),cam([0,-20,12],-58,22,220))
# 8 servo module onto the rack (countersunk from the front, nuts from the back)
e=parts_in(SERVO_MOD,0.2,1.8,[0,110,0])+fast_in(sel('rack_scr'),2.2,stagger=0.15,dist=30)+fast_in(sel('rack_nut'),3.9,stagger=0.15,dist=30)
step('08_servo_to_rack','Join the servo module to the rack (4× M3 countersunk + nuts)',6.0,GRIP_BASE+HOLDERS+HOLDSCR+FINGERS,e,
     cam([0,-40,0],-100,26,420),cam([0,-40,0],-215,32,250),camfn=lambda t: ease((t-2.6)/1.4))
# 9 crank, slid in from below, countersunk M3x14
e=[ev('crank <1>',[(0.2,[0,0,-110]),(1.6,[0,0,0])])]+fast_in(sel('crank_scr'),2.0,stagger=0.15,dist=30)
step('09_crank','Slide the crank in from below and bolt it to the horn (4× M3×14 countersunk)',5.0,GRIP_BASE+HOLDERS+HOLDSCR+FINGERS+SERVO_MOD+RACKSCR,e,
     cam([0,-50,-15],-75,-20,440),cam([0,-50,-15],-95,-6,420))
# 10 links
e=parts_in(['link-1 <1>','link-2 <1>'],0.2,1.4,[0,-50,0])+fast_in(sel('linkA_scr'),1.8,stagger=0.2,dist=30)+(fast_in(sel('linkA_nut'),2.6,stagger=0.2,dist=20) if LINK_CRANK_NUT else [])+fast_in(sel('linkB_scr'),3.3,stagger=0.2,dist=30)
step('10_links','Connect the links: crank side, then finger-holder side',5.5,GRIP_BASE+HOLDERS+HOLDSCR+FINGERS+SERVO_MOD+RACKSCR+CRANK,e,cam([0,-50,0],-88,12,400),cam([0,-50,0],-80,20,400))
# 11 camera mount
e=parts_in(['feetech_camera_mount_bottom <1>'],0.2,1.4,[0,0,60])+parts_in(['camera holder v3 <1>'],1.6,2.6,[0,0,60])+fast_in(['clevis_bolt'],2.9,dt=0.7,dist=35)+fast_in(['clevis_nut'],3.5,dt=0.5,dist=20)
BEFORE_CAM=GRIP_BASE+HOLDERS+HOLDSCR+FINGERS+SERVO_MOD+RACKSCR+CRANK+LINKS
step('11_camera_mount','Add the camera mount and hinge it with an M5 bolt',5.0,BEFORE_CAM,e,cam([0,10,45],40,18,420),cam([0,10,45],25,20,410))
# 12 arm adapter: first onto the arm's wrist-roll horn (pre-assembled away from the gripper), then onto the servo
AW=[0,150,0]
e =[ev('horn spacer 3.5 mm <1>',[(0.2,np.add(AW,[0,40,0])),(0.9,AW),(2.9,AW),(4.0,[0,0,0])])]
e+=[ev('feetech_back_holder_to_horn <1>',[(0.4,np.add(AW,[0,-40,0])),(1.1,AW),(2.9,AW),(4.0,[0,0,0])])]
for i,k in enumerate(sel('arm_scr')):
    t0=1.3+i*0.15; e.append(ev(k,[(t0,np.add(AW,-DIR[k]*25)),(t0+0.5,AW),(2.9,AW),(4.0,[0,0,0])]))
e+=fast_in(sel('adp_scr'),4.4,stagger=0.15)
step('12_arm_adapter',"Screw the arm adapter to the arm's wrist roll, then onto the gripper servo",6.5,BEFORE_CAM+CAMMOUNT,e,cam([0,40,12],55,22,470),cam([0,10,12],70,24,400))
# 13 camera
e=parts_in([k for k in P if k.startswith('Raspberry')],0.2,1.4,[0,-50,0])+fast_in(sel('cam_scr'),1.8,stagger=0.15)
step('13_camera','Screw the Raspberry Pi HQ Camera to the holder (4× M2×8)',4.5,BEFORE_CAM+CAMMOUNT+ADAPTER,e,cam([0,-15,45],-60,14,480),cam([0,-15,45],-70,18,470))
ALL=[k for k in list(P)+list(F) if not k.startswith('iron_')]
step('14_done','Done: the servo drives both fingers through the crank and links',8.0,ALL,[],cam([0,-50,10],-60,25,520),cam([0,-50,10],-150,25,520),qfn=lambda t: 40*0.5*(1-np.cos(2*np.pi*t/4.0)))

def kf_offset(kf,t):
    if t<=kf[0][0]: return np.asarray(kf[0][1])
    for (t0,o0),(t1,o1) in zip(kf,kf[1:]):
        if t<=t1: return lerp(o0,o1,ease((t-t0)/max(t1-t0,1e-6)))
    return np.asarray(kf[-1][1])
def frames(st):
    n=int(st['dur']*FPS); shots=[]
    for i in range(n):
        t=i/FPS; u=ease(i/(n-1)); uc=float(st['camfn'](t)) if st['camfn'] else u
        q=st['qfn'](t) if st['qfn'] else st['q']
        M=world(q); parts=[]
        for k in st['base']: parts.append(dict(mesh=MESH[k],M=[float(x) for x in M[k].ravel()],col=list(COL[k])))
        for e in st['events']:
            k=e['key']; t0=e['kf'][0][0]
            if t<t0 or (e['hide'] is not None and t>e['hide']): continue
            T=trans(kf_offset(e['kf'],t))@M[k]; fade=min(1.0,(t-t0)/0.25)
            parts.append(dict(mesh=MESH[k],M=[float(x) for x in T.ravel()],col=list(COL[k]),alpha=fade if fade<1 else 1))
        c0,c1=st['cam0'],st['cam1']
        c=dict(target=[float(x) for x in lerp(c0['target'],c1['target'],uc)],yaw=float(lerp(c0['yaw'],c1['yaw'],uc)),pitch=float(lerp(c0['pitch'],c1['pitch'],uc)),dist=float(lerp(c0['dist'],c1['dist'],uc)),fov=30)
        shots.append(dict(file=f'{i:04d}.png',cam=c,parts=parts,bg=[1,1,1]))
    return shots
if __name__=='__main__':
    only=sys.argv[1:]
    for st in STEPS:
        if only and st['name'] not in only: continue
        json.dump(frames(st),open(f'shots_{st["name"]}.json','w')); print(st['name'],int(st['dur']*FPS))
    json.dump([dict(name=s['name'],title=s['title'],dur=s['dur']) for s in STEPS],open('steps.json','w'),indent=1)
