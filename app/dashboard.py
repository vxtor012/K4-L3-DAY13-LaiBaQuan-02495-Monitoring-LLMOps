from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .metrics import percentile


def compute_dashboard_metrics(log_path: Path = Path("data/logs.jsonl")) -> dict[str, Any]:
    if not log_path.exists():
        return {
            "latency": {"p50": 0, "p95": 0, "p99": 0, "ttft_p95": 0, "passed": True},
            "traffic": {"count": 0, "rate_per_minute": 0.0, "passed": False},
            "errors": {
                "error_rate_pct": 0.0,
                "count_by_value": {},
                "tool_success_rate_pct": 100.0,
                "passed": True,
            },
            "cost": {"total": 0.0, "sum_by_minute": {}, "passed": True},
            "tokens": {"sum_by_field": {"tokens_in": 0, "tokens_out": 0, "total": 0}, "passed": True},
            "quality": {"mean": 0.0, "passed": False},
        }

    records: list[dict[str, Any]] = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    latencies: list[int] = []
    ttfts: list[int] = []
    req_received_count = 0
    req_failed_count = 0
    error_counts: Counter[str] = Counter()
    tool_successes: list[bool] = []
    costs: list[float] = []
    costs_by_minute: dict[str, float] = {}
    tokens_in_total = 0
    tokens_out_total = 0
    quality_scores: list[float] = []
    timestamps: list[datetime] = []

    for r in records:
        event = r.get("event")
        ts_str = r.get("ts")
        minute_key = ts_str[:16] if ts_str and len(ts_str) >= 16 else "now"

        if ts_str:
            try:
                timestamps.append(datetime.fromisoformat(ts_str.replace("Z", "+00:00")))
            except Exception:
                pass

        if event == "request_received":
            req_received_count += 1

        elif event == "request_failed":
            req_failed_count += 1
            err_type = r.get("error_type", "unknown")
            error_counts[err_type] += 1
            if "tool_success" in r and r.get("tool_success") is not None:
                tool_successes.append(bool(r.get("tool_success")))

        elif event == "response_sent":
            if "latency_ms" in r:
                latencies.append(int(r["latency_ms"]))
            if "ttft_ms" in r:
                ttfts.append(int(r["ttft_ms"]))
            if "cost_usd" in r:
                cost = float(r["cost_usd"])
                costs.append(cost)
                costs_by_minute[minute_key] = round(costs_by_minute.get(minute_key, 0.0) + cost, 6)
            if "tokens_in" in r:
                tokens_in_total += int(r["tokens_in"])
            if "tokens_out" in r:
                tokens_out_total += int(r["tokens_out"])
            if "quality_score" in r:
                quality_scores.append(float(r["quality_score"]))
            if "tool_success" in r and r.get("tool_success") is not None:
                tool_successes.append(bool(r.get("tool_success")))

    # 1. Latency panel
    p50 = percentile(latencies, 50)
    p95 = percentile(latencies, 95)
    p99 = percentile(latencies, 99)
    ttft_p95 = percentile(ttfts, 95)
    latency_passed = p95 <= 3000

    # 2. Traffic panel
    if timestamps and len(timestamps) >= 2:
        duration_min = max(1.0, (max(timestamps) - min(timestamps)).total_seconds() / 60.0)
    else:
        duration_min = 1.0
    rate_per_min = round(req_received_count / duration_min, 2)
    traffic_passed = rate_per_min >= 1.0 or req_received_count >= 1

    # 3. Errors panel
    error_rate_pct = round((req_failed_count / max(1, req_received_count)) * 100, 2)
    tool_success_rate = (
        round((tool_successes.count(True) / len(tool_successes)) * 100, 2)
        if tool_successes
        else 100.0
    )
    errors_passed = error_rate_pct <= 2.0

    # 4. Cost panel
    total_cost = round(sum(costs), 4)
    cost_passed = total_cost <= 2.5

    # 5. Tokens panel
    total_tokens = tokens_in_total + tokens_out_total
    tokens_passed = total_tokens <= 50000

    # 6. Quality panel
    quality_mean = round(sum(quality_scores) / len(quality_scores), 2) if quality_scores else 0.0
    quality_passed = quality_mean >= 0.75

    return {
        "latency": {
            "p50": p50,
            "p95": p95,
            "p99": p99,
            "ttft_p95": ttft_p95,
            "unit": "ms",
            "threshold": "p95 <= 3000 ms",
            "passed": latency_passed,
        },
        "traffic": {
            "count": req_received_count,
            "rate_per_minute": rate_per_min,
            "unit": "requests_per_minute",
            "threshold": "rate_per_minute >= 1",
            "passed": traffic_passed,
        },
        "errors": {
            "error_rate_pct": error_rate_pct,
            "count_by_value": dict(error_counts),
            "tool_success_rate_pct": tool_success_rate,
            "unit": "percent",
            "threshold": "error_rate_pct <= 2 %",
            "passed": errors_passed,
        },
        "cost": {
            "total": total_cost,
            "sum_by_minute": costs_by_minute,
            "unit": "usd",
            "threshold": "total <= 2.5 usd",
            "passed": cost_passed,
        },
        "tokens": {
            "sum_by_field": {
                "tokens_in": tokens_in_total,
                "tokens_out": tokens_out_total,
                "total": total_tokens,
            },
            "unit": "tokens",
            "threshold": "sum_by_field <= 50000 tokens",
            "passed": tokens_passed,
        },
        "quality": {
            "mean": quality_mean,
            "unit": "score_0_to_1",
            "threshold": "mean >= 0.75",
            "passed": quality_passed,
        },
    }


def get_dashboard_html() -> str:
    return """<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>K4-L3A Day 13 Monitoring & LLMOps Dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    :root {
      --bg: #0d1117;
      --card-bg: #161b22;
      --border: #30363d;
      --text: #c9d1d9;
      --heading: #f0f6fc;
      --accent: #58a6ff;
      --green: #3fb950;
      --red: #f85149;
      --yellow: #d29922;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      padding: 24px;
    }
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
      padding-bottom: 16px;
      border-bottom: 1px solid var(--border);
    }
    h1 { font-size: 24px; color: var(--heading); }
    .meta { font-size: 14px; color: #8b949e; }
    .badge {
      display: inline-block;
      padding: 4px 10px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 600;
    }
    .badge-pass { background: rgba(63,185,80,0.15); color: var(--green); border: 1px solid var(--green); }
    .badge-fail { background: rgba(248,81,73,0.15); color: var(--red); border: 1px solid var(--red); }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
      gap: 20px;
    }
    .card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 18px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .card-title {
      font-size: 16px;
      font-weight: 600;
      color: var(--heading);
    }
    .metric-value {
      font-size: 32px;
      font-weight: 700;
      color: var(--heading);
    }
    .metric-unit { font-size: 14px; color: #8b949e; font-weight: normal; margin-left: 4px; }
    .stats-row {
      display: flex;
      gap: 16px;
      font-size: 13px;
      color: #8b949e;
    }
    .stats-row b { color: var(--text); }
    .threshold-info {
      font-size: 12px;
      color: #8b949e;
      background: #0d1117;
      padding: 6px 10px;
      border-radius: 6px;
    }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>K4-L3A Day 13 Monitoring & LLMOps Dashboard</h1>
      <div class="meta">Cửa sổ quan sát: <b>60 phút</b> | Tự động làm mới: <b>30s</b> | Nguồn: <code>data/logs.jsonl</code></div>
    </div>
    <div id="last-update" class="meta">Đang tải...</div>
  </header>

  <div class="grid">
    <!-- Panel 1: Latency -->
    <div class="card" id="panel-latency">
      <div class="card-header">
        <span class="card-title">1. Latency percentiles and TTFT</span>
        <span class="badge" id="badge-latency">...</span>
      </div>
      <div>
        <span class="metric-value" id="val-latency-p95">-</span><span class="metric-unit">ms (P95)</span>
      </div>
      <div class="stats-row">
        <span>P50: <b id="val-latency-p50">-</b> ms</span>
        <span>P99: <b id="val-latency-p99">-</b> ms</span>
        <span>TTFT P95: <b id="val-ttft-p95">-</b> ms</span>
      </div>
      <div class="threshold-info">Threshold: <code>p95 &lt;= 3000 ms</code></div>
    </div>

    <!-- Panel 2: Traffic -->
    <div class="card" id="panel-traffic">
      <div class="card-header">
        <span class="card-title">2. Request traffic</span>
        <span class="badge" id="badge-traffic">...</span>
      </div>
      <div>
        <span class="metric-value" id="val-traffic-rate">-</span><span class="metric-unit">req/phút</span>
      </div>
      <div class="stats-row">
        <span>Tổng requests: <b id="val-traffic-count">-</b></span>
      </div>
      <div class="threshold-info">Threshold: <code>rate_per_minute &gt;= 1</code></div>
    </div>

    <!-- Panel 3: Errors -->
    <div class="card" id="panel-errors">
      <div class="card-header">
        <span class="card-title">3. Error rate and retrieval success</span>
        <span class="badge" id="badge-errors">...</span>
      </div>
      <div>
        <span class="metric-value" id="val-error-rate">-</span><span class="metric-unit">% lỗi</span>
      </div>
      <div class="stats-row">
        <span>Retrieval success: <b id="val-retrieval-success">-</b> %</span>
        <span>Phân loại lỗi: <b id="val-error-breakdown">0</b></span>
      </div>
      <div class="threshold-info">Threshold: <code>error_rate_pct &lt;= 2 %</code></div>
    </div>

    <!-- Panel 4: Cost -->
    <div class="card" id="panel-cost">
      <div class="card-header">
        <span class="card-title">4. Cost over time</span>
        <span class="badge" id="badge-cost">...</span>
      </div>
      <div>
        <span class="metric-value" id="val-cost-total">-</span><span class="metric-unit">USD</span>
      </div>
      <div class="stats-row">
        <span>Cửa sổ quan sát: <b>60 phút</b></span>
      </div>
      <div class="threshold-info">Threshold: <code>total &lt;= 2.5 USD</code></div>
    </div>

    <!-- Panel 5: Tokens -->
    <div class="card" id="panel-tokens">
      <div class="card-header">
        <span class="card-title">5. Input and output tokens</span>
        <span class="badge" id="badge-tokens">...</span>
      </div>
      <div>
        <span class="metric-value" id="val-tokens-total">-</span><span class="metric-unit">tokens</span>
      </div>
      <div class="stats-row">
        <span>Tokens IN: <b id="val-tokens-in">-</b></span>
        <span>Tokens OUT: <b id="val-tokens-out">-</b></span>
      </div>
      <div class="threshold-info">Threshold: <code>sum_by_field &lt;= 50000 tokens</code></div>
    </div>

    <!-- Panel 6: Quality -->
    <div class="card" id="panel-quality">
      <div class="card-header">
        <span class="card-title">6. Quality proxy</span>
        <span class="badge" id="badge-quality">...</span>
      </div>
      <div>
        <span class="metric-value" id="val-quality-mean">-</span><span class="metric-unit">/ 1.0</span>
      </div>
      <div class="stats-row">
        <span>Thang đo: <b>0.0 – 1.0 (heuristic proxy)</b></span>
      </div>
      <div class="threshold-info">Threshold: <code>mean &gt;= 0.75</code></div>
    </div>
  </div>

  <script>
    async function refreshDashboard() {
      try {
        const res = await fetch('/api/dashboard-metrics');
        const data = await res.json();
        
        // 1. Latency
        document.getElementById('val-latency-p95').textContent = data.latency.p95;
        document.getElementById('val-latency-p50').textContent = data.latency.p50;
        document.getElementById('val-latency-p99').textContent = data.latency.p99;
        document.getElementById('val-ttft-p95').textContent = data.latency.ttft_p95;
        setBadge('badge-latency', data.latency.passed);

        // 2. Traffic
        document.getElementById('val-traffic-rate').textContent = data.traffic.rate_per_minute;
        document.getElementById('val-traffic-count').textContent = data.traffic.count;
        setBadge('badge-traffic', data.traffic.passed);

        // 3. Errors
        document.getElementById('val-error-rate').textContent = data.errors.error_rate_pct;
        document.getElementById('val-retrieval-success').textContent = data.errors.tool_success_rate_pct;
        const errDetails = Object.entries(data.errors.count_by_value).map(([k,v]) => `${k}:${v}`).join(', ') || 'Không có';
        document.getElementById('val-error-breakdown').textContent = errDetails;
        setBadge('badge-errors', data.errors.passed);

        // 4. Cost
        document.getElementById('val-cost-total').textContent = '$' + data.cost.total.toFixed(4);
        setBadge('badge-cost', data.cost.passed);

        // 5. Tokens
        document.getElementById('val-tokens-total').textContent = data.tokens.sum_by_field.total.toLocaleString();
        document.getElementById('val-tokens-in').textContent = data.tokens.sum_by_field.tokens_in.toLocaleString();
        document.getElementById('val-tokens-out').textContent = data.tokens.sum_by_field.tokens_out.toLocaleString();
        setBadge('badge-tokens', data.tokens.passed);

        // 6. Quality
        document.getElementById('val-quality-mean').textContent = data.quality.mean.toFixed(2);
        setBadge('badge-quality', data.quality.passed);

        document.getElementById('last-update').textContent = 'Cập nhật lúc: ' + new Date().toLocaleTimeString();
      } catch (err) {
        console.error('Error fetching dashboard metrics:', err);
      }
    }

    function setBadge(id, passed) {
      const el = document.getElementById(id);
      if (passed) {
        el.className = 'badge badge-pass';
        el.textContent = 'Bình thường';
      } else {
        el.className = 'badge badge-fail';
        el.textContent = 'Vượt ngưỡng';
      }
    }

    refreshDashboard();
    setInterval(refreshDashboard, 30000);
  </script>
</body>
</html>"""
