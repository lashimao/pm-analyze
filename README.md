# PM-Analyze

Analyze any Polymarket wallet in one command. No API key, no dependencies, just Python.

一条命令分析任意 Polymarket 钱包。不需要 API Key，不需要装依赖，只要有 Python 就行。

## How it works / 怎么用

1. Go to any Polymarket profile page, copy the wallet address from the URL

   打开任意 Polymarket 用户主页，从 URL 里复制钱包地址

   ```
   https://polymarket.com/profile/0xABC123...
                                   ^^^^^^^^^^^ copy this / 复制这个
   ```

2. Run the script / 运行脚本

   ```bash
   python3 scripts/polymarket_strategy_snapshot.py \
     --user 0xABC123... \
     --output snapshot.json
   ```

3. Done. Open `snapshot.json` to see the full analysis.

   搞定。打开 `snapshot.json` 就能看到完整分析结果。

## What you get / 你能看到什么

| What / 内容 | Example / 举例 |
|---|---|
| Trading rhythm / 交易节奏 | How often they trade, what time of day / 多久交一次，什么时间段活跃 |
| Market focus / 市场偏好 | Sports? Politics? Crypto? / 玩体育？政治？加密？ |
| Position exposure / 持仓暴露 | How much money at risk, which direction / 押了多少钱，押的哪边 |
| PnL / 盈亏 | Are they making or losing money / 赚了还是亏了 |
| Order book context / 盘口上下文 | Spread, depth, liquidity around their positions / 他们持仓附近的价差、深度、流动性 |
| Execution style / 执行风格 | Market orders vs limit orders, size patterns / 市价单还是限价单，下单大小规律 |

## Privacy / 隐私

By default, wallet addresses are masked in the output (`0x1234...abcd`). Your analysis is safe to share.

默认自动脱敏，输出里的钱包地址会被打码成 `0x1234...abcd`，分析结果可以直接分享。

Want raw addresses? Add `--include-identifiers`.

需要保留原始地址？加 `--include-identifiers`。

## Advanced options / 进阶参数

```bash
python3 scripts/polymarket_strategy_snapshot.py \
  --user 0xABC123... \
  --days 14 \          # lookback window, default 30 / 回看天数，默认30
  --limit 20000 \      # max rows to fetch / 最多拉多少条数据
  --top-slugs 12 \     # how many markets to deep-dive / 深入分析几个市场
  --output snapshot.json
```

## What this does NOT do / 不做什么

- **No trading** — it doesn't place any orders / 不会下单
- **No copy-trade** — it doesn't generate follow signals / 不会生成跟单信号
- **No private API** — all data comes from public endpoints / 所有数据来自公开接口

## Repo layout / 仓库结构

```
scripts/polymarket_strategy_snapshot.py   ← the main script / 主脚本
agents/openai.yaml                        ← default prompt for AI analysis / AI 分析默认提示词
tests/test_public_snapshot.py             ← unit tests / 单元测试
SKILL.md                                  ← workflow docs / 工作流文档
```

## Requirements / 环境要求

- Python 3.8+
- No pip install needed / 不需要装任何包

## Run tests / 跑测试

```bash
python3 -m unittest discover -s tests
```

## Notes / 注意

- Data comes from public Polymarket endpoints, may change over time / 数据来自公开接口，可能随时间变化
- Some older markets may have incomplete metadata / 部分老市场元数据不完整
- Order book snapshots show current state, not historical fills / 订单簿是当前状态，不是历史成交
