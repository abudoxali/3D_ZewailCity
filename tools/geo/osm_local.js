// Project OSM geometry to a local ENU metre frame and report key campus features.
const fs=require('fs');
const g=JSON.parse(fs.readFileSync(process.argv[2]));
const REF={lat:29.9410,lon:31.0670};
const mlat=111132.92-559.82*Math.cos(2*REF.lat*Math.PI/180),mlon=111412.84*Math.cos(REF.lat*Math.PI/180);
const E=(p)=>[(p.lon-REF.lon)*mlon,(p.lat-REF.lat)*mlat];
const ways={};for(const e of g.elements)if(e.type==='way')ways[e.id]=e;
function cen(id){const pts=ways[id].geometry.map(E);let a=0,cx=0,cy=0;for(let i=0;i<pts.length-1;i++){const[x0,y0]=pts[i],[x1,y1]=pts[i+1];const c=x0*y1-x1*y0;a+=c;cx+=(x0+x1)*c;cy+=(y0+y1)*c}a/=2;return{c:[cx/(6*a),cy/(6*a)],area:Math.abs(a)}}
for(const id of [540106548,540106547,540106545,540106546,540106540,540106541]){const r=cen(id);console.log(id,ways[id].tags.building,'centroid',r.c.map(v=>v.toFixed(1)).join(','),'area',r.area.toFixed(0))}
// circle fit (Kasa) on service ways forming the ring: collect points 250-350 m from a guess
const guess=cen(540106547).c;let P=[];
for(const e of Object.values(ways)){const t=e.tags||{};if(!t.highway||!e.geometry)continue;for(const p of e.geometry){const q=E(p);const r=Math.hypot(q[0]-guess[0],q[1]-guess[1]);if(r>230&&r<330)P.push(q)}}
function kasa(P){let sx=0,sy=0,sxx=0,syy=0,sxy=0,sxz=0,syz=0,sz=0,n=P.length;for(const[x,y]of P){const z=x*x+y*y;sx+=x;sy+=y;sxx+=x*x;syy+=y*y;sxy+=x*y;sxz+=x*z;syz+=y*z;sz+=z}
 // solve [sxx sxy sx;sxy syy sy;sx sy n][a b c]=[sxz syz sz]
 const A=[[sxx,sxy,sx,sxz],[sxy,syy,sy,syz],[sx,sy,n,sz]];for(let i=0;i<3;i++){for(let j=i+1;j<3;j++){const f=A[j][i]/A[i][i];for(let k=i;k<4;k++)A[j][k]-=f*A[i][k]}}
 const s=[0,0,0];for(let i=2;i>=0;i--){let v=A[i][3];for(let k=i+1;k<3;k++)v-=A[i][k]*s[k];s[i]=v/A[i][i]}
 const cx=s[0]/2,cy=s[1]/2,r=Math.sqrt(s[2]+cx*cx+cy*cy);return[cx,cy,r]}
let [cx,cy,r]=kasa(P);
for(let it=0;it<4;it++){P=P.filter(([x,y])=>Math.abs(Math.hypot(x-cx,y-cy)-r)<12);[cx,cy,r]=kasa(P)}
const res=P.map(([x,y])=>Math.hypot(x-cx,y-cy)-r);const rms=Math.sqrt(res.reduce((a,b)=>a+b*b,0)/res.length);
console.log('ring fit centre',cx.toFixed(1),cy.toFixed(1),'r',r.toFixed(1),'n',P.length,'rms',rms.toFixed(2));
for(const e of g.elements){if(e.type==='node'&&e.tags&&e.tags.barrier){const q=E(e);if(Math.abs(q[0])<700&&Math.abs(q[1])<700)console.log('barrier',e.id,JSON.stringify(e.tags),q.map(v=>v.toFixed(1)).join(','),'dist_from_ring_c',Math.hypot(q[0]-cx,q[1]-cy).toFixed(0))}}
fs.writeFileSync(process.argv[3]||'/dev/null',JSON.stringify({REF,mlat,mlon,ring:[cx,cy,r,rms]}));
