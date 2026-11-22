"""Минимальный MCP-сервер: чтение только результатов этого проекта."""
import json
from pathlib import Path
from mcp.server.fastmcp import FastMCP

ROOT = Path(__file__).resolve().parent
mcp = FastMCP('Aave EDA')


@mcp.tool()
def get_analysis_summary() -> dict:
    """Вернуть сохранённые фактические показатели EDA Aave."""
    return json.loads((ROOT/'data/results_summary.json').read_text(encoding='utf-8'))


@mcp.tool()
def get_data_sources() -> dict:
    """Вернуть список источников и число сохранённых запросов, без API-ключей."""
    manifest = json.loads((ROOT/'data/manifest.json').read_text(encoding='utf-8'))
    return {'sources':['DeFiLlama','CoinGecko','Etherscan HTML','web3.py Ethereum RPC',
                       'The Graph Aave V3 Metis on 0xGraph'],
            'saved_responses':len(manifest)}


if __name__ == '__main__':
    mcp.run(transport='stdio')
