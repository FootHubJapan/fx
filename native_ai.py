#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ネイティブAI呼び出しモジュール（OpenAI不使用）
あなたのHTTP APIを呼び出す
"""

import os
import json
import requests
from typing import Optional

DEFAULT_TIMEOUT_SEC = 20


def call_native_ai(text: str, context: Optional[str] = None) -> str:
    """
    Call your Native AI HTTP API and return a reply string.

    Required env:
      - NATIVE_AI_URL

    Optional env:
      - NATIVE_AI_API_KEY (Bearer token)
      - NATIVE_AI_TIMEOUT_SEC
    """

    url = os.getenv("NATIVE_AI_URL", "").strip()
    if not url:
        return "NATIVE_AI_URL が未設定です（.env または Render環境変数を確認してね）"

    api_key = os.getenv("NATIVE_AI_API_KEY", "").strip()

    timeout = DEFAULT_TIMEOUT_SEC
    try:
        timeout = int(os.getenv("NATIVE_AI_TIMEOUT_SEC", str(DEFAULT_TIMEOUT_SEC)))
    except Exception:
        timeout = DEFAULT_TIMEOUT_SEC

    headers = {
        "Content-Type": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {"text": text}
    if context:
        payload["context"] = context

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=timeout)
        if res.status_code >= 400:
            # 返ってきた本文が長いことがあるので短くする
            body = (res.text or "").strip()
            if len(body) > 600:
                body = body[:600] + "..."
            return f"ネイティブAI呼び出し失敗: HTTP {res.status_code}\n{body}"

        # JSON parse
        try:
            data = res.json()
        except Exception:
            raw = (res.text or "").strip()
            if len(raw) > 1500:
                raw = raw[:1500] + "..."
            return f"ネイティブAIの応答がJSONではありません:\n{raw}"

        # reply key candidates
        reply = (
            data.get("reply")
            or data.get("response")
            or data.get("text")
        )

        if reply is None:
            # 予想外形式でも落ちないように
            dumped = json.dumps(data, ensure_ascii=False)
            if len(dumped) > 1500:
                dumped = dumped[:1500] + "..."
            return f"ネイティブAIの返却形式が想定外です:\n{dumped}"

        return str(reply)

    except requests.exceptions.Timeout:
        return f"ネイティブAIがタイムアウトしました（{timeout}s）"
    except Exception as e:
        return f"ネイティブAI呼び出し中に例外が発生しました: {type(e).__name__}: {e}"
