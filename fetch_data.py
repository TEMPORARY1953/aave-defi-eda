"""Загрузка реальных данных. Запуск: python fetch_data.py. Ключи только из .env."""
import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from web3 import Web3

ROOT = Path(__file__).resolve().parent
RAW = ROOT / 'data/raw'
RAW.mkdir(parents=True, exist_ok=True)
load_dotenv(ROOT / '.env')
TOKEN = '0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9'
GRAPH = os.getenv('THEGRAPH_URL') or 'https://metisapi.0xgraph.xyz/subgraphs/name/aave/protocol-v3-metis'
RPC = os.getenv('ETH_RPC_URL') or 'https://eth-mainnet.public.blastapi.io'
START = pd.Timestamp('2025-11-23', tz='UTC')
END = pd.Timestamp('2026-11-21', tz='UTC')  # последняя завершённая UTC-дата на момент работы
manifest = []
session = requests.Session()
session.headers['User-Agent'] = 'Mozilla/5.0 (Aave educational EDA)'


def request(name, url, payload=None, params=None):
    """Сохраняем исходный ответ и provenance. Секреты не сохраняем."""
    for attempt in range(3):
        try:
            r = session.post(url, json=payload, timeout=60) if payload else session.get(url, params=params, timeout=60)
            r.raise_for_status()
            break
        except requests.RequestException:
            if attempt == 2:
                raise
            time.sleep(2)
    path = RAW / name
    path.write_bytes(r.content)
    public_params = {k:v for k,v in (params or {}).items() if 'key' not in k.lower()}
    public_url = url
    if url == RPC and url != 'https://eth-mainnet.public.blastapi.io':
        public_url = '<ETH_RPC_URL>'
    if url == GRAPH and url != 'https://metisapi.0xgraph.xyz/subgraphs/name/aave/protocol-v3-metis':
        public_url = '<THEGRAPH_URL>'
    manifest.append({'file':str(path.relative_to(ROOT)), 'url':public_url,
                     'params':public_params, 'query':payload,
                     'retrieved_at_utc':datetime.now(timezone.utc).isoformat(),
                     'http_status':r.status_code, 'sha256':hashlib.sha256(r.content).hexdigest()})
    (ROOT/'data/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    return r


def graph_query(name, query):
    body = request(name, GRAPH, {'query':query}).json()
    if body.get('errors'):
        raise RuntimeError(body['errors'])
    return body['data']


def parse_etherscan(html):
    """Только таблица обычных транзакций; соседние вкладки и pending исключены."""
    soup = BeautifulSoup(html, 'html.parser')
    rows = []
    for row in soup.select('#table-view-tab-pane tbody tr'):
        tx = row.select_one('a[href^="/tx/0x"]')
        block = row.select_one('a[href^="/block/"]')
        date = row.select_one('.showDate')
        method = row.select_one('.td_functionNameOri')
        if tx and block and date:
            rows.append({'tx_hash':tx['href'].split('/')[-1], 'block_number':int(block.get_text(strip=True)),
                         'timestamp_utc':date.get_text(strip=True),
                         'method':method.get_text(' ', strip=True) if method else 'unknown'})
    if not rows:
        raise RuntimeError('Публичная таблица Etherscan недоступна или её разметка изменилась')
    return pd.DataFrame(rows)


def collect():
    print('DeFiLlama / CoinGecko', flush=True)
    for slug in ['aave', 'compound-finance', 'morpho']:
        request(f'defillama_{slug}.json', f'https://api.llama.fi/protocol/{slug}')
    request('defillama_protocols.json', 'https://api.llama.fi/protocols')
    cg_params = {'vs_currency':'usd', 'days':365, 'interval':'daily'}
    if os.getenv('COINGECKO_API_KEY'):
        cg_params['x_cg_demo_api_key'] = os.environ['COINGECKO_API_KEY']
    request('coingecko_aave.json', 'https://api.coingecko.com/api/v3/coins/aave/market_chart', params=cg_params)

    print('Etherscan: открытые страницы, REST API отдельно', flush=True)
    request('etherscan_token.html', f'https://etherscan.io/token/{TOKEN}')
    html = request('etherscan_transactions.html', f'https://etherscan.io/address/{TOKEN}').text
    transactions = parse_etherscan(html)
    transactions.to_csv(ROOT/'data/etherscan_transactions.csv', index=False)
    # Реально проверяем API; не считаем сообщение об ошибке использованием данных API.
    api = request('etherscan_api_status.json', 'https://api.etherscan.io/v2/api', params={
        'chainid':1,'module':'stats','action':'tokensupply','contractaddress':TOKEN,
        'apikey':os.getenv('ETHERSCAN_API_KEY') or 'YourApiKeyToken'}).json()
    print('Etherscan REST status:', api.get('message'), '; HTML transactions:', len(transactions), flush=True)

    print('The Graph: Aave V3 Metis, недельные наблюдения m.USDC', flush=True)
    reserves = graph_query('graph_reserves.json', '{ _meta { block { number timestamp } hasIndexingErrors } reserves(first:100) { id symbol decimals } }')
    reserve_id = next(x['id'] for x in reserves['reserves'] if x['symbol']=='m.USDC')
    dates = pd.date_range(START, END, freq='7D')
    graph_rows = []
    # В каждом недельном окне берём первое реальное обновление; это не средняя ставка за неделю.
    for batch in range(0, len(dates), 10):
        bits = []
        for i, date in enumerate(dates[batch:batch+10]):
            begin = int(date.timestamp())
            finish = min(begin + 7*86400, int(pd.Timestamp('2026-11-22', tz='UTC').timestamp()))
            bits.append(f'd{i}: reserveParamsHistoryItems(first:1, orderBy:timestamp, orderDirection:asc, where:{{reserve:"{reserve_id}",timestamp_gte:{begin},timestamp_lt:{finish}}}) {{ id timestamp liquidityRate variableBorrowRate availableLiquidity }}')
        result = graph_query(f'graph_history_{batch//10}.json', '{'+'\n'.join(bits)+'}')
        for entries in result.values():
            graph_rows.extend(entries)
    if not graph_rows:
        raise RuntimeError('Subgraph не вернул исторических наблюдений')
    pd.DataFrame(graph_rows).to_csv(ROOT/'data/graph_metis_usdc.csv', index=False)

    print('web3.py: исторические eth_call через Ethereum RPC', flush=True)
    book = request('AaveV3Ethereum.sol', 'https://raw.githubusercontent.com/bgd-labs/aave-address-book/main/src/AaveV3Ethereum.sol').text
    a_token = re.search(r'AAVE_A_TOKEN\s*=\s*(0x[0-9a-fA-F]{40})', book).group(1)
    w3 = Web3(Web3.HTTPProvider(RPC, request_kwargs={'timeout':60}))
    assert w3.eth.chain_id == 1
    abi = [
        {'name':'totalSupply','type':'function','stateMutability':'view','inputs':[], 'outputs':[{'type':'uint256'}]},
        {'name':'decimals','type':'function','stateMutability':'view','inputs':[], 'outputs':[{'type':'uint8'}]},
        {'name':'balanceOf','type':'function','stateMutability':'view','inputs':[{'name':'account','type':'address'}], 'outputs':[{'type':'uint256'}]},
    ]
    contract = w3.eth.contract(address=Web3.to_checksum_address(TOKEN), abi=abi)
    decimals = contract.functions.decimals().call()
    rpc_rows = []
    sample_dates = sorted(set([START, END] + list(pd.date_range(START, END, freq='MS'))))
    for date in sample_dates:
        stamp = int(date.timestamp())
        info = request(f'ethereum_block_{stamp}.json', f'https://coins.llama.fi/block/ethereum/{stamp}').json()
        block = w3.eth.get_block(int(info['height']))
        number = block['number']
        supply = contract.functions.totalSupply().call(block_identifier=number)
        balance = contract.functions.balanceOf(Web3.to_checksum_address(a_token)).call(block_identifier=number)
        rpc_rows.append({'requested_date_utc':date.isoformat(), 'block_number':number,
                         'block_hash':block['hash'].hex(), 'block_timestamp':block['timestamp'],
                         'total_supply_raw':str(supply), 'aave_cash_raw':str(balance),
                         'decimals':decimals, 'total_supply_aave':supply/10**decimals,
                         'aave_v3_cash_aave':balance/10**decimals})
        print(date.date(), number, flush=True)
    (RAW/'web3_snapshots.json').write_text(json.dumps({'chain_id':1,'token':TOKEN,'a_token':a_token,'abi':abi,'samples':rpc_rows}, indent=2), encoding='utf-8')
    manifest.append({'file':'data/raw/web3_snapshots.json','url':RPC if RPC == 'https://eth-mainnet.public.blastapi.io' else '<ETH_RPC_URL>',
                     'methods':['eth_chainId','eth_getBlockByNumber','eth_call'],
                     'retrieved_at_utc':datetime.now(timezone.utc).isoformat(),
                     'sha256':hashlib.sha256((RAW/'web3_snapshots.json').read_bytes()).hexdigest()})
    pd.DataFrame(rpc_rows).to_csv(ROOT/'data/web3_monthly.csv', index=False)
    (ROOT/'data/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Все пять источников собраны.', flush=True)


if __name__ == '__main__':
    collect()
