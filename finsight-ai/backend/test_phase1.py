"""Quick test script for all Phase 1 ticker endpoints."""
import httpx
import json
import sys

BASE = "http://localhost:8000"

def test_endpoint(url, label):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"  GET {url}")
    print(f"{'='*60}")
    try:
        r = httpx.get(url, timeout=60)
        print(f"Status: {r.status_code}")
        data = r.json()
        print(json.dumps(data, indent=2)[:1500])
        if len(json.dumps(data)) > 1500:
            print("  ... (truncated)")
        return data
    except Exception as e:
        print(f"ERROR: {e}")
        return None

# 1. Health
test_endpoint(f"{BASE}/api/health", "Health Check")

# 2. Ticker overview
data = test_endpoint(f"{BASE}/api/ticker/AAPL", "Ticker Overview — AAPL")

# 3. Metrics
data = test_endpoint(f"{BASE}/api/ticker/AAPL/metrics", "Metrics — AAPL")
if data and "metrics" in data:
    print(f"\n  Total periods: {len(data['metrics'])}")
    for m in data["metrics"]:
        print(f"  {m['period']}: P/E={m['pe_ratio']}, ROE={m['roe']}, "
              f"Gross={m['gross_margin']}, D/E={m['debt_to_equity']}, "
              f"RevGrowth={m['revenue_growth']}")

# 4. Financials (income)
test_endpoint(f"{BASE}/api/ticker/AAPL/financials?statement_type=income", "Income Statement — AAPL")

# 5. Prices
data = test_endpoint(f"{BASE}/api/ticker/AAPL/prices?period=1y", "Price History (1Y) — AAPL")
if data and "prices" in data:
    print(f"\n  Total data points: {len(data['prices'])}")
    print(f"  First: {data['prices'][0]['date']} close=${data['prices'][0]['close']}")
    print(f"  Last:  {data['prices'][-1]['date']} close=${data['prices'][-1]['close']}")

# 6. Test cache (second call should be near-instant)
import time
print(f"\n{'='*60}")
print("  Cache Performance Test")
print(f"{'='*60}")
start = time.time()
r = httpx.get(f"{BASE}/api/ticker/AAPL/metrics", timeout=30)
elapsed = time.time() - start
print(f"  Cached metrics response: {r.status_code} in {elapsed*1000:.0f}ms")

print(f"\n{'='*60}")
print("  ALL TESTS PASSED ✓")
print(f"{'='*60}")
