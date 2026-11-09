// Rasterise axis-frame OSM JSON. usage: node axis_raster.js in.json out.ppm xmin xmax ymin ymax px_per_m [dy]
// dy shifts y (e.g. -260.6 to put the origin at the dome).
const fs=require('fs');const [,,inp,out,a,b,c,d,s_,dy_]=process.argv;const xmin=+a,xmax=+b,ymin=+c,ymax=+d,s=+s_,dy=+(dy_||0);
const W=Math.round((xmax-xmin)*s),H=Math.round((ymax-ymin)*s);const buf=Buffer.alloc(W*H*3,255);
const X=x=>(x-xmin)*s,Y=y=>(ymax-(y+dy))*s;
function px(x,y,c){x|=0;y|=0;if(x<0||y<0||x>=W||y>=H)return;const i=(y*W+x)*3;buf[i]=c[0];buf[i+1]=c[1];buf[i+2]=c[2]}
function line(x0,y0,x1,y1,c,w){const n=Math.ceil(Math.hypot(x1-x0,y1-y0))+1;for(let i=0;i<=n;i++){const x=x0+(x1-x0)*i/n,y=y0+(y1-y0)*i/n;for(let dx=-w;dx<=w;dx++)for(let dy=-w;dy<=w;dy++)px(x+dx,y+dy,c)}}
for(let gx=Math.ceil(xmin/50)*50;gx<xmax;gx+=50)for(let y=0;y<H;y+=3)px(X(gx),y,gx===0?[150,150,255]:[215,215,215]);
for(let gy=Math.ceil((ymin)/50)*50;gy<ymax;gy+=50)for(let x=0;x<W;x+=3)px(x,(ymax-gy)*s,gy===0?[150,150,255]:[215,215,215]);
const j=JSON.parse(fs.readFileSync(inp));
const col=t=>t.building?[200,30,30]:t.highway==='footway'||t.highway==='pedestrian'?[40,150,40]:t.highway==='service'?[70,70,230]:t.highway?[20,20,20]:t.barrier?[200,130,0]:(t.landuse||t.leisure||t.amenity)?[190,150,220]:null;
for(const w of j.ways){const c=col(w.tags);if(!c)continue;const wd=w.tags.building||/secondary|unclassified/.test(w.tags.highway||'')?1:0;for(let i=1;i<w.pts.length;i++)line(X(w.pts[i-1][0]),Y(w.pts[i-1][1]),X(w.pts[i][0]),Y(w.pts[i][1]),c,wd)}
for(const n of j.nodes)if(n.tags.barrier){for(let dx=-3;dx<=3;dx++)for(let dy2=-3;dy2<=3;dy2++)px(X(n.p[0])+dx,Y(n.p[1])+dy2,[255,0,255])}
fs.writeFileSync(out,Buffer.concat([Buffer.from(`P6 ${W} ${H} 255\n`),buf]));console.log(W,H);
