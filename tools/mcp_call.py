"""Project-local real MCP stdio client; keeps tool schemas and results as evidence."""
import argparse
import asyncio
import base64
import json
import os
from pathlib import Path
import sys
from datetime import timedelta
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]

async def main():
    p = argparse.ArgumentParser()
    p.add_argument('server', choices=['blender', 'godot'])
    p.add_argument('tool', nargs='?')
    p.add_argument('--args', default='{}')
    p.add_argument('--code-file')
    p.add_argument('--blender-server',choices=['installed','ahuja'],default='ahuja')
    p.add_argument('--out', required=True)
    a = p.parse_args()
    env = dict(os.environ, BLENDER_HOST='127.0.0.1', BLENDER_PORT='9876', ENABLE_TELEMETRY='false')
    blender_exe = Path(os.environ['APPDATA']) / 'Claude/Claude Extensions/ant.dir.gh.blender.blender-mcp/.venv/Scripts/blender-mcp.exe'
    use_installed=a.server=='blender' and a.blender_server=='installed'
    params = StdioServerParameters(command=str(blender_exe) if use_installed else sys.executable,
        args=[] if use_installed else (['-m','blender_mcp.server'] if a.server=='blender' else
        [str(ROOT / 'tools/integrations/godot-mcp/mcp/godot_mcp_server.py')]), env=env)
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w, read_timeout_seconds=timedelta(seconds=300)) as s:
            init = await s.initialize()
            listing = await s.list_tools()
            all_tools = list(listing.tools)
            while listing.nextCursor:
                listing = await s.list_tools(cursor=listing.nextCursor)
                all_tools.extend(listing.tools)
            out = {'server': a.server, 'initialize': init.model_dump(mode='json'),
                   'tools': [t.model_dump(mode='json') for t in all_tools]}
            if a.tool:
                args = json.loads(a.args)
                if a.code_file:
                    args['code'] = Path(a.code_file).read_text(encoding='utf-8')
                    if a.server=='blender' and a.blender_server=='ahuja':
                        args['code']+='\nprint(result)\n'
                res = await s.call_tool(a.tool, args)
                out.update(tool=a.tool, result=res.model_dump(mode='json'))
                for i, c in enumerate(res.content):
                    if c.type == 'image':
                        image = Path(a.out).with_suffix(f'.{i}.png')
                        image.parent.mkdir(parents=True, exist_ok=True)
                        image.write_bytes(base64.b64decode(c.data))
                        out['result']['content'][i]['data'] = str(image)
            dest = Path(a.out)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(json.dumps(out, indent=2), encoding='utf-8')
            res = out.get('result', {})
            print(json.dumps({'evidence': str(dest), 'tool': a.tool, 'isError': res.get('isError'),
                  'result': str(res.get('structuredContent', res.get('content', [])))[:3500]}, ensure_ascii=True))

asyncio.run(main())
