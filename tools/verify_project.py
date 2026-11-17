"""Run inherited suites unchanged, plus V17 emitted-geometry/movement acceptance.

Failures are retained, including old absolute-height/route assumptions. Never
reinterpret a legacy failed suite as passed because the new suite passes.
"""
import os
from pathlib import Path
import subprocess,json,time,re,datetime
R=Path(__file__).resolve().parents[1];O=R/'output/checks';G=R/'game/godot'
tests=['V18Gallery','V17Reconstruction','Validate','V5Ground','V5Gates','V5Academic','V5Dormitory','V6Academic','V6Dormitory','V5Journey','V6Journey','V8Gates','V8Entries','V10AdminEntry','V11Gates','V11GateCoverage','V11PerimeterSeal','V11FullJourney','V11Ui','V15Corridor','V16AdminCirculation','V16Walkthrough']
d=O/'regressions';d.mkdir(parents=True,exist_ok=True);rows=[]
for name in tests:
    t=time.monotonic();p=d/(name+'.log')
    with p.open('w',encoding='utf-8') as log:
        try:code=subprocess.run([os.environ.get('GODOT_EXE','godot_console'),'--headless','--fixed-fps','60','--path',str(G),'res://tests/'+name+'.tscn'],cwd=R,stdout=log,stderr=subprocess.STDOUT,timeout=300).returncode
        except subprocess.TimeoutExpired:code=124
    s=p.read_text(encoding='utf-8',errors='replace')
    failures=[line for line in s.splitlines() if '[FAIL]' in line or 'SCRIPT ERROR' in line or re.search(r'\b[1-9]\d* failed\b',line)]
    rows.append(dict(suite=name,exit_code=code,passed_lines=s.count('[PASS]'),failures=failures,seconds=round(time.monotonic()-t,2),log=str(p.relative_to(R))))
    print(name,code,rows[-1]['passed_lines'],'passes',len(failures),'failures',flush=True)
    (d/'summary.json').write_text(json.dumps({'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'suites':rows,'passed_suites':sum(x['exit_code']==0 and not x['failures'] for x in rows),'passed_assertion_lines':sum(x['passed_lines'] for x in rows),'method':'Inherited assertions can repeat across derived suites; counts are not unique tests'},indent=2))
raise SystemExit(1 if any(x['exit_code'] or x['failures'] for x in rows) else 0)
