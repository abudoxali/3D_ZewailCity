// Rasterise OSM JSON (Overpass "out geom") into a PPM -> PNG for inspection.
// usage: node osm_raster.js in.json out.ppm minlat minlon maxlat maxlon px_per_m
const fs=require('fs');const [,,inp,out,a,b,c,d,ppm]=process.argv;
const minlat=+a,minlon=+b,maxlat=+c,maxlon=+d,s=+ppm;
const lat0=(minlat+maxlat)/2,mlat=111320,mlon=111320*Math.cos(lat0*Math.PI/180);
const W=Math.round((maxlon-minlon)*mlon*s),H=Math.round((maxlat-minlat)*mlat*s);
const buf=Buffer.alloc(W*H*3,255);
const X=lo=>(lo-minlon)*mlon*s,Y=la=>(maxlat-la)*mlat*s;
function px(x,y,c){x|=0;y|=0;if(x<0||y<0||x>=W||y>=H)return;const i=(y*W+x)*3;buf[i]=c[0];buf[i+1]=c[1];buf[i+2]=c[2]}
function line(x0,y0,x1,y1,c,w){const n=Math.ceil(Math.hypot(x1-x0,y1-y0))+1;for(let i=0;i<=n;i++){const x=x0+(x1-x0)*i/n,y=y0+(y1-y0)*i/n;for(let dx=-w;dx<=w;dx++)for(let dy=-w;dy<=w;dy++)px(x+dx,y+dy,c)}}
const data=JSON.parse(fs.readFileSync(inp));
const col=t=>t.building?[200,40,40]:t.highway==='footway'?[60,160,60]:t.highway==='service'?[120,120,220]:t.highway?[30,30,30]:t.barrier==='wall'||t.barrier==='fence'?[180,120,0]:t.landuse||t.leisure||t.amenity?[200,170,220]:null;
const wid=t=>t.highway&&/secondary|primary|trunk/.test(t.highway)?2:t.highway&&t.highway!=='footway'?1:0;
for(const e of data.elements){if(e.type!=='way'||!e.geometry)continue;const t=e.tags||{};const c=col(t);if(!c)continue;
 for(let i=1;i<e.geometry.length;i++){const p=e.geometry[i-1],q=e.geometry[i];if(!p||!q)continue;line(X(p.lon),Y(p.lat),X(q.lon),Y(q.lat),c,wid(t))}}
for(const e of data.elements){if(e.type==='node'&&e.tags&&(e.tags.barrier)){const x=X(e.lon),y=Y(e.lat);for(let dx=-3;dx<=3;dx++)for(let dy=-3;dy<=3;dy++)px(x+dx,y+dy,[255,0,255])}}
// 100 m grid ticks
for(let gx=0;gx<W;gx+=100*s)for(let y=0;y<H;y+=4)px(gx,y,[210,210,210]);
for(let gy=0;gy<H;gy+=100*s)for(let x=0;x<W;x+=4)px(x,gy,[210,210,210]);
fs.writeFileSync(out,Buffer.concat([Buffer.from(`P6 ${W} ${H} 255\n`),buf]));console.log(W,H);
