import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import requests
from bs4 import BeautifulSoup

root = Path('data/probes')
token = '0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9'
jobs = [
 ('etherscan_token_transfers', f'https://etherscan.io/token/generic-tokentxns2?m=normal&contractAddress={token}&a=&sid=&p=1', None),
 ('graph_schema', 'https://metisapi.0xgraph.xyz/subgraphs/name/aave/protocol-v3-metis', {'query':'{ __type(name:"ReserveParamsHistoryItem") { fields { name } } }'}),
 ('address_book', 'https://raw.githubusercontent.com/bgd-labs/aave-address-book/main/src/AaveV3Ethereum.sol', None),
 ('llama_protocols', 'https://api.llama.fi/protocols', None),
]
def run(job):
 name, url, payload = job
 try:
  r=requests.post(url,json=payload,timeout=40) if payload else requests.get(url,timeout=40)
  (root/(name+'.txt')).write_text(r.text,encoding='utf-8')
  print(name,r.status_code,len(r.content),r.text[:120])
 except Exception as e: print(name,type(e).__name__,str(e)[:120])
with ThreadPoolExecutor(max_workers=4) as pool: list(pool.map(run,jobs))
for name in ['etherscan_token_transfers','etherscan_transfers']:
 p=root/(name+'.txt')
 if not p.exists(): continue
 soup=BeautifulSoup(p.read_text(encoding='utf-8'),'html.parser')
 for row in soup.select('tbody tr')[:2]: print(name,str(row)[:4000])
for name in ['llama_aave','llama_compound','llama_morpho']:
 d=json.loads((root/(name+'.txt')).read_text(encoding='utf-8'))
 print(name,'keys',list(d),'last',d.get('tvl',[])[-1:],'chains',list(d.get('chainTvls',{})))
