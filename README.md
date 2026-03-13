# PM-Analyze

Analyze any Polymarket wallet in one command. No API key, no dependencies, just Python.

## How it works

1. Go to any Polymarket profile page, copy the wallet address from the URL

   ```
   https://polymarket.com/profile/0xABC123...
                                   ^^^^^^^^^^^ copy this
   ```

2. Run the script

   ```bash
   python3 scripts/polymarket_strategy_snapshot.py \
     --user 0xABC123... \
     --output snapshot.json
   ```

3. Done. Open `snapshot.json` to see the full analysis.

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

## Advanced options

```bash
python3 scripts/polymarket_strategy_snapshot.py \
  --user 0xABC123... \
  --days 14 \          # lookback window, default 30
  --limit 20000 \      # max rows to fetch
  --top-slugs 12 \     # how many markets to deep-dive
  --output snapshot.json
```

## What this does NOT do

- **No trading** — doesn't place any orders
- **No copy-trade** — doesn't generate follow signals
- **No private API** — all data from public endpoints

## Repo layout

```
scripts/polymarket_strategy_snapshot.py   ← main script
agents/openai.yaml                        ← default prompt for AI analysis
tests/test_public_snapshot.py             ← unit tests
SKILL.md                                  ← workflow docs
```

## Requirements

- Python 3.8+
- No pip install needed

## Run tests

```bash
python3 -m unittest discover -s tests
```

---

# PM-Analyze 中文说明

一条命令分析任意 Polymarket 钱包。不需要 API Key，不需要装依赖，有 Python 就行。

## 怎么用

1. 打开任意 Polymarket 用户主页，从 URL 里复制钱包地址

   ```
   https://polymarket.com/profile/0xABC123...
                                   ^^^^^^^^^^^ 复制这个
   ```

2. 跑脚本

   ```bash
   python3 scripts/polymarket_strategy_snapshot.py \
     --user 0xABC123... \
     --output snapshot.json
   ```

3. 搞定。打开 `snapshot.json` 看结果。

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

## 进阶参数

```bash
python3 scripts/polymarket_strategy_snapshot.py \
  --user 0xABC123... \
  --days 14 \          # 回看天数，默认30
  --limit 20000 \      # 最多拉多少条数据
  --top-slugs 12 \     # 深入分析几个市场
  --output snapshot.json
```

## 不做什么

- **不下单** — 纯分析，不会替你交易
- **不跟单** — 不生成任何跟单信号
- **不依赖私有接口** — 所有数据来自公开 API

## 环境要求

- Python 3.8+
- 不需要装任何包

## 跑测试

```bash
python3 -m unittest discover -s tests
```
