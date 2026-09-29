"""Small, dependency-free runtime dashboard for the CP2 log contract."""

from __future__ import annotations

import html
import json
import os
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from statistics import mean
from typing import Any


def _number(event: dict[str, Any], field: str) -> float:
    value = event.get(field, 0)
    return float(value) if isinstance(value, int | float) else 0.0


def _percentile(values: list[float], percentile: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, round(percentile / 100 * len(ordered) - 1)))
    return ordered[index]


def _read_recent_events() -> list[dict[str, Any]]:
    path = Path(os.getenv("LOG_PATH", "data/logs.jsonl"))
    if not path.exists():
        return []
    parsed_events: list[tuple[datetime, dict[str, Any]]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
            timestamp = datetime.fromisoformat(event["ts"].replace("Z", "+00:00"))
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            continue
        parsed_events.append((timestamp, event))
    if not parsed_events:
        return []

    data_events = [
        (timestamp, event)
        for timestamp, event in parsed_events
        if event.get("event") in {"request_received", "response_sent", "request_failed"}
    ]
    if not data_events:
        return []

    # The lab can replay traffic whose timestamps differ from the machine clock.
    # Use the newest recorded event as the end of the configured 60-minute window
    # so the dashboard remains a faithful view of the most recent log workload.
    window_end = max(timestamp for timestamp, _ in data_events)
    cutoff = window_end - timedelta(minutes=60)
    return [event for timestamp, event in data_events if timestamp >= cutoff]


def _card(title: str, unit: str, threshold: str, body: str) -> str:
    return f"""
    <section class=\"card\">
      <h2>{html.escape(title)}</h2>
      <p class=\"threshold\">{html.escape(threshold)}</p>
      <div class=\"content\">{body}</div>
      <p class=\"unit\">Unit: {html.escape(unit)}</p>
    </section>"""


def render_dashboard() -> str:
    events = _read_recent_events()
    responses = [event for event in events if event.get("event") == "response_sent"]
    requests = [event for event in events if event.get("event") == "request_received"]
    failures = [event for event in events if event.get("event") == "request_failed"]
    latencies = [_number(event, "latency_ms") for event in responses]
    ttfts = [_number(event, "ttft_ms") for event in responses]
    retrievals = [event.get("tool_success") for event in events if event.get("tool_success") is not None]
    retrieval_rate = 100 * sum(value is True for value in retrievals) / len(retrievals) if retrievals else 0
    error_rate = 100 * len(failures) / len(requests) if requests else 0
    errors = Counter(str(event.get("error_type", "unknown")) for event in failures)
    costs_by_minute: dict[str, float] = defaultdict(float)
    for event in responses:
        costs_by_minute[str(event.get("ts", ""))[:16]] += _number(event, "cost_usd")
    cost_rows = "".join(
        f"<li>{html.escape(minute)}: ${value:.6f}</li>" for minute, value in sorted(costs_by_minute.items())[-5:]
    ) or "<li>No response data</li>"
    error_rows = ", ".join(f"{html.escape(name)}: {count}" for name, count in errors.items()) or "none"
    quality = [_number(event, "quality_score") for event in responses]

    panels = [
        _card("Latency percentiles and TTFT", "ms", "SLO: P95 ≤ 3000 ms", f"<b>P50</b> {_percentile(latencies, 50):.0f} · <b>P95</b> {_percentile(latencies, 95):.0f} · <b>P99</b> {_percentile(latencies, 99):.0f}<br><b>TTFT P95</b> {_percentile(ttfts, 95):.0f}"),
        _card("Request traffic", "requests_per_minute", "Threshold: ≥ 1 request/min", f"<b>Requests</b> {len(requests)} in the selected 60-minute window<br><b>Rate</b> {len(requests) / 60:.2f} requests/min"),
        _card("Error rate and retrieval success", "percent", "Error rate ≤ 2% · Retrieval success ≥ 90%", f"<b>Error rate</b> {error_rate:.2f}%<br><b>Breakdown</b> {error_rows}<br><b>Retrieval success</b> {retrieval_rate:.2f}%"),
        _card("Cost over time", "usd", "Total cost ≤ $2.50", f"<b>Total</b> ${sum(_number(event, 'cost_usd') for event in responses):.6f}<ul>{cost_rows}</ul>"),
        _card("Input and output tokens", "tokens", "Total ≤ 50,000 tokens", f"<b>Input</b> {sum(_number(event, 'tokens_in') for event in responses):.0f}<br><b>Output</b> {sum(_number(event, 'tokens_out') for event in responses):.0f}"),
        _card("Quality proxy", "score_0_to_1", "Mean quality ≥ 0.75", f"<b>Mean quality</b> {mean(quality) if quality else 0:.2f}"),
    ]
    return f"""<!doctype html>
<html lang=\"en\"><head><meta charset=\"utf-8\"><meta http-equiv=\"refresh\" content=\"30\">
<title>K4-L3A LLMOps Dashboard</title><style>
body {{ background:#10151f; color:#e9edf5; font-family:system-ui,sans-serif; margin:32px; }}
h1 {{ margin-bottom:4px; }} .meta,.threshold,.unit {{ color:#aab6c8; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(320px,1fr)); gap:16px; margin-top:24px; }}
.card {{ background:#192231; border:1px solid #33445e; border-radius:10px; padding:18px; min-height:160px; }}
h2 {{ margin:0; font-size:18px; }} .content {{ font-size:18px; line-height:1.7; }} ul {{ font-size:13px; margin:6px 0; padding-left:18px; }}
</style></head><body><h1>K4-L3A Monitoring &amp; LLMOps</h1>
<p class=\"meta\">Log source: data/logs.jsonl · Time range: last 60 minutes · Auto-refresh: 30 seconds · Events: {len(events)}</p>
<main class=\"grid\">{''.join(panels)}</main></body></html>"""
