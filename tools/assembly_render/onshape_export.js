// Export the CAD data the render pipeline needs, straight from the Onshape web app.
//
// Usage: open the solarian-gripper1 Onshape document while signed in, open the
// browser devtools console, paste this file and run:
//
//   await exportGripper()
//
// It downloads solarian-gripper1-onshape-export.zip containing:
//   assembly_gripper1_v5.json                 assembly definition (occurrence transforms, mates)
//   assembly_feetech_raspberry_slim.json      assembly with the crank / link drive linkage
//   meshes/<part>.stl                         fine tessellation of every part, in part-studio coordinates
//   solarian-gripper1.step                    STEP of the gripper1_v5 assembly
// Unzip it into tools/assembly_render/cad/ and run ./build.sh.

const CFG = {
  doc: '517a50d1e5582bf4d5f0bfdf',
  ws: '7dbed727fa7bd55c2f836191',
  v5: '52a2f1f168a9575e23acf47c',            // gripper1_v5 (what the URDF/MJCF is exported from)
  slim: '977b7f4db11c0ab84e468115',          // Assembly Feetech - Raspberry Slim (has crank + links + horn)
  linkageParts: ['crank', 'link-1', 'link-2', 'Servo Horn'],
  purchased: ['Servo', 'rail', 'left_carriage', 'right_carriage', 'Servo Horn'],
};

const xsrf = () => decodeURIComponent((document.cookie.split(';').map(c => c.trim())
  .find(c => c.startsWith('XSRF-TOKEN=')) || '').split('=').slice(1).join('='));
const getJSON = async (u) => (await fetch(u, { headers: { Accept: 'application/json' } })).json();
const postJSON = async (u, body) => (await fetch(u, {
  method: 'POST', body: JSON.stringify(body),
  headers: { 'Content-Type': 'application/json', Accept: 'application/json', 'X-XSRF-TOKEN': xsrf() },
})).json();
const cleanName = (n) => n.replace(/ <\d+>$/, '').replace(/[^A-Za-z0-9_.-]+/g, '_');

function partBase(i) {
  const wvm = i.documentId === CFG.doc ? `w/${CFG.ws}`
    : (i.documentVersion ? `v/${i.documentVersion}` : `m/${i.documentMicroversion}`);
  return `/api/partstudios/d/${i.documentId}/${wvm}/e/${i.elementId}`;
}

// Tessellate one part via the tessellatedfaces endpoint (same origin, tolerance control) -> binary STL in mm.
async function tessellate(i, angle, chord) {
  const q = `partId=${encodeURIComponent(i.partId)}&angleTolerance=${angle}&chordTolerance=${chord}` +
    `&outputFacetNormals=true&outputVertexNormals=false&configuration=${encodeURIComponent(i.fullConfiguration || 'default')}`;
  const bodies = await getJSON(`${partBase(i)}/tessellatedfaces?${q}`);
  const tris = bodies.flatMap(b => (b.faces || []).flatMap(f => f.facets || []));
  const buf = new ArrayBuffer(84 + 50 * tris.length), dv = new DataView(buf);
  dv.setUint32(80, tris.length, true);
  let o = 84;
  for (const t of tris) {
    for (let k = 0; k < 3; k++) dv.setFloat32(o + 4 * k, (t.normal || [0, 0, 0])[k], true); o += 12;
    for (const v of t.vertices) { for (let k = 0; k < 3; k++) dv.setFloat32(o + 4 * k, v[k] * 1000, true); o += 12; }
    o += 2;
  }
  return new Uint8Array(buf);
}

async function translate(url, body) {
  let st = await postJSON(url, body);
  while (st.requestState === 'ACTIVE') { await new Promise(r => setTimeout(r, 1000)); st = await getJSON(`/api/translations/${st.id}`); }
  if (st.requestState !== 'DONE') throw new Error(st.failureReason);
  return new Uint8Array(await (await fetch(`/api/documents/d/${st.resultDocumentId}/externaldata/${st.resultExternalDataIds[0]}`)).arrayBuffer());
}

function zip(files) { // store-only zip
  const T = new Uint32Array(256).map((_, n) => { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1; return c >>> 0; });
  const crc = (u) => { let c = 0xFFFFFFFF; for (const b of u) c = T[(c ^ b) & 0xFF] ^ (c >>> 8); return (c ^ 0xFFFFFFFF) >>> 0; };
  const enc = new TextEncoder(), parts = [], central = []; let off = 0;
  for (const [name, data] of files) {
    const nb = enc.encode(name), c = crc(data);
    const lh = new DataView(new ArrayBuffer(30));
    lh.setUint32(0, 0x04034b50, true); lh.setUint16(4, 20, true); lh.setUint32(14, c, true);
    lh.setUint32(18, data.length, true); lh.setUint32(22, data.length, true); lh.setUint16(26, nb.length, true);
    parts.push(new Uint8Array(lh.buffer), nb, data);
    const ch = new DataView(new ArrayBuffer(46));
    ch.setUint32(0, 0x02014b50, true); ch.setUint16(4, 20, true); ch.setUint16(6, 20, true); ch.setUint32(16, c, true);
    ch.setUint32(20, data.length, true); ch.setUint32(24, data.length, true); ch.setUint16(28, nb.length, true); ch.setUint32(42, off, true);
    central.push(new Uint8Array(ch.buffer), nb);
    off += 30 + nb.length + data.length;
  }
  const size = central.reduce((s, x) => s + x.length, 0), end = new DataView(new ArrayBuffer(22));
  end.setUint32(0, 0x06054b50, true); end.setUint16(8, files.length, true); end.setUint16(10, files.length, true);
  end.setUint32(12, size, true); end.setUint32(16, off, true);
  return new Blob([...parts, ...central, new Uint8Array(end.buffer)], { type: 'application/zip' });
}

async function exportGripper() {
  const enc = new TextEncoder(), files = [];
  const asmUrl = (e) => `/api/assemblies/d/${CFG.doc}/w/${CFG.ws}/e/${e}?includeMateFeatures=true`;
  const v5 = await getJSON(asmUrl(CFG.v5)), slim = await getJSON(asmUrl(CFG.slim));
  files.push(['assembly_gripper1_v5.json', enc.encode(JSON.stringify(v5))]);
  files.push(['assembly_feetech_raspberry_slim.json', enc.encode(JSON.stringify(slim))]);
  const inst = (a) => [...a.rootAssembly.instances, ...(a.subAssemblies || []).flatMap(s => s.instances)].filter(i => i.type === 'Part');
  const parts = new Map();
  for (const i of inst(v5)) parts.set(cleanName(i.name), i);
  for (const i of inst(slim)) if (CFG.linkageParts.includes(i.name.replace(/ <\d+>$/, ''))) parts.set(cleanName(i.name), i);
  for (const [name, i] of parts) {
    const coarse = CFG.purchased.includes(i.name.replace(/ <\d+>$/, '')) || name.startsWith('Raspberry');
    files.push([`meshes/${name}.stl`, await tessellate(i, coarse ? 0.15 : 0.05, coarse ? 0.00005 : 0.00001)]);
    console.log('tessellated', name);
  }
  files.push(['solarian-gripper1.step', await translate(`/api/assemblies/d/${CFG.doc}/w/${CFG.ws}/e/${CFG.v5}/translations`,
    { formatName: 'STEP', storeInDocument: false, destinationName: 'solarian-gripper1' })]);
  const a = document.createElement('a');
  a.href = URL.createObjectURL(zip(files)); a.download = 'solarian-gripper1-onshape-export.zip';
  a.textContent = 'Download solarian-gripper1-onshape-export.zip';
  Object.assign(a.style, { position: 'fixed', top: '80px', left: '50%', zIndex: 999999, background: '#d9480f', color: '#fff', padding: '12px 18px', borderRadius: '8px' });
  document.body.appendChild(a); a.click();
  return files.map(([n, d]) => `${n} ${d.length}`);
}
