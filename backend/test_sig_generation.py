#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试高德签名生成是否正确
"""
import hashlib
import io
import sys
from pathlib import Path

from dotenv import load_dotenv

from services.provider_clients import AMapClient

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()
load_dotenv(Path(__file__).resolve().parent / ".env")

amap = AMapClient()

# 测试参数
test_params = {
    "key": amap.api_key,
    "keywords": "象鼻山",
    "city": "桂林",
    "offset": 1,
    "types": "",
    "extensions": "all",
}

print("=" * 60)
print("[TEST] AMap Signature Generation")
print("=" * 60)
print(f"API Key: {amap.api_key[:20]}...")
print(f"Security Code: {amap.security_code[:20]}...")
print()

# 生成签名
sig = amap._generate_sig(test_params)
print(f"Generated Signature: {sig}")
print()

# 手动验证签名生成过程
print("[DEBUG] Signature generation process:")
normalized = amap._normalize_params(test_params)
print(f"1. Normalized params: {normalized}")

sorted_params = sorted(
    [(str(key), str(value)) for key, value in normalized.items()],
    key=lambda item: item[0],
)
print(f"2. Sorted params: {sorted_params}")

query = "&".join([f"{key}={value}" for key, value in sorted_params])
print(f"3. Query string: {query}")

raw = f"{query}{amap.security_code}"
print(f"4. Raw string (with security code): {raw[:80]}...")

md5_hash = hashlib.md5(raw.encode("utf-8")).hexdigest()
print(f"5. MD5 hash: {md5_hash}")
print()

if sig == md5_hash:
    print("[OK] Signature generation is correct")
else:
    print("[FAIL] Signature mismatch!")
    print(f"  Expected: {md5_hash}")
    print(f"  Got: {sig}")