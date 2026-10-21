"""AST 静态校验：拦截危险导入与危险调用。"""
import ast

FORBIDDEN_IMPORTS = {"os", "sys", "subprocess", "socket", "requests", "shutil", "ctypes", "importlib", "urllib"}
FORBIDDEN_CALLS = {"eval", "exec", "compile", "__import__", "open", "input"}


def validate_code(code: str) -> dict:
    """对代码做 AST 静态校验。

    Returns:
        {"passed": bool, "errors": [...], "risk_points": [...]}
    """
    errors: list[str] = []
    risk_points: list[str] = []

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return {"passed": False, "errors": [f"语法错误: {e}"], "risk_points": []}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in FORBIDDEN_IMPORTS:
                    risk_points.append(f"禁止导入模块: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[0] in FORBIDDEN_IMPORTS:
                risk_points.append(f"禁止导入模块: {node.module}")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
                risk_points.append(f"禁止调用: {node.func.id}")

    return {"passed": not risk_points, "errors": errors, "risk_points": risk_points}
