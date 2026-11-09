// Curate the OSM extract into the Blender frame for the generators.
// Blender frame: origin = dome centre = axis-frame (0, DOME_Y); +Y toward the main gate; x right.
// 2017 building outlines (OSMuser111107, 2017-11-13) are shifted +BUILDING_DX in x: their axis
// sits ~3 m west of the 2021 road centrelines and the gate axis (documented in SOURCE_EVIDENCE.md).
// usage: node export_osm_campus.js osm_axis_frame.json out.json
const fs=require('fs');const j=JSON.parse(fs.readFileSync(process.argv[2]));
const DOME_Y=246.1, BUILDING_DX=3.0;
const B=([x,y])=>[+x.toFixed(2),+(y-DOME_Y).toFixed(2)];
const W=id=>j.ways.find(w=>w.id===id);
const plot=W(540106539).pts.map(B);
function inside(p,poly){let c=false;for(let i=0,k=poly.length-1;i<poly.length;k=i++){const[a,b]=poly[i],[c2,d]=poly[k];if((b>p[1])!==(d>p[1])&&p[0]<(c2-a)*(p[1]-b)/(d-b)+a)c=!c}return c}
const RING=[912696913,685373371], APPROACH=[685373372,912696914];
const out={attribution:"Road and building geometry (c) OpenStreetMap contributors, ODbL 1.0 (https://www.openstreetmap.org/copyright). Extract 2026-11-06 via Overpass API.",
 frame:{...j.frame,dome_axis_y:DOME_Y,building_dx:BUILDING_DX,note:"Blender = (x_axis, y_axis - dome_axis_y). See tools/geo/*.js"},
 plot_boundary:plot,campus_roads:[],campus_footways:[],external_roads:[],slip_roads:[],drop_off_loop:null,buildings:{},gates:[]};
for(const id of APPROACH){const w=W(id);out.slip_roads.push({id,tags:w.tags,pts:w.pts.map(B)})}
out.drop_off_loop={id:912696912,pts:W(912696912).pts.map(B)};
const EXTERNAL=[540096421,29079248,98608684,675124066,675124067,684389287,684401327,762771316,1208487327,914331578,76564574,540096391,914331577,93732799,540106511,540106512,98608682,98608683];
for(const id of EXTERNAL){const w=W(id);if(w)out.external_roads.push({id,tags:w.tags,pts:w.pts.map(B)})}
const skip=new Set([...RING,...APPROACH,912696912,912696891,912696893,...EXTERNAL]);
for(const w of j.ways){const t=w.tags;if(!t.highway||skip.has(w.id))continue;const pts=w.pts.map(B);
 const fr=pts.filter(p=>inside(p,plot)).length/pts.length;if(fr<0.8)continue;
 (t.highway==='footway'||t.highway==='pedestrian'?out.campus_footways:out.campus_roads).push({id:w.id,tags:t,pts})}
const shiftB=p=>[+(p[0]+BUILDING_DX).toFixed(2),+(p[1]-DOME_Y).toFixed(2)];
const BLD={"admin_2017":540106548,"academic_2017":540106547,"helmy_2017":540106545,"east_institute_2017":540106546,"east_pair_a":540106540,"east_pair_b":540106541};
for(const[k,id]of Object.entries(BLD)){const w=W(id);out.buildings[k]={id,tags:w.tags,pts:w.pts.map(shiftB)}}
for(const n of j.nodes)if(n.tags.barrier){const p=B(n.p);if(inside(p,plot)||Math.hypot(...p)<700)out.gates.push({id:n.id,tags:n.tags,p})}
fs.writeFileSync(process.argv[3],JSON.stringify(out));
console.log('plot',plot.length,'campus roads',out.campus_roads.length,'footways',out.campus_footways.length,'external',out.external_roads.length,'gates',out.gates.length);
