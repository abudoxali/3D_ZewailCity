"""Retained V12 command evidence; baseline evidence directories are never written."""
from pathlib import Path
import subprocess,json,time,datetime,argparse
R=Path(__file__).resolve().parents[1];O=R/'output/validation/v15'
p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('--timeout',type=int,default=300)
a,cmd=p.parse_known_args();cmd=cmd[1:] if cmd[:1]==['--'] else cmd
d=O/'logs';d.mkdir(exist_ok=True);start=time.monotonic();utc=datetime.datetime.now(datetime.timezone.utc).isoformat()
with (d/(a.name+'.log')).open('w',encoding='utf-8') as log:
    try:code=subprocess.run(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT,timeout=a.timeout).returncode
    except subprocess.TimeoutExpired:code=124
rep=dict(command=cmd,exit_code=code,seconds=round(time.monotonic()-start,2),started_utc=utc)
(d/(a.name+'.json')).write_text(json.dumps(rep,indent=2));print(json.dumps(rep));raise SystemExit(code)
