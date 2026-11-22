"""Однократная проверка открытых endpoints; ответы сохранены для аудита."""
import json
import urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

OUT = Path('data/probes')
OUT.mkdir(parents=True, exist_ok=True)
TOKEN = '0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9'
jobs = [
    ('etherscan_address', f'https://etherscan.io/address/{TOKEN}', None),
    ('etherscan_txs100', f'https://etherscan.io/txs?a={TOKEN}&ps=100', None),
    ('etherscan_genericjs', 'https://etherscan.io/assets/js/custom/generic.js?v=26.11.3.2', None),
    ('etherscan_token_transfers', f'https://etherscan.io/token/generic-tokentxns2?m=normal&contractAddress={TOKEN}&a=&sid=&p=1', None),
    ('graph_schema', 'https://metisapi.0xgraph.xyz/subgraphs/name/aave/protocol-v3-metis', {'query':'{ __type(name:"ReserveParamsHistoryItem") { fields { name } } }'}),
    ('address_book', 'https://raw.githubusercontent.com/bgd-labs/aave-address-book/main/src/AaveV3Ethereum.sol', None),
    ('llama_protocols', 'https://api.llama.fi/protocols', None),
    ('coingecko', 'https://api.coingecko.com/api/v3/coins/aave/market_chart?vs_currency=usd&days=365&interval=daily', None),
    ('etherscan_api', f'https://api.etherscan.io/v2/api?chainid=1&module=stats&action=tokensupply&contractaddress={TOKEN}&apikey=YourApiKeyToken', None),
    ('etherscan_token', f'https://etherscan.io/token/{TOKEN}', None),
    ('etherscan_transfers', f'https://etherscan.io/tokentxns?a={TOKEN}', None),
    ('graph_metis', 'https://metisapi.0xgraph.xyz/subgraphs/name/aave/protocol-v3-metis', {'query':'{ _meta { block { number timestamp } } reserves(first: 5) { id symbol decimals liquidityRate } }'}),
    ('graph_old', 'https://api.thegraph.com/subgraphs/name/aave/protocol-v3', {'query':'{ _meta { block { number } } }'}),
    ('rpc_publicnode', 'https://ethereum-rpc.publicnode.com', {'jsonrpc':'2.0','id':1,'method':'eth_blockNumber','params':[]}),
    ('rpc_llama', 'https://eth.llamarpc.com', {'jsonrpc':'2.0','id':1,'method':'eth_blockNumber','params':[]}),
    ('llama_aave', 'https://api.llama.fi/protocol/aave', None),
    ('llama_compound', 'https://api.llama.fi/protocol/compound-finance', None),
    ('llama_morpho', 'https://api.llama.fi/protocol/morpho', None),
]

def run(job):
    name, url, payload = job
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode() if payload else None,
              headers={'User-Agent':'Mozilla/5.0 (educational DeFi EDA)', 'Content-Type':'application/json'})
        with urllib.request.urlopen(req, timeout=40) as response:
            body = response.read()
            status = response.status
        (OUT / (name + '.txt')).write_bytes(body)
        return {'name':name,'url':url,'status':status,'bytes':len(body),'preview':body[:250].decode(errors='replace')}
    except Exception as exc:
        return {'name':name,'url':url,'error':str(exc)}

with ThreadPoolExecutor(max_workers=6) as pool:
    results = list(pool.map(run, jobs))
(OUT / 'results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
for item in results:
    print(json.dumps(item, ensure_ascii=False))
