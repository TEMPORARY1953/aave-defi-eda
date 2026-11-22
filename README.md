# DeFi EDA Aave

Учебный анализ Lending-протокола Aave по условию `Task.docx`: пять инструментов,
сравнение с Compound и Morpho, семь рисунков, выводы, описание MCP и доступный журнал диалога.

## Запуск

Нужен Python 3.12. В PowerShell откройте эту папку:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m jupyterlab analysis.ipynb
```

В Jupyter выберите Python из этого окружения и выполните **Restart Kernel and Run All Cells**.
Активация PowerShell-окружения не требуется. Ноутбук по умолчанию читает приложенный снимок,
поэтому интернет и ключи для пересчёта не нужны. Для автоматического выполнения всех ячеек:

```powershell
.\.venv\Scripts\python.exe execute_notebook.py
```

Скрипт создаёт временное ядро в `.runtime/`, выполняет ноутбук в чистом процессе Python из
`.venv` и сохраняет выполненные ячейки обратно в `analysis.ipynb`.

## Основные результаты

Общий период: **23.11.2025–21.11.2026**, **364 дневных наблюдения**. Снимок загружен 22.11.2026.
Текущий неполный день исключён из дневного сравнения; отдельная выборка Etherscan относится
к моменту загрузки и не смешивается с годовой статистикой.

- TVL Aave: **28.27 → 15.84 млрд USD**, изменение **−44.0%**.
- Цена AAVE: **161.12 → 97.85 USD**, изменение **−39.3%**.
- TVL Morpho вырос на **69.0%**, Compound снизился на **43.5%**.
- Ethereum занимает **84.6%** TVL Aave на последнюю общую дату.
- Aave V3 — **3-е место** по TVL в сохранённом списке DeFiLlama после исключения CEX.

Расчёты — в `analysis.ipynb`, выводы — в `REPORT.md`.
Изменение долларового TVL не равно чистому притоку средств. Причина резкого апрельского
снижения отдельно не установлена: это наблюдение ряда API, без придуманного объяснения.

## Пять использованных инструментов

| Инструмент | Реальные данные | Способ доступа и ограничения |
|---|---|---|
| DeFiLlama | TVL Aave, Compound, Morpho; TVL сетей; top-50 | Бесплатный REST API, parent-серии без добавления borrowed/staking/pool2 |
| CoinGecko | Дневная цена, капитализация, 24ч объём AAVE | Бесплатный market_chart REST API, USD |
| Etherscan | 18 подтверждённых последних транзакций к AAVE; страница токена | Публичный HTML; выборка примерно за 10 минут 22.11.2026, не полная годовая история |
| web3.py | 14 исторических снимков эмиссии AAVE и остатка на aAAVE | Ethereum eth_call через бесплатный архивный RPC Blast API |
| The Graph | 49 наблюдений APR m.USDC в 52 недельных окнах | Subgraph Aave V3 Metis на 0xGraph, указанный в официальном репозитории Aave |

Etherscan REST API вернул `Missing/Invalid API Key`, а отдельная страница `/txs` — 403.
Удалось прочитать основную таблицу страницы `/address/…`; pending и соседние вкладки исключены.
HTML не выдаётся за успешное обращение к REST API. Полная история Transfer events не собиралась.

PublicNode отклонил исторические eth_call, 1RPC не имел нужного состояния; Blast API вернул
исторические значения. Номера блоков найдены через DeFiLlama Block API, сами значения — через RPC.
Устаревший hosted endpoint The Graph недоступен; использовано действующее размещение Metis
на 0xGraph, **не gateway The Graph Network**. Обычный GraphQL API Aave не подменяет The Graph.
В недельных окнах без наблюдений данные не придумывались.

Источники: [DeFiLlama](https://api.llama.fi/protocol/aave),
[методология TVL](https://docs.llama.fi/analysts/data-definitions),
[CoinGecko](https://docs.coingecko.com/reference/coins-id-market-chart),
[Etherscan](https://etherscan.io/address/0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9),
[subgraphs Aave](https://github.com/aave/protocol-subgraphs#active-deployments),
[адресная книга](https://github.com/bgd-labs/aave-address-book/blob/main/src/AaveV3Ethereum.sol),
[web3.py](https://web3py.readthedocs.io/en/stable/).

## Повторная загрузка

Для приложенного снимка ключи не нужны. Если нужны свои ключи или RPC, скопируйте
`.env.example` в `.env` и заполните переменные. Не записывайте ключи в ноутбук или репозиторий.

```powershell
Copy-Item .env.example .env
.\.venv\Scripts\python.exe fetch_data.py
.\.venv\Scripts\python.exe execute_notebook.py
```

Либо выставьте `REFRESH_DATA = True` в начале ноутбука и выполните его целиком.
Исходные ответы сохраняются в `data/raw/`, параметры, время и SHA-256 — в `data/manifest.json`.
Новая загрузка перезапишет снимок, а пересчёт — графики и `REPORT.md`.
Если загрузка прервалась, завершите её перед анализом: частично обновлённый набор непригоден.

Окно исследования в `fetch_data.py` и ноутбуке зафиксировано для этой сдачи. CoinGecko
`days=365` — скользящий запрос: при запуске значительно позднее часть нужных дат исчезнет
из бесплатного ответа. Для точного повторения используйте приложенный снимок; для нового
исследования согласованно измените даты в обоих файлах. Бесплатные endpoints могут менять
доступность. RPC должен поддерживать архивные eth_call. Замена Metis на Ethereum subgraph
потребует изменить выбранный резерв и пояснения.

## Файлы

- `analysis.ipynb` — выполненный ноутбук с кодом, текстом, таблицами и семью рисунками.
- `REPORT.md` — итоговый отчёт на русском языке.
- `requirements.txt`, `.env.example` — зависимости и пример настроек.
- `fetch_data.py`, `execute_notebook.py` — загрузка и автоматический запуск.
- `data/raw/` — исходные JSON, HTML, адресная книга и RPC-снимки.
- `data/*.csv` — подготовленные таблицы; `results_summary.json` — основные результаты.
- `plots/` — семь PNG: TVL, конкуренты, цена, капитализация и объём, сети, индексы роста,
  три панели ончейн-наблюдений.
- `MCP_SETUP.md`, `mcp_server.py`, `verify_mcp.py`, `mcp_config.example.json` — минимальный MCP.
- `LLM_USAGE.md`, `export_dialogue.py`, `logs/` — описание ИИ и доступный снимок диалога.
- `data/probes/` — сохранённые проверки доступности источников.

## Проверка и ручной шаг

Зависимости установлены в `.venv`; `pip check` прошёл. Все ячейки выполнены в чистом ядре.
Проверены SHA-256, пропуски, уникальность дат, масштабы значений и сумма TVL сетей.
В основных дневных рядах нет пропусков, сумма сетей совпала с общим TVL.
Все семь PNG просмотрены: заголовки, даты и единицы измерения присутствуют.

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe verify_mcp.py
.\.venv\Scripts\python.exe verify_project.py
```

MCP-клиент действительно выполнил initialize/list/call; ответ сохранён в
`data/mcp_verification.json`. Подключать сервер к интерфейсу Codex для проверки EDA не нужно.

**Перед сдачей обновите журнал после финального ответа** командой
`.\.venv\Scripts\python.exe export_dialogue.py` и проверьте полноту. Если локальный журнал
не содержит завершённый диалог, приложите полный видимый диалог вручную по `LLM_USAGE.md`.
Публичный Dune dashboard — необязательная часть, не создавался.
