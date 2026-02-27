#!/usr/bin/env python3
"""
인덱싱 트리거 스크립트 (로컬 실행)
Usage: python scripts/run_index.py
"""
import requests, sys, time

API = "http://localhost:8001"


def main():
    print("[1/2] 인덱싱 시작 요청...")
    r = requests.post(f"{API}/api/index/run")
    r.raise_for_status()
    print("  →", r.json())

    print("[2/2] 완료 대기 (30초 후 stats 확인)...")
    time.sleep(30)
    r2 = requests.get(f"{API}/api/index/stats")
    print("  →", r2.json())


if __name__ == "__main__":
    main()
