"""Bounded arithmetic expressions, interpreted without Python eval."""
import ast
import math
import operator

# Keep expressions small and restrict operators/functions to numeric operations.
BINARY = {ast.Add: operator.add, ast.Sub: operator.sub,
          ast.Mult: operator.mul, ast.Div: operator.truediv, ast.Pow: operator.pow}
FUNCTIONS = {"sin": math.sin, "cos": math.cos, "exp": math.exp,
             "sqrt": math.sqrt, "abs": abs, "min": min, "max": max}
NAMES = {"t", "T", "ambient", "pi"}


def parse(expression):
    """Validate a compact arithmetic tree once per trial."""
    if len(expression) > 500:
        raise ValueError("Equation must be at most 500 characters.")
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as error:
        raise ValueError("Invalid equation syntax.") from error
    nodes = list(ast.walk(tree))
    allowed = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Call, ast.Name,
               ast.Load, ast.Constant, ast.UAdd, ast.USub, *BINARY)
    if len(nodes) > 100 or any(not isinstance(n, allowed) for n in nodes):
        raise ValueError("Equation contains unsupported operations.")
    for node in nodes:
        if isinstance(node, ast.Name) and node.id not in NAMES | FUNCTIONS.keys():
            raise ValueError(f"Unknown equation name: {node.id}")
        if isinstance(node, ast.Constant) and type(node.value) not in (int, float):
            raise ValueError("Only numeric constants are allowed.")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in FUNCTIONS:
                raise ValueError("Only documented math functions are allowed.")
    return tree.body


def evaluate(node, t, temperature, ambient):
    """Evaluate using floating point only; reject invalid/huge results."""
    values = {"t": t, "T": temperature, "ambient": ambient, "pi": math.pi}
    def visit(item):
        # Recursion is bounded by the validated expression size.
        if isinstance(item, ast.Constant):
            return float(item.value)
        if isinstance(item, ast.Name):
            return values[item.id]
        if isinstance(item, ast.UnaryOp):
            return (-1 if isinstance(item.op, ast.USub) else 1) * visit(item.operand)
        if isinstance(item, ast.Call):
            return FUNCTIONS[item.func.id](*(visit(arg) for arg in item.args))
        left, right = visit(item.left), visit(item.right)
        if isinstance(item.op, ast.Pow) and abs(right) > 16:
            raise ValueError("Equation exponents must be between -16 and 16.")
        return BINARY[type(item.op)](left, right)
    try:
        result = float(visit(node))
        if not math.isfinite(result) or abs(result) > 1e12:
            raise ValueError("Equation result must be finite and at most 1e12.")
        return result
    except (ArithmeticError, TypeError, KeyError) as error:
        raise ValueError(f"Equation cannot be evaluated at t={t:g}: {error}") from error
