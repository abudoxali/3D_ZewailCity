// Convert OSM ways to the campus axis frame (metres).
// Frame: origin = fitted ring-road centre; +Y = unit vector from ring centre to the
// midpoint of the two main-gate nodes (5225739523, 5225739528); +X = +Y rotated -90 deg.
// usage: node osm_to_axis.js osm.json out.json
const fs=require('fs');const g=JSON.parse(fs.readFileSync(process.argv[2]));
const REF={lat:29.9410,lon:31.0670};
const mlat=111132.92-559.82*Math.cos(2*REF.lat*Math.PI/180),mlon=111412.84*Math.cos(REF.lat*Math.PI/180);
const E=p=>[(p.lon-REF.lon)*mlon,(p.lat-REF.lat)*mlat];
const C=[2.9,6.1];const nodes={};for(const e of g.elements)if(e.type==='node')nodes[e.id]=e;
const G1=E(nodes[5225739523]),G2=E(nodes[5225739528]);const G=[(G1[0]+G2[0])/2,(G1[1]+G2[1])/2];
let uy=[G[0]-C[0],G[1]-C[1]];const L=Math.hypot(...uy);uy=[uy[0]/L,uy[1]/L];const ux=[uy[1],-uy[0]];
const T=p=>{const q=E(p);const d=[q[0]-C[0],q[1]-C[1]];return[+(d[0]*ux[0]+d[1]*ux[1]).toFixed(2),+(d[0]*uy[0]+d[1]*uy[1]).toFixed(2)]};
const out={frame:{REF,ring_centre_enu:C,gate_mid_enu:G,axis_bearing_deg:+(Math.atan2(uy[0],uy[1])*180/Math.PI).toFixed(2),gate_dist:+L.toFixed(1),
 note:'x right, y toward main gate, origin ring-road centre; OSM data (c) OpenStreetMap contributors, ODbL'},ways:[],nodes:[]};
for(const e of g.elements){if(e.type==='way'&&e.geometry){const t=e.tags||{};const pts=e.geometry.filter(Boolean).map(T);
  if(pts.every(([x,y])=>Math.abs(x)>900||Math.abs(y)>900))continue;out.ways.push({id:e.id,tags:t,pts})}
 if(e.type==='node'&&e.tags){const q=T(e);if(Math.abs(q[0])<900&&Math.abs(q[1])<900)out.nodes.push({id:e.id,tags:e.tags,p:q})}}
fs.writeFileSync(process.argv[3],JSON.stringify(out));console.log('axis bearing',out.frame.axis_bearing_deg,'gate dist',out.frame.gate_dist,'ways',out.ways.length,'nodes',out.nodes.length);
const bw=id=>out.ways.find(w=>w.id===id);
for(const id of [540106548,540106547,540106545,540106546,540106540,540106541]){const w=bw(id);const xs=w.pts.map(p=>p[0]),ys=w.pts.map(p=>p[1]);console.log(id,w.tags.building,'x',Math.min(...xs).toFixed(0),Math.max(...xs).toFixed(0),'y',Math.min(...ys).toFixed(0),Math.max(...ys).toFixed(0),JSON.stringify(w.pts))}
