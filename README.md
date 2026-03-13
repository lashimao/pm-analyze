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

## 怎么用来赚钱

Polymarket 是公开的，所有人的交易记录都能查。

**找高手学套路：** 去 [Polymarket 排行榜](https://polymarket.com/leaderboard) 找长期盈利的玩家，把他们的主页链接丢进来分析——他们专注哪类市场、下注节奏是什么、每笔多大，你自己对比着想。

**验钱包真假：** 有人推荐一个"稳赚"的钱包截图？先分析一下，看看他的胜率、回撤、真实盈亏，别被精选截图骗了。

**分析自己：** 把自己的主页链接丢进来，看看你亏在哪——是买太贵、持仓时间不对、还是市场选错了。

**用 EV 分辨运气和实力（核心）：** 光看盈亏骗不了你，但 EV 骗不了人。

- **买入均价 vs 卖出均价**：真正有优势的玩家，买进去的价格比最终结算便宜得多。如果一个人赢了很多但买入均价很高，大概率是运气，不是判断力。
- **回转胜率**：在同一个市场里来回交易，赢的比例有多高。稳定高于 60% 说明他在这个市场有真实 edge，低于 50% 说明他在瞎猜。
- **持仓时间**：秒级出手 = 程序化套利；天级持有 = 主观判断。两种模式都能赚钱，但逻辑完全不同，别把程序员当选手学。

**策略核心：** 赚钱的人通常有以下几个共同特征，通过分析可以验证。

- **专注 > 分散**：集中度指数（HHI）高的玩家，往往在某个领域有真实信息优势。雨露均沾的玩家大多在猜——他不可能对所有市场都比市场更聪明。
- **流动性差的市场机会更多**：价差大、盘口浅的市场，定价错误更多。好的玩家倾向于在流动性差的市场建仓，而不是跟大家抢热门市场。
- **套利信号**：Yes 价 + No 价 < $1，说明市场定价出了问题。这种机会短暂，出现就是纯 EV，分析里会直接标出来。
- **下注大小有规律的人更危险**：固定下注 = 没有仓位管理；下注大小随市场波动 = 有主观判断在里面。前者靠运，后者靠功。

**怎么从分析结果里提取一个人的策略核心：**

找到一个长期盈利的钱包之后，按这个顺序读输出结果：

1. **看 `dominant_category` + HHI**：他主攻什么领域、有多集中。HHI > 0.4 说明高度专注，这个领域可能是他的主场。
2. **看 `top_slugs_by_trades`**：他最常交易的具体市场名称——这就是他的狩猎场，也是你值得重点关注的市场。
3. **看 `buy_sell_wap_spread`**：他的买入均价比卖出均价低多少。正数说明他系统性地买在低位，这种人有定价判断力。
4. **看 `roundtrip_positive_ratio`**：他在每个市场里的回转胜率。找出胜率最高的几个市场——那是他真正有 edge 的地方，不是他运气好的地方。
5. **看 `hold_sec_p50`**：中位持仓时间。几十秒 = 程序化，几小时到几天 = 主观判断。决定了你能不能跟着学。

这五个数字组合起来，就是一个人的策略核心：**在哪打、打什么价位、拿多久**。

---

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

## How to use this to make money

Polymarket is public — anyone's trade history is queryable.

**Learn from top traders:** Go to the [Polymarket leaderboard](https://polymarket.com/leaderboard), find consistently profitable wallets, and analyze them — what markets do they focus on, how often do they trade, how big are their bets. Use it as research, not copying.

**Verify "alpha" claims:** Someone sharing a screenshot of a "guaranteed winner" wallet? Run it through here first. Check their real win rate, drawdown, and PnL before trusting a cherry-picked screenshot.

**Audit yourself:** Paste your own profile link and see where you're bleeding — are you overpaying, holding too long, or picking the wrong markets?

**Use EV to separate skill from luck (the core):** Raw PnL is easy to fake with one lucky bet. EV signals are harder to fake.

- **Buy WAP vs sell WAP:** A trader with real edge consistently buys below the eventual resolution price. High PnL but high buy WAP = probably luck, not judgment.
- **Round-trip win rate:** For markets they traded both sides of, how often did they profit? Consistently above 60% = real edge in that market. Below 50% = guessing.
- **Hold time:** Seconds = programmatic arbitrage. Days = discretionary judgment. Both can be profitable, but they're completely different games — don't try to copy a bot's market selection with a human's timing.

**Strategy core:** Profitable traders tend to share a few patterns that show up in the signals.

- **Specialization > diversification:** High HHI (concentration) means they focus on a specific domain where they have real information edge. Spread-thin traders are mostly guessing — nobody has an edge in every market simultaneously.
- **Illiquid markets have more opportunity:** Wide spreads and shallow books mean more mispricing. Good traders build positions in low-liquidity markets rather than fighting over well-priced ones.
- **Arbitrage signals:** Yes price + No price < $1 means the market is mispriced. Pure EV when it appears — the analysis flags these directly.
- **Variable bet sizing matters:** Fixed bet size = no position management, running on luck. Bet size that varies with conviction = there's actual judgment behind the trades.

**How to extract someone's strategy core from the output:**

Once you find a consistently profitable wallet, read the output in this order:

1. **`dominant_category` + HHI** — what domain they specialize in and how focused they are. HHI > 0.4 = highly concentrated, this is probably their home turf.
2. **`top_slugs_by_trades`** — the specific markets they trade most. This is their hunting ground, and where you should be paying attention.
3. **`buy_sell_wap_spread`** — how much cheaper their buys are vs their sells. Positive = they systematically buy low. This is the fingerprint of real pricing judgment.
4. **`roundtrip_positive_ratio` per market** — where their round-trip win rate is highest. Those are the markets where they have actual edge, not just luck.
5. **`hold_sec_p50`** — median hold time. Tens of seconds = programmatic. Hours to days = discretionary. Determines whether their style is learnable.

These five numbers together define a trader's strategy core: **where they play, at what price, and for how long.**

---

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
