"""Экспорт доступных пользовательских и видимых ответов Codex из локального журнала.

Служебные инструкции, внутренние рассуждения и технические tool payloads не экспортируются.
Запустите после завершения диалога, чтобы обновить снимок, включая финальный ответ.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

root = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--session', type=Path, help='Путь к JSONL именно этой беседы')
args = parser.parse_args()
session_path = args.session
if session_path is None:
    candidates = sorted((Path.home()/'.codex/sessions').rglob('*.jsonl'), key=lambda p:p.stat().st_mtime, reverse=True)
    for path in candidates:
        with path.open(encoding='utf-8') as handle:
            first = json.loads(handle.readline())
        cwd = first.get('payload',{}).get('cwd','').replace('\\\\','\\')
        if cwd and Path(cwd).resolve() == root:
            session_path = path
            break
if session_path is None:
    raise SystemExit('Локальный журнал этой папки не найден. Сохраните полный видимый диалог вручную.')

messages = []
for line in session_path.read_text(encoding='utf-8').splitlines():
    try:
        record = json.loads(line)
    except json.JSONDecodeError:
        continue  # последний записываемый фрагмент может быть ещё не завершён
    payload = record.get('payload', {})
    if record.get('type') != 'response_item' or payload.get('type') != 'message':
        continue
    if payload.get('role') not in {'user','assistant'}:
        continue
    text = '\n'.join(item.get('text','') for item in payload.get('content',[])
                     if item.get('type') in {'input_text','output_text'})
    if text:
        messages.append({'timestamp':record.get('timestamp'), 'role':payload['role'], 'text':text})

out = root/'logs'
out.mkdir(exist_ok=True)
(out/'dialogue_snapshot.jsonl').write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in messages)+'\n', encoding='utf-8')
header = '# Доступный снимок видимого диалога Codex\n\nЭто автоматическая выгрузка реальных сообщений из локального журнала на момент экспорта.\nФинальный ответ и более поздние сообщения появятся после повторного запуска экспортёра.\nВнутренние рассуждения, служебные инструкции и технические tool payloads не включены.\n'
body = '\n\n'.join(f"## {x['role']} — {x['timestamp']}\n\n{x['text']}" for x in messages)
(out/'dialogue_snapshot.md').write_text(header+'\n'+body+'\n', encoding='utf-8')
(out/'export_metadata.json').write_text(json.dumps({'exported_at_utc':datetime.now(timezone.utc).isoformat(),
    'source_filename':session_path.name, 'visible_messages':len(messages),
    'complete_after_final_answer':False, 'scope':'user and visible assistant messages only'}, indent=2), encoding='utf-8')
print('Экспортировано реальных сообщений:',len(messages))
