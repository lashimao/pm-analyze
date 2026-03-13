# PM-Analyze

Polymarket 钱包公开数据分析工具，零依赖，只用 Python 标准库。

## 这个项目做什么

- 拉取目标钱包的公开成交、持仓、事件元数据和订单簿上下文
- 生成结构化 JSON 快照，覆盖交易节奏、风险暴露、市场集中度和流动性信号
- 默认脱敏钱包地址（输出里不暴露原始标识）
- 只负责数据整理，解读留给你

## 不做什么

- 不下单、不跟单、不输出可复现的执行参数
- 不依赖任何私有或内部接口

## 仓库结构

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

## 快速开始

```bash
python3 scripts/polymarket_strategy_snapshot.py \
  --user 0xYOUR_WALLET_ADDRESS \
  --days 14 \
  --limit 20000 \
  --top-slugs 12 \
  --output /tmp/polymarket_strategy_snapshot.json
```

## 隐私默认值

脚本默认对输出里的身份信息打码：

- `meta.user` → `0x1234...abcd`
- 报错记录保留接口结构，但 `user`、`wallet`、`address` 参数会被遮蔽

如果需要保留原始地址，加 `--include-identifiers`。

## 输出结构

生成的 JSON 主要包含：

| 字段 | 说明 |
|------|------|
| `meta` | 生成时间、时间窗口、抓取行数、脱敏标记 |
| `activity_signals` | 交易节奏、方向分布、市场集中度 |
| `position_signals` | 库存偏斜、头寸价值、PnL、双边覆盖 |
| `ev_signals` | 成交质量和回转指标 |
| `official_market_profile` | 公开市场元数据的分类和标签覆盖 |
| `slug_market_profile` | 基于 slug 的兜底分类 |
| `orderbook_signals` | 价差、深度、盘口配对检查 |
| `market_snapshots` | 重点 slug 的元数据和订单簿补充 |
| `null_audit` | 空值检查 |
| `errors` | 带脱敏接口记录的抓取错误 |

## 适用场景

- 公开钱包行为的研究型写作
- 机器人执行模式分析
- 市场偏好和风险暴露概览
- 内部复盘时避免原始地址泄露

## 开发

```bash
python3 -m unittest discover -s tests
```

## 说明

- 数据来自 Polymarket 公开接口，随时间可能变化
- 部分老市场元数据覆盖不完整
- 订单簿快照是当前可成交状态，不是历史成交回放
