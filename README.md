# pm-analyze

Public-safe Polymarket wallet analysis.  
面向公开分享的 Polymarket 钱包分析工具。

## Overview / 项目简介

This repository packages a small, dependency-light skill for pulling public Polymarket activity and turning it into a clean JSON snapshot for descriptive analysis. It is built for public research sharing without defaulting to raw wallet identifiers, copy-trade instructions, or reverse-engineered parameter packs.

这个仓库打包了一套轻量、几乎零依赖的 Polymarket 公共分析工具，用来拉取公开活动数据，并整理成适合描述性分析的 JSON 快照。它面向公开研究分享，默认不暴露原始钱包地址，也不输出复制交易指令或参数包。

## What This Does / 这个项目做什么

- Pulls public activity, positions, event metadata, and order-book context for a target wallet  
  拉取目标钱包的公开成交、持仓、事件元数据和订单簿上下文
- Produces a structured JSON snapshot with timing, exposure, market concentration, and liquidity signals  
  生成结构化 JSON，覆盖节奏、风险暴露、市场集中度和流动性信号
- Redacts wallet identifiers in output metadata and error URLs by default  
  默认对输出里的钱包标识和报错链接做脱敏
- Leaves the interpretation layer to the reader or model  
  只负责数据和信号整理，把解读留给读者或模型

## What This Does Not Do / 这个项目不做什么

- It does not place trades  
  不下单
- It does not generate copy-trade rules  
  不生成跟单规则
- It does not output reproducible execution parameters  
  不输出可复现执行参数
- It does not claim private or internal Polymarket access  
  不依赖私有或内部接口

## Repo Layout / 仓库结构

```text
.
├── README.md
├── SKILL.md
├── agents/
│   └── openai.yaml
├── scripts/
│   └── polymarket_strategy_snapshot.py
└── tests/
    └── test_public_snapshot.py
```

## Quick Start / 快速开始

Python standard library is enough. No third-party packages are required.  
只需要 Python 标准库，不依赖第三方包。

```bash
python3 scripts/polymarket_strategy_snapshot.py \
  --user 0xYOUR_WALLET_ADDRESS \
  --days 14 \
  --limit 20000 \
  --top-slugs 12 \
  --output /tmp/polymarket_strategy_snapshot.json
```

## Privacy Defaults / 隐私默认值

By default, the script redacts identifiers in the output.  
脚本默认会对输出里的身份信息打码。

- `meta.user` becomes a masked value such as `0x1234...abcd`  
  `meta.user` 会被写成类似 `0x1234...abcd` 的形式
- Error entries keep the endpoint shape but mask `user`, `wallet`, and `address` query parameters  
  报错记录会保留接口结构，但会打码 `user`、`wallet`、`address` 这些查询参数

If you explicitly want raw identifiers in the output, add:  
如果你明确需要在输出里保留原始地址，可以加这个开关：

```bash
--include-identifiers
```

## Output Shape / 输出结构

The generated JSON is organized for public-facing review.  
生成的 JSON 结构面向公开复盘和分享。

- `meta`: generation info, window, fetched row counts, redaction flag  
  `meta`：生成时间、时间窗口、抓取行数、脱敏标记
- `activity_signals`: cadence, side mix, market concentration, trade frequency  
  `activity_signals`：交易节奏、方向分布、市场集中度、交易频率
- `position_signals`: inventory skew, value, PnL, paired coverage  
  `position_signals`：库存偏斜、头寸价值、PnL、双边覆盖情况
- `ev_signals`: descriptive trade quality and round-trip indicators  
  `ev_signals`：描述性的成交质量和回转指标
- `official_market_profile`: category and tag coverage from public market metadata  
  `official_market_profile`：来自公开市场元数据的分类和标签覆盖
- `slug_market_profile`: slug-based fallback categorization  
  `slug_market_profile`：基于 slug 的兜底分类
- `orderbook_signals`: spread, depth, and simple pair-level book checks  
  `orderbook_signals`：价差、深度和简单的盘口配对检查
- `market_snapshots`: top-slug enrichment with market metadata and books  
  `market_snapshots`：对重点 slug 做的元数据和订单簿补充
- `null_audit`: visibility into missing fields  
  `null_audit`：空值可见性检查
- `errors`: fetch failures with public-safe endpoint logging  
  `errors`：带脱敏接口记录的抓取错误

## Example / 示例

```json
{
  "meta": {
    "user": "0x1111...1111",
    "identifiers_redacted": true
  }
}
```

## Public-Facing Use Cases / 适合公开使用的场景

- Research writeups about public wallet behavior  
  对公开钱包行为做研究型写作
- Bot-style execution pattern summaries  
  总结机器人式执行特征
- Market-focus and exposure overviews  
  做市场偏好和风险暴露概览
- Internal notes where raw wallet identifiers should stay out of shared artifacts  
  内部复盘时避免把原始地址带进共享文档

## Development / 开发

Run the built-in tests:  
运行内置测试：

```bash
python3 -m unittest discover -s tests
```

## Notes / 说明

- The data comes from public Polymarket endpoints and can change over time  
  数据来自 Polymarket 的公开接口，随时间可能变化
- Some legacy markets may have partial metadata coverage  
  一些老市场的元数据覆盖可能不完整
- Public order-book snapshots show current executable context, not historical fills  
  公开订单簿快照展示的是当前可成交上下文，不是历史成交回放

## Related Files / 相关文件

- `SKILL.md` contains the skill-facing workflow and output framing  
  `SKILL.md` 里是给 skill 本身看的工作流说明
- `agents/openai.yaml` contains the default assistant prompt for this public version  
  `agents/openai.yaml` 里是这份公开版默认提示词
