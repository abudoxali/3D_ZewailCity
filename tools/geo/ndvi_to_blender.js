// NDVI = (B08 - B04) / (B08 + B04) from Sentinel-2 L2A, resampled (bilinear in UTM) onto a
// regular grid in the Blender frame (origin = dome, +Y toward the main gate).
// usage: node ndvi_to_blender.js B04.u16 B08.u16 meta.json osm_axis.json dome_ring_y out.json preview.ppm
const fs=require('fs');const a=process.argv;
const rd=f=>{const b=fs.readFileSync(f);const o=b.indexOf(10)+1;const n=(b.length-o)/2;const v=new Float32Array(n);for(let i=0;i<n;i++)v[i]=b.readUInt16LE(o+2*i);return v};
const red=rd(a[2]),nir=rd(a[3]);const meta=JSON.parse(fs.readFileSync(a[4]));const osm=JSON.parse(fs.readFileSync(a[5]));const DY=+a[6];
const [SW,SH]=meta.size;const ndvi=new Float32Array(SW*SH);for(let i=0;i<SW*SH;i++)ndvi[i]=(nir[i]-red[i])/Math.max(1,nir[i]+red[i]);
const REF=osm.frame.REF,mlat=111132.92-559.82*Math.cos(2*REF.lat*Math.PI/180),mlon=111412.84*Math.cos(REF.lat*Math.PI/180);
const C=osm.frame.ring_centre_enu,G=osm.frame.gate_mid_enu;let uy=[G[0]-C[0],G[1]-C[1]];const L=Math.hypot(...uy);uy=[uy[0]/L,uy[1]/L];const ux=[uy[1],-uy[0]];
function utm(lat,lon,zone){const a=6378137,f=1/298.257223563,k0=0.9996,e2=f*(2-f),ep2=e2/(1-e2);const l0=((zone-1)*6-180+3)*Math.PI/180;
 const p=lat*Math.PI/180,l=lon*Math.PI/180;const N=a/Math.sqrt(1-e2*Math.sin(p)**2),T=Math.tan(p)**2,Cc=ep2*Math.cos(p)**2,A=Math.cos(p)*(l-l0);
 const M=a*((1-e2/4-3*e2*e2/64-5*e2**3/256)*p-(3*e2/8+3*e2*e2/32+45*e2**3/1024)*Math.sin(2*p)+(15*e2*e2/256+45*e2**3/1024)*Math.sin(4*p)-(35*e2**3/3072)*Math.sin(6*p));
 return[k0*N*(A+(1-T+Cc)*A**3/6+(5-18*T+T*T+72*Cc-58*ep2)*A**5/120)+500000,k0*(M+N*Math.tan(p)*(A*A/2+(5-T+9*Cc+4*Cc*Cc)*A**4/24+(61-58*T+T*T+600*Cc-330*ep2)*A**6/720))]}
const step=4,x0=-560,x1=560,y0=-720,y1=460;const NX=(x1-x0)/step+1,NY=(y1-y0)/step+1;const q=[];
const img=Buffer.alloc(NX*NY*3);
for(let j=0;j<NY;j++)for(let i=0;i<NX;i++){const xb=x0+i*step,yb=y0+j*step;const yr=yb+DY;
 const e=C[0]+xb*ux[0]+yr*uy[0],n=C[1]+xb*ux[1]+yr*uy[1];const [U,V]=utm(REF.lat+n/mlat,REF.lon+e/mlon,36);
 let fx=(U-meta.origin_utm[0])/meta.pixel_m-0.5,fy=(meta.origin_utm[1]-V)/meta.pixel_m-0.5;const ix=Math.floor(fx),iy=Math.floor(fy),tx=fx-ix,ty=fy-iy;
 const g=(x,y)=>ndvi[Math.min(SH-1,Math.max(0,y))*SW+Math.min(SW-1,Math.max(0,x))];
 const v=(g(ix,iy)*(1-tx)+g(ix+1,iy)*tx)*(1-ty)+(g(ix,iy+1)*(1-tx)+g(ix+1,iy+1)*tx)*ty;q.push(Math.round(v*1000));
 const o=((NY-1-j)*NX+i)*3;const c=Math.max(0,Math.min(1,(v-0.05)/0.45));img[o]=200*(1-c)+20;img[o+1]=180*(1-c)+60+120*c;img[o+2]=150*(1-c)+20}
fs.writeFileSync(a[7],JSON.stringify({source:"Copernicus Sentinel-2 L2A S2A_36RUU_20260916 (B04, B08), contains modified Copernicus Sentinel data 2026",
 note:"NDVI x1000 on a regular grid in the Blender frame (origin = dome centre, +Y toward the main gate). Row-major, j (y) outer, i (x) inner. Resampled bilinearly from 10 m pixels: features narrower than ~20 m are smeared.",
 x0,y0,step,nx:NX,ny:NY,ndvi_x1000:q}));
fs.writeFileSync(a[8],Buffer.concat([Buffer.from(`P6 ${NX} ${NY} 255\n`),img]));
const st=[...q].sort((a,b)=>a-b);console.log('grid',NX,NY,'ndvi p10',st[Math.floor(st.length*.1)],'p50',st[Math.floor(st.length*.5)],'p90',st[Math.floor(st.length*.9)],'p99',st[Math.floor(st.length*.99)]);
