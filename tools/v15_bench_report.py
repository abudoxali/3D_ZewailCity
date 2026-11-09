import json
from pathlib import Path
F=Path(__file__).resolve().parents[1]/'output/validation/v15/bench'
def agg(v):
    ds=[json.loads(p.read_text()) for p in sorted((F/v).glob(f'game_capture_perf_{v}_*.json'))];views=list(ds[0]['views'])
    per={k:sum(d['views'][k]['avg_ms'] for d in ds)/len(ds) for k in views}
    g=lambda key:[d['views'][k].get(key) for d in ds for k in views]
    return dict(runs=len(ds),adapter=ds[0]['adapter'],resolution=ds[0]['actual_render_resolution'],fov=ds[0]['fov'],vsync=[d['actual_vsync_mode'] for d in ds],max_fps=[d['actual_max_fps'] for d in ds],
      aggregate_fps=round(1000/(sum(per.values())/len(per)),1),aggregate_fps_per_run=[round(1000/(sum(d['views'][k]['avg_ms'] for k in views)/len(views)),1) for d in ds],
      mean_frame_ms=round(sum(per.values())/len(per),3),slowest_view=max(per,key=per.get),slowest_fps=round(1000/max(per.values()),1),worst_p99_ms=max(g('p99_ms')),
      per_view_fps={k:round(1000/per[k],1) for k in views},draw_range=[min(g('draws')),max(g('draws'))],primitive_range=[min(g('rendered_primitives')),max(g('rendered_primitives'))],
      texture_memory_bytes=max([x for x in g('texture_memory_bytes') if x] or [0]) or 'UNKNOWN',load_ms=[d['loading'].get('load_ms') for d in ds])
r={'method':'RTX 4070, 1920x1080 High, FOV 84.25, VSync off/max_fps 0, 12 stored views (V14 set + V15_median_eye, V13_approach_aerial), 90 warmup + 180 measured frames; V14,V15 alternating x2'}
for v in ['v14','v15']:r[v]=agg(v)
a,c=r['v14']['aggregate_fps'],r['v15']['aggregate_fps']
r['v15_vs_v14_percent']=round((c-a)/a*100,1)
r['targets']={'all_views_ge_60':min(r['v15']['per_view_fps'].values())>=60,'slowest_ge_90':r['v15']['slowest_fps']>=90}
(F/'performance_v14_v15.json').write_text(json.dumps(r,indent=2))
for v in ['v14','v15']:print(v,{k:r[v][k] for k in ['aggregate_fps','aggregate_fps_per_run','mean_frame_ms','slowest_view','slowest_fps','worst_p99_ms','draw_range','primitive_range','texture_memory_bytes','load_ms']})
print('v15 vs v14',r['v15_vs_v14_percent'],'%',r['targets']);print('v15 per view',r['v15']['per_view_fps'])
