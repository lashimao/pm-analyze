#!/usr/bin/env python3
"""Create a public-safe Polymarket activity snapshot for descriptive analysis."""

from __future__ import annotations

import argparse
import json
import math
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from typing import Any

DATA_API = "https://data-api.polymarket.com"
GAMMA_API = "https://gamma-api.polymarket.com"
CLOB_API = "https://clob.polymarket.com"
ACTIVITY_PAGE_SIZE = 1000
POSITIONS_PAGE_SIZE = 500
ACTIVITY_MAX_OFFSET = 3000
ACTIVITY_WINDOW_ROW_CAP = 4000

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Referer": "https://polymarket.com/",
}
REDACT_IDENTIFIERS = True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch Polymarket activity/positions/market books and compute descriptive signals."
    )
    parser.add_argument("--user", required=True, help="Target wallet address (0x...).")
    parser.add_argument(
        "--limit",
        type=int,
        default=4000,
        help="Target activity rows. With --days/--start-ts, script may exceed this to fully cover the time window.",
    )
    parser.add_argument(
        "--days",
        type=int,
        help="Optional lookback window in days. If provided, activity uses [end-days, end].",
    )
    parser.add_argument(
        "--start-ts",
        type=int,
        help="Optional hard start timestamp (UTC seconds). Rows older than this are excluded.",
    )
    parser.add_argument(
        "--end-ts",
        type=int,
        help="Optional activity end timestamp (UTC seconds).",
    )
    parser.add_argument("--top-slugs", type=int, default=10, help="How many active slugs to enrich with books.")
    parser.add_argument("--timeout", type=int, default=20, help="HTTP timeout in seconds.")
    parser.add_argument("--retries", type=int, default=3, help="Retry attempts for transient errors.")
    parser.add_argument(
        "--book-sleep-ms",
        type=int,
        default=50,
        help="Sleep between order book calls in milliseconds.",
    )
    parser.add_argument(
        "--include-identifiers",
        action="store_true",
        help="Include the raw wallet address in output metadata and error URLs. Default keeps them redacted.",
    )
    parser.add_argument("--output", help="Optional output JSON file.")
    return parser.parse_args()


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def looks_like_evm_address(value: Any) -> bool:
    if not isinstance(value, str) or not value.startswith("0x") or len(value) != 42:
        return False
    return all(ch in "0123456789abcdefABCDEF" for ch in value[2:])


def mask_address(value: Any) -> Any:
    if not looks_like_evm_address(value):
        return value
    return f"{value[:6]}...{value[-4:]}"


def redact_query_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    if not parsed.query:
        return url
    masked_pairs = []
    for key, value in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True):
        if key.lower() in {"user", "address", "wallet"}:
            masked_pairs.append((key, mask_address(value)))
        else:
            masked_pairs.append((key, value))
    query = urllib.parse.urlencode(masked_pairs, doseq=True)
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, query, parsed.fragment))


def sanitize_endpoint(url: str) -> str:
    if REDACT_IDENTIFIERS:
        return redact_query_url(url)
    return url


def build_error_entry(url: str, error: str) -> dict[str, str]:
    return {"endpoint": sanitize_endpoint(url), "error": error}


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def to_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def parse_maybe_json_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        if text.startswith("["):
            try:
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                return []
    return []


def normalize_outcome(value: Any, index_value: Any = None) -> str:
    if value is None and index_value is None:
        return "UNKNOWN"
    if isinstance(value, str):
        upper = value.strip().upper()
        if upper in {"UP", "YES"}:
            return "UP"
        if upper in {"DOWN", "NO"}:
            return "DOWN"
        if upper:
            return upper
    idx = to_int(index_value)
    if idx == 0:
        return "UP"
    if idx == 1:
        return "DOWN"
    return "UNKNOWN"


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * q
    low = math.floor(pos)
    high = math.ceil(pos)
    if low == high:
        return ordered[low]
    left = ordered[low] * (high - pos)
    right = ordered[high] * (pos - low)
    return left + right


def safe_fetch_json(
    base_url: str,
    path: str,
    params: dict[str, Any] | None,
    timeout: int,
    retries: int,
) -> tuple[Any | None, str | None, str]:
    query = urllib.parse.urlencode(params or {}, doseq=True)
    url = f"{base_url}{path}"
    if query:
        url = f"{url}?{query}"

    for attempt in range(retries):
        request = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = response.read().decode("utf-8")
            return json.loads(payload), None, url
        except urllib.error.HTTPError as exc:
            reason = f"HTTP {exc.code}"
            if exc.reason:
                reason = f"{reason} {exc.reason}"
            if exc.code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                time.sleep(0.6 * (2**attempt))
                continue
            return None, reason, url
        except urllib.error.URLError as exc:
            if attempt < retries - 1:
                time.sleep(0.6 * (2**attempt))
                continue
            return None, f"URLError {exc.reason}", url
        except json.JSONDecodeError:
            return None, "JSONDecodeError", url
        except TimeoutError:
            if attempt < retries - 1:
                time.sleep(0.6 * (2**attempt))
                continue
            return None, "TimeoutError", url
    return None, "UnknownError", url


def fetch_user_rows_paginated(
    path: str,
    user: str,
    total_limit: int,
    page_size: int,
    timeout: int,
    retries: int,
    extra_params: dict[str, Any] | None = None,
    max_offset: int | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    offset = 0

    while len(rows) < total_limit:
        if max_offset is not None and offset > max_offset:
            break
        batch_limit = min(page_size, total_limit - len(rows))
        params = {
            "user": user,
            "limit": batch_limit,
            "offset": offset,
        }
        if extra_params:
            params.update(extra_params)
        payload, error, url = safe_fetch_json(
            DATA_API,
            path,
            params,
            timeout=timeout,
            retries=retries,
        )
        if error:
            # data-api activity usually returns 400 when offset exceeds available rows.
            if offset > 0 and path == "/activity" and error.startswith("HTTP 400"):
                break
            errors.append(build_error_entry(url, error))
            break
        if not isinstance(payload, list):
            errors.append(build_error_entry(url, "Invalid payload"))
            break
        if not payload:
            break

        rows.extend(payload)
        offset += len(payload)
        if len(payload) < batch_limit:
            break

    return rows, errors


def dedupe_activity_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique_rows: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()

    for row in rows:
        row_id = row.get("id")
        if row_id is not None:
            key = ("id", row_id)
        else:
            key = (
                "raw",
                row.get("timestamp"),
                row.get("asset"),
                row.get("side"),
                row.get("price"),
                row.get("size"),
                row.get("slug"),
                row.get("type"),
            )
        if key in seen:
            continue
        seen.add(key)
        unique_rows.append(row)

    return unique_rows


def fetch_activity_rows_windowed(
    user: str,
    total_limit: int,
    timeout: int,
    retries: int,
    start_ts: int | None = None,
    end_ts: int | None = None,
    coverage_floor_ts: int | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, str]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    windows: list[dict[str, Any]] = []
    current_end = end_ts
    window_index = 0
    reached_coverage = coverage_floor_ts is None

    while True:
        need_more_rows = len(rows) < total_limit
        need_more_coverage = not reached_coverage
        if not need_more_rows and not need_more_coverage:
            break

        window_index += 1
        remaining = max(0, total_limit - len(rows))
        if remaining > 0:
            window_limit = min(ACTIVITY_WINDOW_ROW_CAP, remaining)
        else:
            window_limit = ACTIVITY_WINDOW_ROW_CAP
        window_params: dict[str, Any] = {}
        if start_ts is not None:
            window_params["start"] = start_ts
        if current_end is not None:
            window_params["end"] = current_end

        batch_rows, batch_errors = fetch_user_rows_paginated(
            path="/activity",
            user=user,
            total_limit=window_limit,
            page_size=ACTIVITY_PAGE_SIZE,
            timeout=timeout,
            retries=retries,
            extra_params=window_params,
            max_offset=ACTIVITY_MAX_OFFSET,
        )
        errors.extend(batch_errors)
        if not batch_rows:
            break

        unique_batch = dedupe_activity_rows(batch_rows)
        existing = dedupe_activity_rows(rows + unique_batch)
        added_count = len(existing) - len(rows)
        rows = existing
        if added_count <= 0:
            break

        batch_ts = [to_int(row.get("timestamp")) for row in unique_batch if to_int(row.get("timestamp")) is not None]
        ts_min = min(batch_ts) if batch_ts else None
        ts_max = max(batch_ts) if batch_ts else None
        windows.append(
            {
                "window_index": window_index,
                "start_ts": start_ts,
                "end_ts": current_end,
                "coverage_floor_ts": coverage_floor_ts,
                "rows_added": added_count,
                "rows_raw": len(batch_rows),
                "ts_min": ts_min,
                "ts_max": ts_max,
            }
        )

        if ts_min is None:
            break
        if coverage_floor_ts is not None and ts_min <= coverage_floor_ts:
            reached_coverage = True
        if start_ts is not None and ts_min <= start_ts:
            break

        next_end = ts_min - 1
        if current_end is not None and next_end >= current_end:
            break
        if len(batch_rows) < window_limit:
            break

        current_end = next_end

    return rows, errors, windows


def summarize_activity(rows: list[dict[str, Any]]) -> dict[str, Any]:
    trade_rows = [row for row in rows if str(row.get("type", "")).upper() == "TRADE"]

    timestamps = sorted([to_int(row.get("timestamp")) for row in trade_rows if to_int(row.get("timestamp")) is not None])
    gaps: list[float] = []
    for left, right in zip(timestamps[:-1], timestamps[1:]):
        if right >= left:
            gaps.append(float(right - left))

    side_counts = Counter([(row.get("side") or "UNKNOWN").upper() for row in trade_rows])
    outcome_counts = Counter(
        [normalize_outcome(row.get("outcome"), row.get("outcomeIndex")) for row in trade_rows]
    )
    slug_counts = Counter([row.get("slug") or "UNKNOWN" for row in trade_rows])

    usdc_sizes = [to_float(row.get("usdcSize")) for row in trade_rows]
    valid_usdc_sizes = [value for value in usdc_sizes if value is not None]

    days = {
        datetime.fromtimestamp(ts, timezone.utc).date().isoformat()
        for ts in timestamps
    }
    active_days = len(days) or 1

    slug_outcomes: dict[str, set[str]] = defaultdict(set)
    for row in trade_rows:
        slug = row.get("slug") or "UNKNOWN"
        outcome = normalize_outcome(row.get("outcome"), row.get("outcomeIndex"))
        if outcome != "UNKNOWN":
            slug_outcomes[slug].add(outcome)
    if slug_outcomes:
        dual_outcome_slug_ratio = sum(1 for outcomes in slug_outcomes.values() if len(outcomes) >= 2) / len(slug_outcomes)
    else:
        dual_outcome_slug_ratio = None

    trade_count = len(trade_rows)
    slug_concentration_hhi = None
    if trade_count > 0:
        slug_concentration_hhi = sum((count / trade_count) ** 2 for count in slug_counts.values())

    return {
        "rows": len(rows),
        "trade_rows": trade_count,
        "total_notional_usdc": sum(valid_usdc_sizes) if valid_usdc_sizes else None,
        "avg_trade_notional_usdc": statistics.mean(valid_usdc_sizes) if valid_usdc_sizes else None,
        "trade_notional_p10": percentile(valid_usdc_sizes, 0.10),
        "trade_notional_p50": percentile(valid_usdc_sizes, 0.50),
        "trade_notional_p75": percentile(valid_usdc_sizes, 0.75),
        "trade_notional_p90": percentile(valid_usdc_sizes, 0.90),
        "daily_trade_count": trade_count / active_days if trade_count else None,
        "median_intertrade_s": statistics.median(gaps) if gaps else None,
        "p10_intertrade_s": percentile(gaps, 0.10),
        "p95_intertrade_s": percentile(gaps, 0.95),
        "burst_2s_ratio": (sum(1 for gap in gaps if gap <= 2) / len(gaps)) if gaps else None,
        "side_counts": dict(side_counts),
        "outcome_counts": dict(outcome_counts),
        "slug_concentration_hhi": slug_concentration_hhi,
        "dual_outcome_slug_ratio": dual_outcome_slug_ratio,
        "top_slugs_by_trades": slug_counts.most_common(),
    }


def summarize_positions(rows: list[dict[str, Any]]) -> dict[str, Any]:
    outcome_sizes_by_slug: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    percent_pnls: list[float] = []
    cash_pnls: list[float] = []
    current_values: list[float] = []

    for row in rows:
        slug = row.get("slug") or "UNKNOWN"
        outcome = normalize_outcome(row.get("outcome"), row.get("outcomeIndex"))
        size = to_float(row.get("size"))
        if size is not None and outcome in {"UP", "DOWN"}:
            outcome_sizes_by_slug[slug][outcome] += abs(size)

        percent_pnl = to_float(row.get("percentPnl"))
        if percent_pnl is not None:
            percent_pnls.append(percent_pnl)
        cash_pnl = to_float(row.get("cashPnl"))
        if cash_pnl is not None:
            cash_pnls.append(cash_pnl)
        current_value = to_float(row.get("currentValue"))
        if current_value is not None:
            current_values.append(current_value)

    paired = 0
    total_skews: list[float] = []
    for outcomes in outcome_sizes_by_slug.values():
        up_size = outcomes.get("UP", 0.0)
        down_size = outcomes.get("DOWN", 0.0)
        total = up_size + down_size
        if up_size > 0 and down_size > 0:
            paired += 1
        if total > 0:
            total_skews.append(abs(up_size - down_size) / total)

    total_slugs = len(outcome_sizes_by_slug)
    position_pair_coverage = (paired / total_slugs) if total_slugs else None
    inventory_skew_mean = statistics.mean(total_skews) if total_skews else None

    return {
        "rows": len(rows),
        "position_pair_coverage": position_pair_coverage,
        "inventory_skew_mean": inventory_skew_mean,
        "total_current_value": sum(current_values) if current_values else None,
        "total_cash_pnl": sum(cash_pnls) if cash_pnls else None,
        "pnl_dispersion": statistics.pstdev(percent_pnls) if len(percent_pnls) > 1 else None,
    }


def compute_ev_signals(activity_rows: list[dict[str, Any]]) -> dict[str, Any]:
    trades = [row for row in activity_rows if str(row.get("type", "")).upper() == "TRADE"]
    if not trades:
        return {
            "trade_rows": 0,
            "no_outcome_trade_ratio": None,
            "yes_outcome_trade_ratio": None,
            "buy_sell_wap_spread": None,
            "roundtrip_slug_count": 0,
            "roundtrip_positive_ratio": None,
            "roundtrip_edge_sum": None,
            "roundtrip_weighted_spread": None,
            "roundtrip_matched_qty": None,
            "fifo_realized_est": None,
            "fifo_closed_matches": 0,
            "fifo_win_rate": None,
            "fifo_avg_gain": None,
            "fifo_avg_loss": None,
            "fifo_loss_pct_p75": None,
            "fifo_loss_pct_p95": None,
            "fifo_gain_pct_p60": None,
            "fifo_gain_pct_p80": None,
            "fifo_gain_retrace_proxy_pct": None,
            "max_consecutive_losses": None,
            "daily_realized_pnl_min": None,
            "daily_realized_pnl_min_abs": None,
            "realized_max_drawdown_usdc": None,
            "realized_max_drawdown_pct": None,
            "hold_sec_p50": None,
            "hold_sec_p75": None,
            "hold_sec_p90": None,
        }

    # 1) Outcome/side distribution and weighted execution prices.
    no_count = 0
    yes_count = 0
    buy_qty = 0.0
    buy_notional = 0.0
    sell_qty = 0.0
    sell_notional = 0.0

    # 2) Per-slug round-trip edge.
    per_slug: dict[str, dict[str, float]] = defaultdict(
        lambda: {
            "buy_sz": 0.0,
            "buy_notional": 0.0,
            "sell_sz": 0.0,
            "sell_notional": 0.0,
        }
    )

    for row in trades:
        raw_outcome = str(row.get("outcome") or "").upper()
        if raw_outcome == "NO":
            no_count += 1
        elif raw_outcome == "YES":
            yes_count += 1

        side = str(row.get("side") or "").upper()
        size = to_float(row.get("size")) or 0.0
        price = to_float(row.get("price")) or 0.0
        notional = size * price

        if side == "BUY":
            buy_qty += size
            buy_notional += notional
        elif side == "SELL":
            sell_qty += size
            sell_notional += notional

        slug = row.get("slug") or "UNKNOWN"
        bucket = per_slug[slug]
        if side == "BUY":
            bucket["buy_sz"] += size
            bucket["buy_notional"] += notional
        elif side == "SELL":
            bucket["sell_sz"] += size
            bucket["sell_notional"] += notional

    roundtrip_edges: list[float] = []
    roundtrip_spread_weighted = 0.0
    roundtrip_matched_qty = 0.0
    positive_count = 0

    for item in per_slug.values():
        if item["buy_sz"] <= 0 or item["sell_sz"] <= 0:
            continue
        buy_px = item["buy_notional"] / item["buy_sz"]
        sell_px = item["sell_notional"] / item["sell_sz"]
        matched = min(item["buy_sz"], item["sell_sz"])
        edge = (sell_px - buy_px) * matched
        roundtrip_edges.append(edge)
        roundtrip_spread_weighted += (sell_px - buy_px) * matched
        roundtrip_matched_qty += matched
        if edge > 0:
            positive_count += 1

    # 3) FIFO realized edge and holding period.
    fifo_lots: dict[str, deque[list[float]]] = defaultdict(deque)
    fifo_realized = 0.0
    hold_secs: list[float] = []
    match_pnls: list[float] = []
    match_pnl_pcts: list[float] = []
    loss_pnl_pcts_abs: list[float] = []
    gain_pnl_pcts: list[float] = []
    match_events: list[dict[str, float]] = []
    realized_pnl_by_day: dict[str, float] = defaultdict(float)

    sorted_trades = sorted(
        trades,
        key=lambda row: to_int(row.get("timestamp")) or 0,
    )
    for row in sorted_trades:
        side = str(row.get("side") or "").upper()
        asset = str(row.get("asset") or "")
        qty = to_float(row.get("size")) or 0.0
        px = to_float(row.get("price")) or 0.0
        ts = float(to_int(row.get("timestamp")) or 0)
        if qty <= 0:
            continue

        if side == "BUY":
            fifo_lots[asset].append([qty, px, ts])
            continue
        if side != "SELL":
            continue

        remain = qty
        while remain > 1e-9 and fifo_lots[asset]:
            lot_qty, lot_px, lot_ts = fifo_lots[asset][0]
            matched = min(remain, lot_qty)
            pnl = (px - lot_px) * matched
            fifo_realized += pnl
            match_pnls.append(pnl)
            hold_secs.append(max(0.0, ts - lot_ts))
            if lot_px > 0:
                pnl_pct = (px - lot_px) / lot_px
                match_pnl_pcts.append(pnl_pct)
                if pnl < -1e-9:
                    loss_pnl_pcts_abs.append(abs(pnl_pct))
                elif pnl > 1e-9:
                    gain_pnl_pcts.append(pnl_pct)
            match_events.append({"ts": ts, "pnl": pnl})
            day_key = datetime.fromtimestamp(ts, timezone.utc).date().isoformat()
            realized_pnl_by_day[day_key] += pnl

            lot_qty -= matched
            remain -= matched
            if lot_qty <= 1e-9:
                fifo_lots[asset].popleft()
            else:
                fifo_lots[asset][0][0] = lot_qty

    wins = [value for value in match_pnls if value > 1e-9]
    losses = [value for value in match_pnls if value < -1e-9]

    max_consecutive_losses = 0
    consecutive_losses = 0
    for pnl in match_pnls:
        if pnl < -1e-9:
            consecutive_losses += 1
            max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
        elif pnl > 1e-9:
            consecutive_losses = 0

    daily_realized_values = list(realized_pnl_by_day.values())
    daily_realized_pnl_min = min(daily_realized_values) if daily_realized_values else None
    daily_realized_pnl_min_abs = (
        abs(daily_realized_pnl_min) if daily_realized_pnl_min is not None and daily_realized_pnl_min < 0 else 0.0
    ) if daily_realized_pnl_min is not None else None

    realized_max_drawdown_usdc = None
    realized_max_drawdown_pct = None
    if match_events:
        ordered_events = sorted(match_events, key=lambda row: row["ts"])
        cumulative = 0.0
        peak = 0.0
        max_drawdown = 0.0
        for row in ordered_events:
            cumulative += row["pnl"]
            peak = max(peak, cumulative)
            drawdown = peak - cumulative
            max_drawdown = max(max_drawdown, drawdown)
        realized_max_drawdown_usdc = max_drawdown
        if peak > 0:
            realized_max_drawdown_pct = max_drawdown / peak

    gain_p60 = percentile(gain_pnl_pcts, 0.60)
    gain_p80 = percentile(gain_pnl_pcts, 0.80)
    gain_retrace_proxy = None
    if gain_p60 is not None and gain_p80 is not None:
        gain_retrace_proxy = max(0.0, gain_p80 - gain_p60)

    buy_wap = (buy_notional / buy_qty) if buy_qty > 0 else None
    sell_wap = (sell_notional / sell_qty) if sell_qty > 0 else None

    return {
        "trade_rows": len(trades),
        "no_outcome_trade_ratio": (no_count / len(trades)) if trades else None,
        "yes_outcome_trade_ratio": (yes_count / len(trades)) if trades else None,
        "buy_qty": buy_qty,
        "sell_qty": sell_qty,
        "buy_wap": buy_wap,
        "sell_wap": sell_wap,
        "buy_sell_wap_spread": (sell_wap - buy_wap) if (buy_wap is not None and sell_wap is not None) else None,
        "roundtrip_slug_count": len(roundtrip_edges),
        "roundtrip_positive_ratio": (positive_count / len(roundtrip_edges)) if roundtrip_edges else None,
        "roundtrip_edge_sum": sum(roundtrip_edges) if roundtrip_edges else None,
        "roundtrip_weighted_spread": (
            roundtrip_spread_weighted / roundtrip_matched_qty
        ) if roundtrip_matched_qty > 0 else None,
        "roundtrip_matched_qty": roundtrip_matched_qty if roundtrip_matched_qty > 0 else None,
        "fifo_realized_est": fifo_realized if match_pnls else None,
        "fifo_closed_matches": len(match_pnls),
        "fifo_win_rate": (len(wins) / (len(wins) + len(losses))) if (wins or losses) else None,
        "fifo_avg_gain": statistics.mean(wins) if wins else None,
        "fifo_avg_loss": statistics.mean(losses) if losses else None,
        "fifo_loss_pct_p75": percentile(loss_pnl_pcts_abs, 0.75),
        "fifo_loss_pct_p95": percentile(loss_pnl_pcts_abs, 0.95),
        "fifo_gain_pct_p60": gain_p60,
        "fifo_gain_pct_p80": gain_p80,
        "fifo_gain_retrace_proxy_pct": gain_retrace_proxy,
        "max_consecutive_losses": max_consecutive_losses if match_pnls else None,
        "daily_realized_pnl_min": daily_realized_pnl_min,
        "daily_realized_pnl_min_abs": daily_realized_pnl_min_abs,
        "realized_max_drawdown_usdc": realized_max_drawdown_usdc,
        "realized_max_drawdown_pct": realized_max_drawdown_pct,
        "hold_sec_p50": percentile(hold_secs, 0.50),
        "hold_sec_p75": percentile(hold_secs, 0.75),
        "hold_sec_p90": percentile(hold_secs, 0.90),
    }


def parse_best_level(book: dict[str, Any], side: str) -> tuple[float | None, float | None]:
    levels = book.get(side, [])
    if not isinstance(levels, list) or not levels:
        return None, None
    level = levels[0]
    if not isinstance(level, dict):
        return None, None
    return to_float(level.get("price")), to_float(level.get("size"))


def fetch_market_snapshot(slug: str, timeout: int, retries: int, book_sleep_ms: int) -> dict[str, Any]:
    snapshot: dict[str, Any] = {
        "slug": slug,
        "market_id": None,
        "condition_id": None,
        "market_slug": None,
        "market_category": None,
        "market_tags": [],
        "event_id": None,
        "token_books": [],
        "pair_metrics": None,
        "errors": [],
    }

    event_rows, error, url = safe_fetch_json(
        GAMMA_API,
        "/events",
        {"slug": slug},
        timeout=timeout,
        retries=retries,
    )
    if error:
        snapshot["errors"].append(build_error_entry(url, error))
        return snapshot
    market: dict[str, Any] | None = None
    if isinstance(event_rows, list) and event_rows:
        event = event_rows[0]
        markets = event.get("markets") or []
        if isinstance(markets, list) and markets:
            market = markets[0]

    if market is None:
        # Fallback: some legacy slugs are discoverable only via /markets?slug=...
        market_rows, market_error, market_url = safe_fetch_json(
            GAMMA_API,
            "/markets",
            {"slug": slug},
            timeout=timeout,
            retries=retries,
        )
        if market_error:
            snapshot["errors"].append(build_error_entry(market_url, market_error))
            return snapshot
        if not isinstance(market_rows, list) or not market_rows:
            snapshot["errors"].append(build_error_entry(market_url, "No market found"))
            return snapshot
        market = market_rows[0]

    snapshot["market_id"] = market.get("id")
    snapshot["condition_id"] = market.get("conditionId")
    snapshot["market_slug"] = market.get("slug") or slug
    snapshot["market_category"] = market.get("category")
    tags = market.get("tags")
    if isinstance(tags, list):
        snapshot["market_tags"] = tags
    snapshot["event_id"] = market.get("eventId")

    # Official metadata fallback: some /events payloads omit category/tags.
    if not snapshot["market_category"]:
        meta_rows, meta_error, meta_url = safe_fetch_json(
            GAMMA_API,
            "/markets",
            {"slug": slug},
            timeout=timeout,
            retries=retries,
        )
        if meta_error:
            snapshot["errors"].append(build_error_entry(meta_url, meta_error))
        elif isinstance(meta_rows, list) and meta_rows:
            meta_market = meta_rows[0]
            if not snapshot["market_id"]:
                snapshot["market_id"] = meta_market.get("id")
            if not snapshot["condition_id"]:
                snapshot["condition_id"] = meta_market.get("conditionId")
            if not snapshot["market_slug"]:
                snapshot["market_slug"] = meta_market.get("slug") or slug
            if not snapshot["market_category"]:
                snapshot["market_category"] = meta_market.get("category")
            meta_tags = meta_market.get("tags")
            if isinstance(meta_tags, list) and not snapshot["market_tags"]:
                snapshot["market_tags"] = meta_tags
            if not snapshot["event_id"]:
                snapshot["event_id"] = meta_market.get("eventId")
    token_ids = parse_maybe_json_list(market.get("clobTokenIds"))
    outcomes = parse_maybe_json_list(market.get("outcomes"))
    display_prices = parse_maybe_json_list(market.get("outcomePrices"))

    books: list[dict[str, Any]] = []
    for idx, token_id in enumerate(token_ids):
        label = str(outcomes[idx]) if idx < len(outcomes) else f"OUTCOME_{idx}"
        book_data, book_error, book_url = safe_fetch_json(
            CLOB_API,
            "/book",
            {"token_id": token_id},
            timeout=timeout,
            retries=retries,
        )
        if book_sleep_ms > 0:
            time.sleep(book_sleep_ms / 1000.0)

        token_entry: dict[str, Any] = {
            "token_id": str(token_id),
            "outcome": label,
            "display_price": to_float(display_prices[idx]) if idx < len(display_prices) else None,
            "best_bid": None,
            "best_ask": None,
            "spread": None,
            "top_level_depth": None,
            "error": None,
        }

        if book_error:
            token_entry["error"] = book_error
            books.append(token_entry)
            snapshot["errors"].append(build_error_entry(book_url, book_error))
            continue

        if not isinstance(book_data, dict):
            token_entry["error"] = "InvalidBookPayload"
            books.append(token_entry)
            snapshot["errors"].append(build_error_entry(book_url, "InvalidBookPayload"))
            continue

        best_bid, bid_size = parse_best_level(book_data, "bids")
        best_ask, ask_size = parse_best_level(book_data, "asks")
        token_entry["best_bid"] = best_bid
        token_entry["best_ask"] = best_ask
        if best_bid is not None and best_ask is not None:
            token_entry["spread"] = best_ask - best_bid
        if bid_size is not None or ask_size is not None:
            token_entry["top_level_depth"] = (bid_size or 0.0) + (ask_size or 0.0)
        books.append(token_entry)

    snapshot["token_books"] = books

    if len(books) >= 2:
        asks = [entry.get("best_ask") for entry in books[:2]]
        if asks[0] is not None and asks[1] is not None:
            best_ask_sum = asks[0] + asks[1]
            snapshot["pair_metrics"] = {
                "best_ask_sum": best_ask_sum,
                "arb_margin": 1.0 - best_ask_sum,
                "arb_positive": best_ask_sum < 1.0,
            }
    return snapshot


def summarize_orderbooks(market_snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    margins: list[float] = []
    spreads: list[float] = []
    depths: list[float] = []
    positive_count = 0
    usable_pairs = 0

    for snapshot in market_snapshots:
        pair = snapshot.get("pair_metrics")
        if pair and pair.get("arb_margin") is not None:
            usable_pairs += 1
            margins.append(float(pair["arb_margin"]))
            if pair.get("arb_positive"):
                positive_count += 1
        for token in snapshot.get("token_books", []):
            spread = token.get("spread")
            depth = token.get("top_level_depth")
            if spread is not None:
                spreads.append(float(spread))
            if depth is not None:
                depths.append(float(depth))

    return {
        "book_pairs_usable": usable_pairs,
        "arb_positive_rate": (positive_count / usable_pairs) if usable_pairs else None,
        "avg_arb_margin": statistics.mean(margins) if margins else None,
        "avg_book_spread": statistics.mean(spreads) if spreads else None,
        "avg_top_level_depth": statistics.mean(depths) if depths else None,
    }


def summarize_official_market_profile(
    activity_summary: dict[str, Any],
    market_snapshots: list[dict[str, Any]],
) -> dict[str, Any]:
    slug_trade_count = {slug: count for slug, count in activity_summary.get("top_slugs_by_trades", [])}
    category_weighted: Counter[str] = Counter()
    resolved = 0
    unresolved = 0

    for snapshot in market_snapshots:
        category = str(snapshot.get("market_category") or "").strip() or "unknown"
        trade_count = slug_trade_count.get(snapshot.get("slug"), 0)
        if category == "unknown":
            unresolved += 1
        else:
            resolved += 1
        category_weighted[category] += trade_count

    total_weight = sum(category_weighted.values())
    category_share = {
        category: (weight / total_weight) if total_weight > 0 else 0.0
        for category, weight in category_weighted.items()
    }
    dominant_category = None
    if category_weighted:
        dominant_category = category_weighted.most_common(1)[0][0]

    return {
        "coverage_markets": len(market_snapshots),
        "resolved_category_markets": resolved,
        "unresolved_category_markets": unresolved,
        "resolved_category_ratio": (resolved / len(market_snapshots)) if market_snapshots else None,
        "category_trade_weights": dict(category_weighted),
        "category_trade_share": category_share,
        "dominant_category": dominant_category,
    }


def extract_top_slugs(activity_summary: dict[str, Any], top_n: int) -> list[str]:
    pairs = activity_summary.get("top_slugs_by_trades", [])
    return [slug for slug, _count in pairs[:top_n] if slug and slug != "UNKNOWN"]


# ---------------------------------------------------------------------------
# Slug-based market classification (fallback when API category/tags missing)
# ---------------------------------------------------------------------------

_SLUG_CATEGORY_RULES: list[tuple[str, list[str]]] = [
    # Sports
    ("sports/olympics", ["olympics", "speed-skating", "ice-hockey", "biathlon", "skiing",
                         "bobsled", "luge", "curling", "figure-skating", "skeleton"]),
    ("sports/nba", ["nba", "all-star-game", "cavaliers", "celtics", "lakers", "pistons",
                    "bucks", "knicks", "warriors", "nuggets", "thunder", "rockets",
                    "grizzlies", "timberwolves", "heat", "suns", "sixers", "nets",
                    "clippers", "hawks", "bulls", "pacers", "magic", "raptors",
                    "hornets", "spurs", "blazers", "pelicans", "kings", "jazz",
                    "mavericks", "eastern-conference", "western-conference"]),
    ("sports/nfl", ["nfl", "super-bowl", "chiefs", "eagles", "49ers", "ravens",
                    "bills", "cowboys", "lions", "packers", "nfl-draft"]),
    ("sports/football", ["premier-league", "la-liga", "bundesliga", "serie-a", "ligue-1",
                         "champions-league", "europa-league", "mex-", "liga-mx",
                         "chelsea", "arsenal", "liverpool", "barcelona", "real-madrid",
                         "manchester", "juventus", "psg", "bayern", "ipl",
                         "indian-premier-league"]),
    ("sports/rugby", ["six-nations", "rugby", "rusixnat-"]),
    ("sports/f1", ["f1-", "formula-1", "grand-prix", "verstappen", "hamilton",
                   "leclerc", "norris", "piastri", "red-bull-racing",
                   "constructors-champion", "drivers-champion"]),
    ("sports/esports", ["esport", "blast-slam", "team-liquid", "team-vitality",
                        "g2-esports", "fnatic", "lec-", "pgl-", "counter-strike",
                        "valorant", "league-of-legends"]),
    ("sports/mma", ["ufc", "mma", "fight-night", "boxing", "bellator"]),
    ("sports/tennis", ["tennis", "atp-", "wta-", "grand-slam", "djokovic",
                       "federer", "nadal", "alcaraz", "sinner"]),
    ("sports/mlb", ["mlb", "world-series", "yankees", "dodgers", "astros",
                    "braves", "phillies", "padres", "mets", "cubs"]),
    # Social media / personalities
    ("social/elon-tweets", ["elon-musk", "musk-tweet", "of-tweets"]),
    ("social/trump-posts", ["trump-truth-social", "truth-social-posts"]),
    # Tech / AI
    ("tech/ai", ["ai-model", "anthropic", "openai", "google-ai", "deepseek",
                 "best-ai-model", "artificial-intelligence", "chatgpt", "gemini",
                 "claude-ai"]),
    ("tech/general", ["apple-", "microsoft-", "nvidia-", "tesla-stock",
                      "spacex-", "starlink"]),
    # Politics
    ("politics/geopolitics", ["iran", "strike-", "tariff", "sanction", "ceasefire",
                              "invasion", "nato-", "china-taiwan", "russia-ukraine",
                              "north-korea", "missile"]),
    ("politics/us-domestic", ["executive-order", "doge-", "congress-", "senate-",
                              "house-of-rep", "supreme-court", "impeach",
                              "government-shutdown"]),
    ("politics/elections", ["election", "mayoral", "governor", "presidential",
                           "parliament", "referendum", "primary-", "nominee",
                           "win-the-most-seats"]),
    # Finance
    ("finance/central-banks", ["reserve-bank", "rba-", "ecb-", "fed-", "fomc",
                               "interest-rate", "boj-", "boe-", "rate-cut",
                               "rate-hike", "inflation-", "cpi-"]),
    ("finance/markets", ["s-p-500", "nasdaq", "bitcoin", "ethereum", "solana",
                         "crypto", "home-value", "revenue", "gdp-"]),
    # Entertainment
    ("entertainment/awards", ["oscar", "academy-award", "golden-globe", "grammy",
                              "emmy", "bafta", "cannes"]),
    ("entertainment/music", ["spotify", "billboard", "album-", "song-"]),
    ("entertainment/tv", ["traitor", "survivor", "bachelor", "reality-tv",
                          "top-chef", "big-brother"]),
    # Weather / science
    ("weather", ["temperature", "weather", "snow", "rainfall", "climate",
                 "hurricane", "global-temp"]),
]


def classify_slug(slug: str) -> str:
    """Classify a market slug into a category using keyword pattern matching.

    Returns a hierarchical category string like 'sports/nba' or 'politics/elections'.
    Falls back to 'uncategorized' when no rule matches.
    """
    lower = slug.lower()
    for category, keywords in _SLUG_CATEGORY_RULES:
        for kw in keywords:
            if kw in lower:
                return category
    return "uncategorized"


def build_slug_based_market_profile(
    activity_summary: dict[str, Any],
) -> dict[str, Any]:
    """Classify ALL traded slugs by name patterns and produce a category breakdown.

    Unlike ``summarize_official_market_profile`` which only covers the top-N
    enriched slugs and relies on the API ``market.category`` field (often empty),
    this function classifies every slug from the activity data.
    """
    all_slug_trades: list[tuple[str, int]] = activity_summary.get("top_slugs_by_trades", [])
    if not all_slug_trades:
        return {
            "total_slugs": 0,
            "total_trades": 0,
            "category_slug_counts": {},
            "category_trade_counts": {},
            "category_trade_share": {},
            "top_category": None,
            "top3_categories": [],
            "category_details": {},
        }

    category_slugs: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for slug, count in all_slug_trades:
        cat = classify_slug(slug)
        category_slugs[cat].append((slug, count))

    total_trades = sum(c for _, c in all_slug_trades)
    category_trade_counts: dict[str, int] = {}
    category_slug_counts: dict[str, int] = {}
    for cat, items in category_slugs.items():
        category_slug_counts[cat] = len(items)
        category_trade_counts[cat] = sum(c for _, c in items)

    category_trade_share = {
        cat: (cnt / total_trades) if total_trades > 0 else 0.0
        for cat, cnt in category_trade_counts.items()
    }

    sorted_cats = sorted(category_trade_counts.items(), key=lambda x: -x[1])
    top_category = sorted_cats[0][0] if sorted_cats else None
    top3 = [
        {"category": cat, "trades": cnt, "share": category_trade_share.get(cat, 0.0)}
        for cat, cnt in sorted_cats[:3]
    ]

    # Per-category top slugs (max 3 each, for reference)
    category_details: dict[str, list[dict[str, Any]]] = {}
    for cat, items in category_slugs.items():
        top_items = sorted(items, key=lambda x: -x[1])[:3]
        category_details[cat] = [
            {"slug": s, "trades": c} for s, c in top_items
        ]

    return {
        "total_slugs": len(all_slug_trades),
        "total_trades": total_trades,
        "category_slug_counts": dict(sorted(category_slug_counts.items(), key=lambda x: -x[1])),
        "category_trade_counts": dict(sorted(category_trade_counts.items(), key=lambda x: -x[1])),
        "category_trade_share": dict(sorted(category_trade_share.items(), key=lambda x: -x[1])),
        "top_category": top_category,
        "top3_categories": top3,
        "category_details": category_details,
    }


def collect_none_paths(value: Any, prefix: str = "", out: list[str] | None = None) -> list[str]:
    if out is None:
        out = []
    if value is None:
        out.append(prefix or "$")
        return out
    if isinstance(value, dict):
        for key, child in value.items():
            next_prefix = f"{prefix}.{key}" if prefix else key
            collect_none_paths(child, next_prefix, out)
        return out
    if isinstance(value, list):
        for idx, child in enumerate(value):
            next_prefix = f"{prefix}[{idx}]"
            collect_none_paths(child, next_prefix, out)
        return out
    return out


def build_null_audit(snapshot: dict[str, Any], sample_limit: int = 200) -> dict[str, Any]:
    paths = collect_none_paths(snapshot)
    top_level_counts: Counter[str] = Counter()
    for path in paths:
        top = path.split(".", 1)[0]
        if "[" in top:
            top = top.split("[", 1)[0]
        top_level_counts[top] += 1
    return {
        "none_count_total": len(paths),
        "none_paths_sample": paths[:sample_limit],
        "none_count_by_top_level": dict(top_level_counts),
    }


def main() -> int:
    args = parse_args()
    global REDACT_IDENTIFIERS
    REDACT_IDENTIFIERS = not args.include_identifiers
    errors: list[dict[str, Any]] = []

    hard_start_ts = args.start_ts
    end_ts = args.end_ts
    coverage_floor_ts: int | None = None
    if args.days is not None:
        if args.days <= 0:
            raise SystemExit("--days must be a positive integer")
        if end_ts is None:
            end_ts = int(time.time())
        coverage_floor_ts = end_ts - args.days * 24 * 3600
    elif hard_start_ts is not None:
        coverage_floor_ts = hard_start_ts

    if hard_start_ts is not None and end_ts is not None and hard_start_ts > end_ts:
        raise SystemExit("--start-ts must be <= --end-ts")

    activity_rows, activity_errors, activity_windows = fetch_activity_rows_windowed(
        user=args.user,
        total_limit=args.limit,
        timeout=args.timeout,
        retries=args.retries,
        start_ts=hard_start_ts,
        end_ts=end_ts,
        coverage_floor_ts=coverage_floor_ts,
    )
    errors.extend(activity_errors)

    position_rows, position_errors = fetch_user_rows_paginated(
        path="/positions",
        user=args.user,
        total_limit=args.limit,
        page_size=POSITIONS_PAGE_SIZE,
        timeout=args.timeout,
        retries=args.retries,
    )
    errors.extend(position_errors)

    activity_summary = summarize_activity(activity_rows)
    position_summary = summarize_positions(position_rows)
    ev_signals = compute_ev_signals(activity_rows)
    top_slugs = extract_top_slugs(activity_summary, args.top_slugs)

    market_snapshots: list[dict[str, Any]] = []
    for slug in top_slugs:
        snap = fetch_market_snapshot(
            slug=slug,
            timeout=args.timeout,
            retries=args.retries,
            book_sleep_ms=args.book_sleep_ms,
        )
        errors.extend(snap.get("errors", []))
        market_snapshots.append(snap)

    book_summary = summarize_orderbooks(market_snapshots)
    official_market_profile = summarize_official_market_profile(activity_summary, market_snapshots)
    slug_market_profile = build_slug_based_market_profile(activity_summary)
    activity_timestamps = [
        to_int(row.get("timestamp")) for row in activity_rows if to_int(row.get("timestamp")) is not None
    ]
    activity_min_ts = min(activity_timestamps) if activity_timestamps else None
    activity_max_ts = max(activity_timestamps) if activity_timestamps else None
    activity_span_days = (
        (activity_max_ts - activity_min_ts) / 86400
        if activity_min_ts is not None and activity_max_ts is not None and activity_max_ts >= activity_min_ts
        else None
    )

    output = {
        "meta": {
            "generated_at_utc": now_utc_iso(),
            "user": args.user if args.include_identifiers else mask_address(args.user),
            "identifiers_redacted": not args.include_identifiers,
            "limit": args.limit,
            "days": args.days,
            "start_ts": hard_start_ts,
            "end_ts": end_ts,
            "coverage_floor_ts": coverage_floor_ts,
            "top_slugs_requested": args.top_slugs,
            "top_slugs_enriched": len(top_slugs),
            "activity_rows_fetched": len(activity_rows),
            "positions_rows_fetched": len(position_rows),
            "activity_fetch_mode": "time_windowed_offset_pagination",
            "activity_windows": activity_windows,
            "activity_timestamp_min": activity_min_ts,
            "activity_timestamp_max": activity_max_ts,
            "activity_span_days": activity_span_days,
        },
        "activity_signals": activity_summary,
        "position_signals": position_summary,
        "ev_signals": ev_signals,
        "official_market_profile": official_market_profile,
        "slug_market_profile": slug_market_profile,
        "orderbook_signals": book_summary,
        "top_slugs": top_slugs,
        "market_snapshots": market_snapshots,
        "errors": errors,
    }
    output["null_audit"] = build_null_audit(output)

    text = json.dumps(output, ensure_ascii=False, indent=2)
    print(text)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(text + "\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
