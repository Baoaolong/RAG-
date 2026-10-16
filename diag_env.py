# -*- coding: utf-8 -*-
"""临时诊断脚本：确认创空间容器里能不能读到密钥。

只把 sha256 前 12 位和长度写出来，不写明文。写完删掉。
"""
import hashlib
import os
import sys


def report(stream):
    for name in ("ADMIN_PASSWORD", "DASHSCOPE_API_KEY"):
        value = os.getenv(name)
        if value is None:
            print(f"[RAG-DIAG] {name}: MISSING", file=stream, flush=True)
        else:
            digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
            print(f"[RAG-DIAG] {name}: len={len(value)} sha256_12={digest}", file=stream, flush=True)


report(sys.stdout)
report(sys.stderr)
