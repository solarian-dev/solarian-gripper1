import json, re, numpy as np
import os
HERE = os.path.dirname(os.path.abspath(__file__))
CAD = os.environ.get('GRIPPER_CAD', os.path.join(HERE, 'cad'))
A = json.load(open(os.path.join(CAD, 'assembly_gripper1_v5.json')))
inst = {}
for i in A['rootAssembly']['instances'] + [x for s in A.get('subAssemblies',[]) for x in s['instances']]:
    inst[i['id']] = i
def mesh_name(n): return re.sub(r'[^A-Za-z0-9_.-]+','_', re.sub(r' <\d+>$','',n))
COL = {
 'Servo':(0.13,0.13,0.15),'rail':(0.72,0.74,0.78),'left_carriage':(0.62,0.64,0.68),'right_carriage':(0.62,0.64,0.68),
 'soft_gripper_finger':(0.85,0.2,0.15),'finger_pad':(0.1,0.1,0.1),
 'Raspberry_Pi_HQ_Camera_-_board':(0.1,0.45,0.2),'Raspberry_Pi_HQ_Camera_-_lens_holder':(0.15,0.15,0.15),'Raspberry_Pi_HQ_Camera_-_sensor':(0.3,0.3,0.5),
 'screw_cap':(0.25,0.25,0.27),
}
PLA = (0.93,0.93,0.92); PLA2=(0.98,0.62,0.18)
def parts():
    out = {}
    for o in A['rootAssembly']['occurrences']:
        last = inst[o['path'][-1]]
        if last['type'] != 'Part': continue
        T = np.array(o['transform']).reshape(4,4); T[:3,3] *= 1000
        key = ' / '.join(inst[p]['name'] for p in o['path'])
        m = mesh_name(last['name'])
        if m == 'screw_cap': continue  # visual-only placeholder in the CAD, not a real part
        out[key] = dict(mesh=m, M=T, col=COL.get(m, PLA))
    return out
def tolist(p, **kw):
    d = dict(mesh=p['mesh'], M=[float(x) for x in np.asarray(p['M']).ravel()], col=list(p['col']))
    d.update(kw); return d

import os
A2 = json.load(open(os.path.join(CAD, 'assembly_feetech_raspberry_slim.json')))
inst2 = {i['id']:i for i in A2['rootAssembly']['instances'] + [x for s in A2.get('subAssemblies',[]) for x in s['instances']]}
def occ2(name):
    for o in A2['rootAssembly']['occurrences']:
        if inst2[o['path'][-1]]['name']==name:
            T=np.array(o['transform']).reshape(4,4); T[:3,3]*=1000; return T
def full_parts():
    P = parts()
    rack_v5 = P['rack <1>']['M']; R = rack_v5 @ np.linalg.inv(occ2('rack <1>'))
    for nm, mesh, rel in [('crank <1>','crank',True),('link-1 <1>','link-1',True),('link-2 <1>','link-2',True),('Servo Horn <1>','Servo_Horn',False)]:
        T = occ2(nm); T = R@T if rel else T
        P[nm] = dict(mesh=mesh, M=T, col=(0.13,0.13,0.15) if mesh=='Servo_Horn' else PLA)
    return P
