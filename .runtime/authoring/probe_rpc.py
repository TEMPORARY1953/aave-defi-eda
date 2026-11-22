import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from web3 import Web3

endpoints = ['https://ethereum-rpc.publicnode.com', 'https://ethereum.publicnode.com',
             'https://eth.drpc.org', 'https://1rpc.io/eth', 'https://eth-mainnet.public.blastapi.io',
             'https://rpc.flashbots.net']
block = json.loads(Path('data/raw/ethereum_block_1763856000.json').read_text())['height']
def check(url):
    try:
        w3 = Web3(Web3.HTTPProvider(url, request_kwargs={'timeout':20}))
        value = w3.eth.call({'to':Web3.to_checksum_address('0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9'), 'data':'0x18160ddd'}, block_identifier=block)
        return {'url':url,'block':block,'totalSupply':str(int.from_bytes(value,'big'))}
    except Exception as e:
        return {'url':url,'error':str(e)[:250]}
with ThreadPoolExecutor(max_workers=6) as pool:
    rows = list(pool.map(check,endpoints))
Path('data/probes/rpc_archive.json').write_text(json.dumps(rows,indent=2))
print(json.dumps(rows,indent=2))
