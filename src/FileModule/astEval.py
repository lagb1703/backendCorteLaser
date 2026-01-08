import ast
import builtins
import operator as op
from typing import Dict, Any

class AstEval(ast.NodeVisitor):
    """
    Evaluates a mathematical expression from its AST representation.
    Supports basic arithmetic operations: +, -, *, /, **, %, //.
    """

    # Supported operators
    operators:Dict[Any, Any] = {
        ast.Add: op.add,
        ast.Sub: op.sub,
        ast.Mult: op.mul,
        ast.Div: op.truediv,
        ast.Pow: op.pow,
        ast.Mod: op.mod,
        ast.FloorDiv: op.floordiv,
        ast.USub: op.neg,
    }
    
    ALLOWED_NAMES = {"min", "max", "round"}
    
    def __init__(self, names: Dict[str, Any]):
        self.names = dict(names)

    def visit_BinOp(self, node: ast.BinOp):
        left = self.visit(node.left)
        right = self.visit(node.right)
        operator = self.operators[type(node.op)]
        return operator(left, right)

    def visit_UnaryOp(self, node: ast.UnaryOp):
        operand = self.visit(node.operand)
        operator = self.operators[type(node.op)]
        return operator(operand)

    def visit_Expr(self, node: ast.Expr):
        return self.visit(node.value)

    def visit_Constant(self, node: ast.Constant):
        return node.value

    # For older Python AST compatibility
    def visit_Num(self, node: ast.Num): # type: ignore
        return node.n # type: ignore

    def visit_Call(self, node: ast.Call):
        # only allow calls to simple names in ALLOWED_NAMES
        if isinstance(node.func, ast.Name) and node.func.id in self.ALLOWED_NAMES:
            func = getattr(builtins, node.func.id)
            args = [self.visit(a) for a in node.args]
            kwargs = {str(kw.arg): self.visit(kw.value) for kw in node.keywords}
            return func(*args, **kwargs)
        raise ValueError(f"Function calls not allowed: {ast.dump(node)}")

    def evaluate(self, expression: str) -> Any:
        tree = ast.parse(expression, mode='eval')
        return self.visit(tree.body)
    
    def visit_Name(self, node: ast.Name)-> Any:
        if node.id in self.names:
            return self.names[node.id]
        if node.id in self.ALLOWED_NAMES:
            return getattr(builtins, node.id)
        raise NameError(f"Unknown name: {node.id}")