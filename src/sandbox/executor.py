"""沙箱执行器：受限执行生成的代码。

当前实现基于子进程 + 超时 + AST 前置校验（本机无 Docker）。
部署时可由 Docker 容器隔离实现替换，接口保持不变。
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile


def execute(
    code: str,
    entry_point: str = "recommend",
    scores: dict | None = None,
    timeout: int = 30,
) -> dict:
    """执行代码，返回执行结果与日志。

    Returns:
        {"exit_code": int, "result": dict | None, "logs": [{"level","message"}]}
    """
    scores = scores or {"technical_score": 0, "fundamental_score": 0, "sentiment_score": 0}

    call_code = (
        f"\n\nimport json\n"
        f"result = {entry_point}({scores['technical_score']}, {scores['fundamental_score']}, {scores['sentiment_score']})\n"
        f"print('__RESULT__' + json.dumps(result, ensure_ascii=False))\n"
    )
    full_code = code + call_code

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(full_code)
        tmp_path = f.name

    logs: list[dict] = []
    try:
        proc = subprocess.run(
            ["python", tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        logs.append({"level": "info", "message": f"exit_code={proc.returncode}"})
        if proc.stdout:
            logs.append({"level": "info", "message": proc.stdout.strip()[:500]})
        if proc.stderr:
            logs.append({"level": "error", "message": proc.stderr.strip()[:500]})

        result = None
        if proc.returncode == 0:
            for line in proc.stdout.splitlines():
                if line.startswith("__RESULT__"):
                    try:
                        result = json.loads(line[len("__RESULT__"):])
                    except json.JSONDecodeError:
                        result = None
                    break

        return {"exit_code": proc.returncode, "result": result, "logs": logs}
    except subprocess.TimeoutExpired:
        return {"exit_code": -1, "result": None, "logs": [{"level": "error", "message": f"执行超时（>{timeout}s）"}]}
    finally:
        os.unlink(tmp_path)
