#!/usr/bin/env python3
"""簡単なヘルスチェックテスト"""

import requests
import sys

def test_health(url):
    """ヘルスチェックエンドポイントをテスト"""
    try:
        response = requests.get(f"{url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data}")
            return True
        else:
            print(f"❌ Health check failed: Status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check error: {e}")
        return False

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    print(f"Testing health endpoint: {url}/health")
    success = test_health(url)
    sys.exit(0 if success else 1)
