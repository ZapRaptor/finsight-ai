"""Phase 2 verification: test chat and report endpoints."""
import httpx
import json
import sys

BASE = "http://localhost:8000"

print("=" * 60)
print("  Phase 2 Verification")
print("=" * 60)

# 1. Test non-streaming chat
print("\n[1] POST /api/chat (non-streaming)")
print("-" * 40)
try:
    r = httpx.post(
        f"{BASE}/api/chat",
        json={
            "symbol": "AAPL",
            "question": "What are Apple's profit margins and how have they trended over the last 3 years?",
            "include_documents": True,
        },
        timeout=120,
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"Steps: {data.get('step_log', [])}")
        print(f"Errors: {data.get('errors', [])}")
        print(f"Response ({len(data.get('response', ''))} chars):")
        print(data.get("response", "")[:1000])
    else:
        print(f"Error: {r.text[:500]}")
except Exception as e:
    print(f"FAILED: {e}")

# 2. Test report/memo
print("\n\n[2] POST /api/report/AAPL (investment memo)")
print("-" * 40)
try:
    r = httpx.post(f"{BASE}/api/report/AAPL", timeout=120)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"Steps: {data.get('step_log', [])}")
        memo = data.get("memo", {})
        print(f"Recommendation: {memo.get('recommendation')}")
        print(f"Confidence: {memo.get('confidence')}")
        print(f"Summary: {memo.get('summary', '')[:300]}")
        print(f"Bull case: {memo.get('bull_case', [])}")
        print(f"Bear case: {memo.get('bear_case', [])}")
        print(f"SWOT strengths: {memo.get('swot', {}).get('strengths', [])}")
    else:
        print(f"Error: {r.text[:500]}")
except Exception as e:
    print(f"FAILED: {e}")

print("\n" + "=" * 60)
print("  Phase 2 Verification Complete")
print("=" * 60)
