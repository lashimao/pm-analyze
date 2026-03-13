# PM-Analyze

一个 Claude Skill，用来分析任意 Polymarket 钱包的公开数据。不需要 API Key，不需要装依赖，有 Python 就行。

## 怎么用

1. 打开任意 Polymarket 用户主页，复制地址栏里 `profile/` 后面的钱包地址

   ```
   https://polymarket.com/profile/0xABC123DEF456...
                                   ^^^^^^^^^^^^^^^^
                                   复制这段钱包地址
   ```

2. 跑脚本

   ```bash
   python3 scripts/polymarket_strategy_snapshot.py \
     --user 0xABC123DEF456... \
     --output snapshot.json
   ```

3. 搞定。打开 `snapshot.json` 看结果，或者丢给 AI 让它帮你解读。

## 你能看到什么

| 内容 | 举例 |
|---|---|
| 交易节奏 | 多久交一次，什么时间段活跃 |
| 市场偏好 | 玩体育？政治？加密？ |
| 持仓暴露 | 押了多少钱，押的哪边 |
| 盈亏 | 赚了还是亏了 |
| 盘口上下文 | 持仓附近的价差、深度、流动性 |
| 执行风格 | 市价单还是限价单，下单大小规律 |

## 隐私

默认自动脱敏，钱包地址会被打码成 `0x1234...abcd`，分析结果可以直接分享。

需要原始地址？加 `--include-identifiers`。

## 全部参数

| 参数 | 默认值 | 说明 |
|---|---|---|
| `--user` | 必填 | 目标钱包地址（0x...） |
| `--days` | 全部 | 回看天数 |
| `--limit` | 4000 | 最多拉多少条数据 |
| `--top-slugs` | 10 | 深入分析几个市场的盘口 |
| `--timeout` | 20 | HTTP 超时秒数 |
| `--retries` | 3 | 失败重试次数 |
| `--book-sleep-ms` | — | 盘口请求间隔（毫秒） |
| `--start-ts` | — | 起始时间戳（UTC 秒） |
| `--end-ts` | — | 结束时间戳（UTC 秒） |
| `--include-identifiers` | 关 | 保留原始钱包地址不脱敏 |
| `--output` | 标准输出 | 输出 JSON 文件路径 |

## 不做什么

- **不下单** — 纯分析，不会替你交易
- **不跟单** — 不生成任何跟单信号
- **不输出参数包** — 不会给你可复现的执行参数
- **不依赖私有接口** — 所有数据来自公开 API

## 作为 Skill 使用

这个仓库本身是一个 [Claude Skill](https://docs.anthropic.com/)，可以直接被 AI Agent 调用。`SKILL.md` 定义了工作流，`agents/openai.yaml` 定义了默认提示词。

丢一个 snapshot JSON 给 AI，它会帮你总结：市场偏好、执行风格、风险暴露、流动性观察和关键风险点。

## 环境要求

- Python 3.8+
- 不需要装任何包

## 跑测试

```bash
python3 -m unittest discover -s tests
```

---

# English

A Claude Skill for analyzing public data of any Polymarket wallet. No API key, no dependencies, just Python.

## How it works

1. Go to any Polymarket profile page, copy the wallet address after `profile/` in the URL

   ```
   https://polymarket.com/profile/0xABC123DEF456...
                                   ^^^^^^^^^^^^^^^^
                                   copy the wallet address
   ```

2. Run the script

   ```bash
   python3 scripts/polymarket_strategy_snapshot.py \
     --user 0xABC123DEF456... \
     --output snapshot.json
   ```

3. Done. Open `snapshot.json` or feed it to an AI for interpretation.

## What you get

| What | Example |
|---|---|
| Trading rhythm | How often they trade, what time of day |
| Market focus | Sports? Politics? Crypto? |
| Position exposure | How much money at risk, which direction |
| PnL | Are they making or losing money |
| Order book context | Spread, depth, liquidity around their positions |
| Execution style | Market orders vs limit orders, size patterns |

## Privacy

Wallet addresses are masked by default (`0x1234...abcd`). Your analysis is safe to share.

Want raw addresses? Add `--include-identifiers`.

## All options

| Option | Default | Description |
|---|---|---|
| `--user` | required | Target wallet address (0x...) |
| `--days` | all | Lookback window in days |
| `--limit` | 4000 | Max activity rows to fetch |
| `--top-slugs` | 10 | Markets to enrich with order books |
| `--timeout` | 20 | HTTP timeout in seconds |
| `--retries` | 3 | Retry attempts for transient errors |
| `--book-sleep-ms` | — | Sleep between order book calls (ms) |
| `--start-ts` | — | Start timestamp (UTC seconds) |
| `--end-ts` | — | End timestamp (UTC seconds) |
| `--include-identifiers` | off | Keep raw wallet addresses in output |
| `--output` | stdout | Output JSON file path |

## What this does NOT do

- **No trading** — doesn't place any orders
- **No copy-trade** — doesn't generate follow signals
- **No parameter packs** — doesn't output reproducible execution params
- **No private API** — all data from public endpoints

## As a Skill

This repo is a [Claude Skill](https://docs.anthropic.com/) that can be called directly by AI agents. `SKILL.md` defines the workflow, `agents/openai.yaml` defines the default prompt.

Feed a snapshot JSON to an AI and it will summarize: market focus, execution style, exposure, liquidity observations, and key risks.

## Requirements

- Python 3.8+
- No pip install needed

## Run tests

```bash
python3 -m unittest discover -s tests
```
