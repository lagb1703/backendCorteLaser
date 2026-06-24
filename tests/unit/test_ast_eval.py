import pytest
from src.FileModule.astEval import AstEval


class TestAstEval:
    def test_simple_addition(self):
        evaluator = AstEval({})
        result = evaluator.evaluate("2 + 3")
        assert result == 5

    def test_simple_subtraction(self):
        evaluator = AstEval({})
        result = evaluator.evaluate("10 - 4")
        assert result == 6

    def test_simple_multiplication(self):
        evaluator = AstEval({})
        result = evaluator.evaluate("3 * 4")
        assert result == 12

    def test_simple_division(self):
        evaluator = AstEval({})
        result = evaluator.evaluate("12 / 4")
        assert result == 3.0

    def test_power(self):
        evaluator = AstEval({})
        result = evaluator.evaluate("2 ** 3")
        assert result == 8

    def test_modulo(self):
        evaluator = AstEval({})
        result = evaluator.evaluate("10 % 3")
        assert result == 1

    def test_floor_division(self):
        evaluator = AstEval({})
        result = evaluator.evaluate("10 // 3")
        assert result == 3

    def test_unary_minus(self):
        evaluator = AstEval({})
        result = evaluator.evaluate("-5")
        assert result == -5

    def test_complex_expression(self):
        evaluator = AstEval({})
        result = evaluator.evaluate("(2 + 3) * 4 - 1")
        assert result == 19

    def test_with_variables(self):
        evaluator = AstEval({"x": 5, "y": 3})
        result = evaluator.evaluate("x + y * 2")
        assert result == 11

    def test_with_names_min(self):
        evaluator = AstEval({"a": 5, "b": 3})
        result = evaluator.evaluate("min(a, b)")
        assert result == 3

    def test_with_names_max(self):
        evaluator = AstEval({"a": 5, "b": 3})
        result = evaluator.evaluate("max(a, b)")
        assert result == 5

    def test_with_names_round(self):
        evaluator = AstEval({"x": 3.7})
        result = evaluator.evaluate("round(x)")
        assert result == 4

    def test_unknown_name_raises(self):
        evaluator = AstEval({})
        with pytest.raises(NameError):
            evaluator.evaluate("unknown_var")

    def test_disallowed_function_raises(self):
        evaluator = AstEval({})
        with pytest.raises(ValueError):
            evaluator.evaluate("print(5)")

    def test_nested_operations(self):
        evaluator = AstEval({"a": 2, "b": 3, "c": 4})
        result = evaluator.evaluate("a * (b + c) - 1")
        assert result == 13
