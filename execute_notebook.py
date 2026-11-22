"""Выполнение всех ячеек в чистом ядре именно текущего Python-окружения."""
import json
import sys
from pathlib import Path
import nbformat
from nbclient import NotebookClient

root = Path(__file__).resolve().parent
kernel_dir = root/'.runtime/kernels/aave-eda'
kernel_dir.mkdir(parents=True, exist_ok=True)
(kernel_dir/'kernel.json').write_text(json.dumps({
    'argv':[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],
    'display_name':'Aave EDA', 'language':'python'}), encoding='utf-8')
import os
os.environ['JUPYTER_PATH'] = str(root/'.runtime')
os.environ['JUPYTER_RUNTIME_DIR'] = str(root/'.runtime/jupyter')
os.environ['IPYTHONDIR'] = str(root/'.runtime/ipython')
os.environ['MPLCONFIGDIR'] = str(root/'.runtime/matplotlib')
Path(os.environ['JUPYTER_RUNTIME_DIR']).mkdir(parents=True, exist_ok=True)
notebook = nbformat.read(root/'analysis.ipynb', as_version=4)
client = NotebookClient(notebook, timeout=300, kernel_name='aave-eda', resources={'metadata':{'path':str(root)}})
client.execute()
nbformat.write(notebook, root/'analysis.ipynb')
print('Все ячейки выполнены без ошибок.')
