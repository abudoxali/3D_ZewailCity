"""Verify delivered file hashes without modifying the frozen baseline."""
from pathlib import Path
import json,hashlib,sys
R=Path(__file__).resolve().parents[1]
m=json.loads((R/'FROZEN_BASELINE.json').read_text(encoding='utf-8'))
fail=[]
for name,h in m['files'].items():
 p=R/name
 if not p.is_file() or hashlib.file_digest(p.open('rb'),'sha256').hexdigest()!=h:fail.append(name)
print(f"Frozen V19: {len(m['files'])-len(fail)}/{len(m['files'])} files match")
if fail:print('Changed/missing:',*fail,sep='\n')
sys.exit(bool(fail))
