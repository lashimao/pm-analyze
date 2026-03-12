# pm-analyze

Public-safe Polymarket wallet analysis.

This repository packages a small, dependency-light skill for pulling public Polymarket activity and turning it into a clean JSON snapshot for descriptive analysis. It is designed for sharing research publicly without defaulting to raw wallet identifiers, copy-trade instructions, or reverse-engineered parameter packs.

## What This Does

- Pulls public activity, positions, event metadata, and order-book context for a target wallet
- Produces a structured JSON snapshot with timing, exposure, market concentration, and liquidity signals
- Defaults to redacting wallet identifiers in output metadata and error URLs
- Leaves the interpretation layer to the reader or model

## What This Does Not Do

- It does not place trades
- It does not generate copy-trade rules
- It does not output reproducible execution parameters
- It does not claim private or internal Polymarket access

## Repo Layout

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

## Quick Start

Python standard library is enough. No third-party packages are required.

```bash
python3 scripts/polymarket_strategy_snapshot.py \
  --user 0xYOUR_WALLET_ADDRESS \
  --days 14 \
  --limit 20000 \
  --top-slugs 12 \
  --output /tmp/polymarket_strategy_snapshot.json
```

## Privacy Defaults

By default, the script redacts identifiers in the output:

- `meta.user` becomes a masked value such as `0x1234...abcd`
- error entries keep the endpoint shape but mask `user`, `wallet`, and `address` query parameters

If you explicitly want raw identifiers in the output, add:

```bash
--include-identifiers
```

## Output Shape

The generated JSON is organized for public-facing review:

- `meta`: generation info, window, fetched row counts, redaction flag
- `activity_signals`: cadence, side mix, market concentration, trade frequency
- `position_signals`: inventory skew, value, PnL, paired coverage
- `ev_signals`: descriptive trade quality and round-trip indicators
- `official_market_profile`: category and tag coverage from public market metadata
- `slug_market_profile`: slug-based fallback categorization
- `orderbook_signals`: spread, depth, and simple pair-level book checks
- `market_snapshots`: top-slug enrichment with market metadata and books
- `null_audit`: visibility into missing fields
- `errors`: fetch failures with public-safe endpoint logging

## Example

```json
{
  "meta": {
    "user": "0x1111...1111",
    "identifiers_redacted": true
  }
}
```

## Public-Facing Use Cases

- Research writeups about public wallet behavior
- Bot-style execution pattern summaries
- Market-focus and exposure overviews
- Internal note-taking where raw wallet identifiers should stay out of shared artifacts

## Development

Run the built-in tests:

```bash
python3 -m unittest discover -s tests
```

## Notes

- The data comes from public Polymarket endpoints and can change over time
- Some legacy markets may have partial metadata coverage
- Public order-book snapshots show current executable context, not historical fills

## Related Files

- `SKILL.md` contains the skill-facing workflow and output framing
- `agents/openai.yaml` contains the default assistant prompt for this public version
