"""Exercise the expression grammar, limits and unsafe syntax rejection."""
import pytest
from backend.equations import parse, evaluate


@pytest.mark.parametrize("expression,expected", [
    ("2+3*4-8/2", 10), ("-2 + +3", 1), ("2**3", 8),
    ("sin(pi/2)+cos(0)+sqrt(4)+abs(-3)", 7),
    ("min(2,3)+max(4,5)+exp(0)", 8), ("t+T-ambient", 9)])
def test_math(expression, expected):
    assert evaluate(parse(expression), 2, 300, 293) == pytest.approx(expected)


@pytest.mark.parametrize("expression", ["a", "True", "'text'", "[1]", "T.real", "sin(x=2)",
    "__import__('os')", "t(2)", "2+", "1"*501, "+"*101+"1", "2**17", "1e309", "1e13",
    "1/0", "sqrt(-1)", "exp(1000)", "sin()", "(-1)**0.5", "sin", "(sin)(1,2)"])
def test_reject_invalid(expression):
    with pytest.raises(ValueError):
        evaluate(parse(expression), 0, 293, 293)
