import numpy as np
from scene import full_parts
def rot_xz(a, cx=0.0, cz=0.0):
    c,s=np.cos(a),np.sin(a); M=np.eye(4); M[0,0]=c;M[0,2]=-s;M[2,0]=s;M[2,2]=c
    T=np.eye(4);T[0,3]=cx;T[2,3]=cz; Ti=np.eye(4);Ti[0,3]=-cx;Ti[2,3]=-cz
    return T@M@Ti
def trans(v): T=np.eye(4); T[:3,3]=v; return T
A0=np.array([26.6,-18.6]); B0=np.array([71.5,-15.2]); XH0=74.6; ZH=-15.0
L=np.hypot(*(np.array([XH0-3.03,ZH])-A0))
def ang(v): return np.arctan2(v[1],v[0])
def rot2(a): return np.array([[np.cos(a),-np.sin(a)],[np.sin(a),np.cos(a)]])
def theta_of(q, prev=0.0):
    B=np.array([XH0-q,ZH]); best=None
    for t in np.linspace(prev-0.6,prev+0.6,2401):
        A=rot2(t)@A0; e=abs(np.linalg.norm(B-A)-L)
        if best is None or e<best[0]: best=(e,t)
    return best[1]
_tab=None
def table():
    global _tab
    if _tab is None:
        qs=np.linspace(3.03,-1,40).tolist()+np.linspace(0,56,300).tolist()
        th={}; prev=0.0
        # go from slim pose (q=3.03, theta=0) down to 0, then up to 56
        for q in np.linspace(3.03,0,30): prev=theta_of(q,prev)
        t0=prev; res=[]
        for q in np.linspace(0,56,561): prev=theta_of(q,prev); res.append((q,prev))
        _tab=np.array(res)
    return _tab
def theta(q):
    t=table(); return float(np.interp(q,t[:,0],t[:,1]))
def link_M(T0, A0_, B0_, A, B):
    phi=ang(B-A)-ang(B0_-A0_)
    # in xz: p' = R(phi)(p-A0)+A ; rot_xz(phi) applies (x,z)->(c x - s z, s x + c z) == rot2(phi)
    return trans([A[0],0,A[1]])@rot_xz(phi)@trans([-A0_[0],0,-A0_[1]])@T0
LEFT=['finger_holder_left_n <1>','left_carriage <2>','soft_gripper_finger <1>','finger_pad <2>']
RIGHT=['finger_holder_right_n <1>','right_carriage <1>','soft_gripper_finger <2>','finger_pad <1>']
HORN_ALIGN=None
def group_M(q):
    """Returns transforms (to left-multiply the rest pose) per motion group, plus link absolute poses."""
    th=theta(q)
    g={'L':trans([-q,0,0]),'R':trans([q,0,0]),'crank':rot_xz(th)}
    A=rot2(th)@A0; B=np.array([XH0-q,ZH])
    return g, th, A, B
def pose(P, q):
    g,th,A,B=group_M(q); out={}
    for k in LEFT: out[k]=g['L']@P[k]['M']
    for k in RIGHT: out[k]=g['R']@P[k]['M']
    out['crank <1>']=g['crank']@P['crank <1>']['M']
    out['Servo Horn <1>']=g['crank']@P['Servo Horn <1>']['M']
    out['link-1 <1>']=link_M(P['link-1 <1>']['M'],A0,np.array([71.5,-15.2]),A,B)
    out['link-2 <1>']=link_M(P['link-2 <1>']['M'],-A0,np.array([-71.5,14.8]),-A,-B)
    return out,g
if __name__=='__main__':
    for q in [0,3.03,10,20,30,40,50,54.5]: print(q, round(np.degrees(theta(q)),1))
