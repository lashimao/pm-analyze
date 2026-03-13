# PM-Analyze

一个 Claude Skill，帮你看懂任意 Polymarket 玩家在干什么。

## 怎么用

1. 打开你想分析的 Polymarket 用户主页，复制浏览器地址栏里的链接

   ```
   https://polymarket.com/profile/0xABC123DEF456...
   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   直接复制整个链接
   ```

2. 把链接丢给 AI，说"帮我分析这个钱包"，搞定。

## 你能看到什么

**这个人赚没赚钱**
- 总盈亏多少刀
- 胜率多高、平均每次赚多少 / 亏多少
- 最大回撤——从最高点跌了多少
- 最惨的一天亏了多少

**他在玩什么**
- 市场分类占比（体育 / 政治 / 加密 / AI 等）
- 最常玩的几个市场
- 是重仓一个市场还是雨露均沾

**他怎么玩的**
- 每天交易几笔、每笔下多少钱
- 两笔交易之间隔多久——秒级说明是机器人，小时级说明是人
- 有没有连续快速下单（2秒内连环出手）
- 连续亏损最多几笔

**他买得贵不贵（EV 分析）**
- 买入均价 vs 卖出均价的价差——能看出他有没有在吃亏成交
- 回转分析：同一个市场里买完再卖，每一笔赚还是亏、赢了多少比例
- 持仓时间分布：P50 / P75 / P90 分别持有多久才出手

**他现在手里有什么**
- 当前持仓总价值
- 押的哪边（Yes 还是 No）、有没有对冲
- 是全押一边还是两边都有

**他玩的市场流动性好不好**
- 价差大不大（买卖之间差多少）
- 盘口挂了多少钱
- 有没有套利空间

## 隐私

默认自动脱敏，钱包地址会被打码，分析结果可以直接分享给别人看。

## 不做什么

- **不下单** — 只看不动
- **不跟单** — 不会告诉你"跟着他买"
- **不依赖私有接口** — 所有数据来自公开 API

## 开发者信息

<details>
<summary>命令行用法（开发者点这里）</summary>

```bash
python3 scripts/polymarket_strategy_snapshot.py \
  --user https://polymarket.com/profile/0xABC123DEF456... \
  --output snapshot.json
```

### 全部参数

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

### 环境要求

- Python 3.8+
- 不需要装任何包

### 跑测试

```bash
python3 -m unittest discover -s tests
```

</details>

---

# English

A Claude Skill that lets you understand what any Polymarket player is doing.

## How to use

1. Go to any Polymarket profile page, copy the URL from your browser

   ```
   https://polymarket.com/profile/0xABC123DEF456...
   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   just copy the whole URL
   ```

2. Give the link to an AI and say "analyze this wallet". That's it.

## What you get

**Are they making money?**
- Total realized PnL
- Win rate, average gain / loss per trade
- Max drawdown — how far they fell from peak
- Worst single-day loss

**What are they trading?**
- Category breakdown (sports / politics / crypto / AI etc.)
- Their most active markets
- Concentrated or diversified?

**How do they trade?**
- Daily trade count, bet size per trade
- Time between trades — seconds = bot, hours = human
- Burst trading (rapid-fire orders within 2 seconds)
- Max consecutive losses

**Are they getting good prices? (EV signals)**
- Buy WAP vs sell WAP spread — are they consistently paying up or getting filled well?
- Round-trip win rate: for each market they traded both sides, how often did they profit?
- Hold time percentiles (P50 / P75 / P90) — how long before they exit

**What are they holding right now?**
- Current portfolio value
- Which side (Yes / No), hedged or not
- One-sided or balanced positions

**How liquid are their markets?**
- Bid-ask spread
- Order book depth
- Arbitrage margin available

## Privacy

Wallet addresses are masked by default. Analysis results are safe to share.

## What this does NOT do

- **No trading** — read-only
- **No copy-trade** — won't tell you to "follow this guy"
- **No private API** — all data from public endpoints

## For developers

<details>
<summary>CLI usage (click to expand)</summary>

```bash
python3 scripts/polymarket_strategy_snapshot.py \
  --user https://polymarket.com/profile/0xABC123DEF456... \
  --output snapshot.json
```

### All options

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

### Requirements

- Python 3.8+
- No pip install needed

### Run tests

```bash
python3 -m unittest discover -s tests
```

</details>
