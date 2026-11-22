"""Реальная проверка MCP initialize -> tools/list -> tools/call по stdio."""
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    root = Path(__file__).resolve().parent
    params = StdioServerParameters(command=sys.executable, args=[str(root/'mcp_server.py')])
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as client:
            initialized = await client.initialize()
            listed = await client.list_tools()
            result = await client.call_tool('get_analysis_summary', {})
            sources = await client.call_tool('get_data_sources', {})
            assert not result.isError and not sources.isError
            payload = {'checked_at_utc':datetime.now(timezone.utc).isoformat(),
                       'initialize':initialized.model_dump(mode='json'),
                       'tools':[x.name for x in listed.tools],
                       'summary_result':result.model_dump(mode='json'),
                       'sources_result':sources.model_dump(mode='json')}
            (root/'data/mcp_verification.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
            print('MCP успешно проверен:', ', '.join(payload['tools']))


if __name__ == '__main__':
    asyncio.run(main())
