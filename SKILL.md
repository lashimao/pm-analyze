---
name: polymarket-public-analysis
description: Fetch a public Polymarket wallet's activity, positions, and order-book context, then summarize behavior, exposure, and market focus from a JSON snapshot. Use when analyzing a public wallet or bot without generating copy-trade instructions or reverse-engineered parameter packs.
---

# Polymarket Public Analysis

## Scope

```
脚本 = 公共数据抓取 + 描述性统计
AI   = 行为总结 / 风险提示 / 市场画像 / 执行风格观察
```

公开版默认不输出复制交易建议、可复现信号、参数包、HFT 推导。
输出中的钱包地址和错误链接默认脱敏；只有显式加 `--include-identifiers` 才会保留原值。

## Quick Start

```bash
python3 scripts/polymarket_strategy_snapshot.py \
  --user 0xYOUR_WALLET_ADDRESS \
  --days 14 \
  --limit 20000 \
  --top-slugs 12 \
  --output /tmp/polymarket_strategy_snapshot.json
```

## Workflow

### Step 1: 运行脚本获取公开快照

脚本输出纯数据 JSON，核心结构如下：

```
meta                    → 抓取元信息（默认已脱敏）
activity_signals        → 交易活动统计（频率/节奏/方向/集中度）
position_signals        → 持仓统计（库存偏斜/PnL/覆盖度）
ev_signals              → 描述性成交因子（WAP/roundtrip/FIFO/持仓时长）
orderbook_signals       → 订单簿深度/价差/可成交性
official_market_profile → 官方分类覆盖
slug_market_profile     → slug 文本分类（推断）
market_snapshots        → 每个 top slug 的详细市场快照
null_audit              → 空值审计
errors                  → 抓取错误记录
```

### Step 2: AI 读取 JSON 分析

AI 读取输出 JSON 后，做公开版友好的解读：

1. **总体画像**：主要做什么市场、偏高频还是偏离散、偏库存还是偏配对
2. **行为节奏**：交易频率、爆发式下单、持仓时长、回转倾向
3. **风险暴露**：库存偏斜、PnL 分布、双边覆盖情况
4. **流动性观察**：订单簿深度、价差、可成交性
5. **注意事项**：数据盲区、指标偏差、过度解读风险

### Step 3: AI 输出报告

输出面向公开分享的行为分析，不给“怎么抄”。

## 核心接口

1. `GET https://data-api.polymarket.com/activity`
   - 参数：`user`(必填), `limit`, `offset`, `start`, `end`
   - 用途：交易行为、节奏、方向、回转分析

2. `GET https://data-api.polymarket.com/positions`
   - 参数：`user`(必填), `limit`, `offset`
   - 用途：持仓结构、库存偏斜、PnL

3. `GET https://gamma-api.polymarket.com/events`
   - 参数：`slug`
   - 用途：从 slug 获取 market 元数据

4. `GET https://gamma-api.polymarket.com/markets`
   - 参数：`slug`, `active`, `closed`, `limit`
   - 用途：events 查不到时兜底

5. `GET https://clob.polymarket.com/book`
   - 参数：`token_id`
   - 用途：真实可成交价和深度

## 建议输出结构

1. **一句话摘要**
2. **主要市场与主题**
3. **执行节奏与交易风格**
4. **库存、回转与风险暴露**
5. **流动性与定价观察**
6. **局限性与误判风险**

## Resources

- `scripts/polymarket_strategy_snapshot.py`: 公共数据抓取与基础统计脚本。
