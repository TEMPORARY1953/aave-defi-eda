"""Финальная проверка файлов, выполненного ноутбука и происхождения данных."""
import hashlib
import importlib.metadata
import json
from datetime import datetime, timezone
from pathlib import Path

import nbformat
import pandas as pd
from PIL import Image
from fetch_data import parse_etherscan

root = Path(__file__).resolve().parent
required = ['analysis.ipynb','requirements.txt','.env.example','README.md','REPORT.md',
            'MCP_SETUP.md','LLM_USAGE.md']
assert all((root/name).is_file() for name in required)
manifest = json.loads((root/'data/manifest.json').read_text(encoding='utf-8'))
for item in manifest:
    assert hashlib.sha256((root/item['file']).read_bytes()).hexdigest() == item['sha256']
notebook = nbformat.read(root/'analysis.ipynb', as_version=4)
nbformat.validate(notebook)
code_cells = [c for c in notebook.cells if c.cell_type == 'code']
assert all(c.execution_count is not None for c in code_cells)
assert not any(o.output_type == 'error' for c in code_cells for o in c.outputs)
images_in_notebook = sum('image/png' in o.get('data',{}) for c in code_cells for o in c.outputs)
plots = sorted((root/'plots').glob('*.png'))
assert len(plots) == images_in_notebook == 7
for path in plots:
    with Image.open(path) as image:
        image.verify()
daily = pd.read_csv(root/'data/analysis_daily.csv')
assert len(daily) == 364 and daily.notna().all().all() and daily['date'].is_unique
etherscan = parse_etherscan((root/'data/raw/etherscan_transactions.html').read_text(encoding='utf-8'))
saved = pd.read_csv(root/'data/etherscan_transactions.csv')
pd.testing.assert_frame_equal(etherscan, saved)
assert len(saved) == 18 and saved['tx_hash'].is_unique
web3 = json.loads((root/'data/raw/web3_snapshots.json').read_text(encoding='utf-8'))
assert web3['chain_id'] == 1
for sample in web3['samples']:
    target = pd.Timestamp(sample['requested_date_utc']).timestamp()
    assert 0 <= target-sample['block_timestamp'] < 60
    assert sample['aave_v3_cash_aave'] == int(sample['aave_cash_raw'])/10**sample['decimals']
summary = json.loads((root/'data/results_summary.json').read_text(encoding='utf-8'))
assert len(summary['sources_used']) == 5 and summary['aave_v3_defillama_rank'] <= 50
mcp = json.loads((root/'data/mcp_verification.json').read_text(encoding='utf-8'))
assert not mcp['summary_result']['isError'] and len(mcp['tools']) == 2
result = {'checked_at_utc':datetime.now(timezone.utc).isoformat(), 'status':'passed',
          'executed_code_cells':len(code_cells), 'plots':len(plots), 'raw_responses_sha256_verified':len(manifest),
          'daily_observations':len(daily), 'sources':summary['sources_used'],
          'etherscan_confirmed_sample':len(saved), 'web3_historical_blocks':len(web3['samples']),
          'mcp_verified':True,
          'versions':{name:importlib.metadata.version(name) for name in
                      ['pandas','numpy','matplotlib','seaborn','requests','web3','nbclient','mcp']}}
(root/'data/validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
