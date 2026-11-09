// Minimal COG crop for a single-band uint16 Sentinel-2 band (tiled, deflate). Output: raw uint16 LE.
// usage: node s2_crop.js <TCI url> <lat> <lon> <half_size_m> <out.ppm> <out_meta.json>
const zlib=require('zlib'),fs=require('fs');
const [,,url,lat_,lon_,half_,outp,outm]=process.argv;const lat=+lat_,lon=+lon_,half=+half_;
async function range(a,b){const r=await fetch(url,{headers:{Range:`bytes=${a}-${b}`}});return Buffer.from(await r.arrayBuffer())}
function utm(lat,lon,zone){const a=6378137,f=1/298.257223563,k0=0.9996,e2=f*(2-f),ep2=e2/(1-e2);const l0=((zone-1)*6-180+3)*Math.PI/180;
 const p=lat*Math.PI/180,l=lon*Math.PI/180;const N=a/Math.sqrt(1-e2*Math.sin(p)**2),T=Math.tan(p)**2,C=ep2*Math.cos(p)**2,A=Math.cos(p)*(l-l0);
 const M=a*((1-e2/4-3*e2*e2/64-5*e2**3/256)*p-(3*e2/8+3*e2*e2/32+45*e2**3/1024)*Math.sin(2*p)+(15*e2*e2/256+45*e2**3/1024)*Math.sin(4*p)-(35*e2**3/3072)*Math.sin(6*p));
 const x=k0*N*(A+(1-T+C)*A**3/6+(5-18*T+T*T+72*C-58*ep2)*A**5/120)+500000;
 const y=k0*(M+N*Math.tan(p)*(A*A/2+(5-T+9*C+4*C*C)*A**4/24+(61-58*T+T*T+600*C-330*ep2)*A**6/720));return[x,y]}
(async()=>{let h=await range(0,1<<20);const le=h.toString('ascii',0,2)==='II';const r16=o=>le?h.readUInt16LE(o):h.readUInt16BE(o),r32=o=>le?h.readUInt32LE(o):h.readUInt32BE(o);
 const big=r16(2)===43;if(big)throw 'bigtiff';let ifd=r32(4);const n=r16(ifd);const tags={};
 const sz={1:1,2:1,3:2,4:4,5:8,12:8,16:8};
 for(let i=0;i<n;i++){const o=ifd+2+i*12,tag=r16(o),type=r16(o+2),cnt=r32(o+4);const bytes=sz[type]*cnt;const vo=bytes<=4?o+8:r32(o+8);
  const vals=[];for(let k=0;k<cnt&&k<200000;k++){const q=vo+k*sz[type];if(q+sz[type]>h.length){h=Buffer.concat([h,await range(h.length,q+sz[type]*cnt+16)])}
   vals.push(type===3?r16(q):type===4?r32(q):type===12?(le?h.readDoubleLE(q):h.readDoubleBE(q)):type===16?Number(le?h.readBigUInt64LE(q):h.readBigUInt64BE(q)):h[q])}tags[tag]=vals}
 const bps=tags[258][0];const W=tags[256][0],H=tags[257][0],TW=tags[322][0],TH=tags[323][0],comp=tags[259][0],pred=(tags[317]||[1])[0],spp=tags[277][0];
 const scale=tags[33550],tie=tags[33922];const offs=tags[324],cnts=tags[325];
 console.log({W,H,TW,TH,comp,pred,spp,scale:scale.slice(0,2),tie:tie.slice(3,5)});
 const [ux,uy]=utm(lat,lon,36);const px=(ux-tie[3])/scale[0],py=(tie[4]-uy)/scale[1];const hp=half/scale[0];
 const x0=Math.floor(px-hp),y0=Math.floor(py-hp),x1=Math.ceil(px+hp),y1=Math.ceil(py+hp);const OW=x1-x0,OH=y1-y0;const out=Buffer.alloc(OW*OH*2);
 const tpr=Math.ceil(W/TW);
 for(let ty=Math.floor(y0/TH);ty<=Math.floor((y1-1)/TH);ty++)for(let tx=Math.floor(x0/TW);tx<=Math.floor((x1-1)/TW);tx++){
  const ti=ty*tpr+tx;const raw=await range(offs[ti],offs[ti]+cnts[ti]-1);let d=comp===8||comp===32946?zlib.inflateSync(raw):raw;
  if(pred===2){for(let r=0;r<TH;r++)for(let c=1;c<TW;c++){const i=(r*TW+c)*2;d.writeUInt16LE((d.readUInt16LE(i)+d.readUInt16LE(i-2))&65535,i)}}
  for(let r=0;r<TH;r++){const gy=ty*TH+r;if(gy<y0||gy>=y1)continue;for(let c=0;c<TW;c++){const gx=tx*TW+c;if(gx<x0||gx>=x1)continue;const i=(r*TW+c)*2,o=((gy-y0)*OW+(gx-x0))*2;out[o]=d[i];out[o+1]=d[i+1]}}}
 fs.writeFileSync(outp,Buffer.concat([Buffer.from(`P6 ${OW} ${OH} 255\n`),out]));
 fs.writeFileSync(outm,JSON.stringify({url,utm_zone:'36N (EPSG:32636)',origin_utm:[tie[3]+x0*scale[0],tie[4]-y0*scale[1]],pixel_m:scale[0],size:[OW,OH],centre_latlon:[lat,lon],centre_utm:[ux,uy]},null,1));console.log('crop',OW,OH);
})().catch(e=>{console.error(e);process.exit(1)});
