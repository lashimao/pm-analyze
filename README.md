# PM-Analyze

一个 Claude Skill，用来分析任意 Polymarket 钱包的公开数据。不需要 API Key，不需要装依赖，有 Python 就行。

## 怎么用

1. 打开任意 Polymarket 用户主页，复制浏览器地址栏里的链接

   ```
   https://polymarket.com/profile/0xABC123DEF456...
   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   直接复制整个链接
   ```

2. 跑脚本，把链接贴进去

   ```bash
   python3 scripts/polymarket_strategy_snapshot.py \
     --user https://polymarket.com/profile/0xABC123DEF456... \
     --output snapshot.json
   ```

3. 搞定。打开 `snapshot.json` 看结果，或者丢给 AI 让它帮你解读。

## 你能看到什么

**交易行为**
- 总共交了多少笔、每天平均几笔
- 每笔下注多少钱（中位数、最大、最小）
- 两笔交易之间隔多久（能看出是人还是机器人）
- 连续亏损最多几笔

**赚没赚钱**
- 已实现盈亏（FIFO 匹配每一笔买卖算出来的）
- 胜率、平均赚多少 / 亏多少
- 最大回撤（从最高点跌了多少）
- 每天盈亏曲线里最差的一天亏了多少

**在玩什么市场**
- 市场分类占比（体育 / 政治 / 加密 / AI 等）
- 玩得最多的几个市场名称和交易次数
- 是集中押一个市场还是分散下注（HHI 集中度）

**持仓情况**
- 当前持仓总价值
- 押了哪边（Yes/No）、有没有对冲
- 库存偏斜度（全押一边 vs 两边都有）

**盘口环境**
- 他押的那些市场，价差大不大（流动性好不好）
- 盘口深度（挂了多少钱）
- 有没有套利空间（Yes+No 价格之和 < 1）

**执行风格**
- 买卖比例、Yes/No 比例
- 持仓时间分布（秒级 = 机器人，天级 = 长线）
- 有没有连续快速下单的 burst 行为（2秒内连续交易的比例）

## 隐私

默认自动脱敏，钱包地址会被打码成 `0x1234...abcd`，分析结果可以直接分享。

需要原始地址？加 `--include-identifiers`。

## 全部参数

| 参数 | 默认值 | 说明 |
|---|---|---|
| `--user` | 必填 | Polymarket 主页链接或钱包地址 |
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

1. Go to any Polymarket profile page, copy the URL from your browser

   ```
   https://polymarket.com/profile/0xABC123DEF456...
   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   just copy the whole URL
   ```

2. Run the script, paste the URL

   ```bash
   python3 scripts/polymarket_strategy_snapshot.py \
     --user https://polymarket.com/profile/0xABC123DEF456... \
     --output snapshot.json
   ```

3. Done. Open `snapshot.json` or feed it to an AI for interpretation.

## What you get

**Trading behavior**
- Total trades, daily average, notional size distribution
- Time between trades (spot bots vs humans)
- Max consecutive losses

**Profitability**
- FIFO-matched realized PnL per round-trip
- Win rate, average gain / loss
- Max drawdown (peak-to-trough)
- Worst single-day PnL

**Market focus**
- Category breakdown (sports / politics / crypto / AI etc.)
- Top markets by trade count
- Concentration index (HHI — are they diversified or all-in?)

**Position snapshot**
- Current portfolio value
- Which side (Yes / No), hedged or not
- Inventory skew (one-sided vs balanced)

**Order book context**
- Spread and depth around their active markets
- Top-level liquidity
- Arbitrage margin (Yes + No best ask < 1.0?)

**Execution style**
- Buy/sell ratio, Yes/No ratio
- Hold time distribution (seconds = bot, days = long-term)
- Burst trading ratio (trades within 2s of each other)

## Privacy

Wallet addresses are masked by default (`0x1234...abcd`). Your analysis is safe to share.

Want raw addresses? Add `--include-identifiers`.

## All options

| Option | Default | Description |
|---|---|---|
| `--user` | required | Polymarket profile URL or wallet address |
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
