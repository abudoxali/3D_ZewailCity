// Resample a Sentinel-2 crop (PPM + meta) into the campus axis frame, optionally overlaying OSM.
// usage: node s2_to_axis.js s2.ppm s2_meta.json osm_axis.json out.ppm xmin xmax ymin ymax px_per_m dy overlay(0/1)
const fs=require('fs');const a=process.argv;const ppm=fs.readFileSync(a[2]);const meta=JSON.parse(fs.readFileSync(a[3]));const osm=JSON.parse(fs.readFileSync(a[4]));
const [xmin,xmax,ymin,ymax,s,dy,ov]=a.slice(6).map(Number);
const hdr=ppm.toString('ascii',0,30).split(/\s+/);const SW=+hdr[1],SH=+hdr[2];const off=ppm.indexOf(10)+1;
const REF=osm.frame.REF,mlat=111132.92-559.82*Math.cos(2*REF.lat*Math.PI/180),mlon=111412.84*Math.cos(REF.lat*Math.PI/180);
const C=osm.frame.ring_centre_enu,G=osm.frame.gate_mid_enu;let uy=[G[0]-C[0],G[1]-C[1]];const L=Math.hypot(...uy);uy=[uy[0]/L,uy[1]/L];const ux=[uy[1],-uy[0]];
function utm(lat,lon,zone){const a=6378137,f=1/298.257223563,k0=0.9996,e2=f*(2-f),ep2=e2/(1-e2);const l0=((zone-1)*6-180+3)*Math.PI/180;
 const p=lat*Math.PI/180,l=lon*Math.PI/180;const N=a/Math.sqrt(1-e2*Math.sin(p)**2),T=Math.tan(p)**2,Cc=ep2*Math.cos(p)**2,A=Math.cos(p)*(l-l0);
 const M=a*((1-e2/4-3*e2*e2/64-5*e2**3/256)*p-(3*e2/8+3*e2*e2/32+45*e2**3/1024)*Math.sin(2*p)+(15*e2*e2/256+45*e2**3/1024)*Math.sin(4*p)-(35*e2**3/3072)*Math.sin(6*p));
 return[k0*N*(A+(1-T+Cc)*A**3/6+(5-18*T+T*T+72*Cc-58*ep2)*A**5/120)+500000,k0*(M+N*Math.tan(p)*(A*A/2+(5-T+9*Cc+4*Cc*Cc)*A**4/24+(61-58*T+T*T+600*Cc-330*ep2)*A**6/720))]}
const W=Math.round((xmax-xmin)*s),H=Math.round((ymax-ymin)*s);const out=Buffer.alloc(W*H*3);
function samp(fx,fy,ch){fx-=0.5;fy-=0.5;const x0=Math.floor(fx),y0=Math.floor(fy),tx=fx-x0,ty=fy-y0;const g=(x,y)=>{x=Math.min(SW-1,Math.max(0,x));y=Math.min(SH-1,Math.max(0,y));return ppm[off+(y*SW+x)*3+ch]};
 return (g(x0,y0)*(1-tx)+g(x0+1,y0)*tx)*(1-ty)+(g(x0,y0+1)*(1-tx)+g(x0+1,y0+1)*tx)*ty}
for(let r=0;r<H;r++)for(let c=0;c<W;c++){const x=xmin+(c+0.5)/s,y=ymax-(r+0.5)/s-dy;const e=C[0]+x*ux[0]+y*uy[0],n=C[1]+x*ux[1]+y*uy[1];
 const [U,V]=utm(REF.lat+n/mlat,REF.lon+e/mlon,36);const fx=(U-meta.origin_utm[0])/meta.pixel_m,fy=(meta.origin_utm[1]-V)/meta.pixel_m;const o=(r*W+c)*3;for(let ch=0;ch<3;ch++)out[o+ch]=Math.min(255,samp(fx,fy,ch)*1.0)}
if(ov){const X=x=>(x-xmin)*s,Y=y=>(ymax-(y+dy))*s;function px(x,y,cl){x|=0;y|=0;if(x<0||y<0||x>=W||y>=H)return;const i=(y*W+x)*3;out[i]=cl[0];out[i+1]=cl[1];out[i+2]=cl[2]}
 const line=(x0,y0,x1,y1,cl)=>{const n=Math.ceil(Math.hypot(x1-x0,y1-y0))+1;for(let i=0;i<=n;i++)px(x0+(x1-x0)*i/n,y0+(y1-y0)*i/n,cl)};
 for(const w of osm.ways){const t=w.tags;const cl=t.building?[255,0,0]:t.highway==='service'?[0,90,255]:t.highway==='footway'?[0,160,0]:t.highway?[40,40,40]:null;if(!cl)continue;for(let i=1;i<w.pts.length;i++)line(X(w.pts[i-1][0]),Y(w.pts[i-1][1]),X(w.pts[i][0]),Y(w.pts[i][1]),cl)}}
fs.writeFileSync(a[5],Buffer.concat([Buffer.from(`P6 ${W} ${H} 255\n`),out]));console.log(W,H);
