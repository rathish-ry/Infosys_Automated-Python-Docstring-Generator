import ast
import builtins
import difflib
from typing import List, Dict

from pydocstyle import check


# ---------------- PEP 257 VALIDATION ----------------

def run_pydocstyle(file_path: str) -> List[Dict]:
    """Run pydocstyle on a file and return structured issues."""
    issues = []

    for err in check([file_path]):
        definition = getattr(err, "definition", None)
        def_name = getattr(definition, "name", None)
        kind = getattr(definition, "kind", None) or "module"
        parent = getattr(definition, "parent", None)
        parent_name = getattr(parent, "name", None)

        if kind == "method" and parent_name:
            full_name = f"{parent_name}.{def_name}"
        else:
            full_name = def_name or "module"

        code = getattr(err, "code", None) or getattr(err, "error_code", None) or "D000"
        message = getattr(err, "short_desc", None) or getattr(err, "message", None) or str(err)
        line = getattr(err, "line", None) or getattr(err, "line_number", None) or 0

        issues.append({
            "code": code,
            "message": message,
            "line": line,
            "name": full_name,
            "kind": kind,
        })

    return issues


# ---------------- CODE QUALITY VALIDATOR ----------------

class CodeValidator(ast.NodeVisitor):
    """AST visitor to detect code quality issues."""

    def __init__(self):
        self.issues = []
        self.scopes = [set(dir(builtins))]

        self.known_methods = {
            'upper', 'lower', 'strip', 'split', 'join', 'replace', 'find',
            'startswith', 'endswith', 'isdigit', 'isalpha', 'capitalize',
            'title', 'format', 'encode', 'decode', 'lstrip', 'rstrip',
            'count', 'append', 'extend', 'insert', 'remove', 'pop',
            'clear', 'index', 'sort', 'reverse', 'copy',
            'keys', 'values', 'items', 'get', 'update', 'setdefault'
        }

    # -------- Infrastructure --------

    def generic_visit(self, node):
        for child in ast.iter_child_nodes(node):
            child.parent = node
        super().generic_visit(node)

    def enter_scope(self):
        self.scopes.append(set())

    def exit_scope(self):
        if len(self.scopes) > 1:
            self.scopes.pop()

    def add_name(self, name: str):
        self.scopes[-1].add(name)

    def is_defined(self, name: str) -> bool:
        return any(name in scope for scope in reversed(self.scopes))

    # -------- Visitors --------

    def visit_ClassDef(self, node):
        self.add_name(node.name)
        self.enter_scope()
        self.generic_visit(node)
        self.exit_scope()

    def visit_FunctionDef(self, node):
        self.enter_scope()

        for arg in node.args.args:
            self.add_name(arg.arg)
            if arg.annotation:
                self.check_annotation(arg.annotation, node.lineno)

        if node.returns:
            self.check_annotation(node.returns, node.lineno)

        self.generic_visit(node)
        self.exit_scope()

    def visit_Assign(self, node):
        # Validate RHS first
        self.visit(node.value)

        # Register LHS names
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.add_name(target.id)

    def visit_AnnAssign(self, node):
        if isinstance(node.target, ast.Name):
            self.add_name(node.target.id)
        if node.value:
            self.visit(node.value)

    def visit_For(self, node):
        if isinstance(node.target, ast.Name):
            self.add_name(node.target.id)
        self.generic_visit(node)

    def visit_With(self, node):
        for item in node.items:
            if item.optional_vars and isinstance(item.optional_vars, ast.Name):
                self.add_name(item.optional_vars.id)
        self.generic_visit(node)

    def visit_ListComp(self, node):
        """Handle list comprehensions to register loop variables."""
        self.enter_scope()
        for generator in node.generators:
            if isinstance(generator.target, ast.Name):
                self.add_name(generator.target.id)
            elif isinstance(generator.target, ast.Tuple):
                for elt in generator.target.elts:
                    if isinstance(elt, ast.Name):
                        self.add_name(elt.id)
            self.visit(generator.iter)
            for if_clause in generator.ifs:
                self.visit(if_clause)
        self.visit(node.elt)
        self.exit_scope()

    def visit_SetComp(self, node):
        """Handle set comprehensions to register loop variables."""
        self.enter_scope()
        for generator in node.generators:
            if isinstance(generator.target, ast.Name):
                self.add_name(generator.target.id)
            elif isinstance(generator.target, ast.Tuple):
                for elt in generator.target.elts:
                    if isinstance(elt, ast.Name):
                        self.add_name(elt.id)
            self.visit(generator.iter)
            for if_clause in generator.ifs:
                self.visit(if_clause)
        self.visit(node.elt)
        self.exit_scope()

    def visit_DictComp(self, node):
        """Handle dict comprehensions to register loop variables."""
        self.enter_scope()
        for generator in node.generators:
            if isinstance(generator.target, ast.Name):
                self.add_name(generator.target.id)
            elif isinstance(generator.target, ast.Tuple):
                for elt in generator.target.elts:
                    if isinstance(elt, ast.Name):
                        self.add_name(elt.id)
            self.visit(generator.iter)
            for if_clause in generator.ifs:
                self.visit(if_clause)
        self.visit(node.key)
        self.visit(node.value)
        self.exit_scope()

    def visit_GeneratorExp(self, node):
        """Handle generator expressions to register loop variables."""
        self.enter_scope()
        for generator in node.generators:
            if isinstance(generator.target, ast.Name):
                self.add_name(generator.target.id)
            elif isinstance(generator.target, ast.Tuple):
                for elt in generator.target.elts:
                    if isinstance(elt, ast.Name):
                        self.add_name(elt.id)
            self.visit(generator.iter)
            for if_clause in generator.ifs:
                self.visit(if_clause)
        self.visit(node.elt)
        self.exit_scope()

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            name = node.id

            if name in ('self', 'cls', 'True', 'False', 'None'):
                return

            if not self.is_defined(name):
                suggestions = difflib.get_close_matches(
                    name,
                    {n for scope in self.scopes for n in scope},
                    n=1,
                    cutoff=0.8
                )

                msg = f"Undefined name '{name}'"
                if suggestions:
                    msg += f" - did you mean '{suggestions[0]}'?"

                self.issues.append({
                    "code": "E821",
                    "message": msg,
                    "line": node.lineno
                })

    def visit_Attribute(self, node):
        # Detect method typos by checking attribute names against known methods
        if hasattr(node, 'attr'):
            attr = node.attr
            matches = difflib.get_close_matches(
                attr, self.known_methods, n=1, cutoff=0.6
            )

            if matches and matches[0] != attr:
                self.issues.append({
                    "code": "W001",
                    "message": f"Potential typo: '{attr}()' - did you mean '{matches[0]}()'?",
                    "line": node.lineno
                })

        self.generic_visit(node)

    # -------- Annotation checks --------

    def check_annotation(self, annotation, line_no):
        if isinstance(annotation, ast.Name):
            name = annotation.id
            valid = {
                'int', 'str', 'float', 'bool', 'list', 'dict', 'tuple', 'set',
                'Any', 'Optional', 'Union', 'List', 'Dict', 'Tuple', 'Set',
                'None', 'type', 'object', 'bytes'
            }

            if name not in valid and not self.is_defined(name):
                self.issues.append({
                    "code": "E821",
                    "message": f"Undefined type '{name}' in annotation",
                    "line": line_no
                })

        elif isinstance(annotation, ast.Subscript):
            self.check_annotation(annotation.value, line_no)
            if isinstance(annotation.slice, ast.Tuple):
                for elt in annotation.slice.elts:
                    self.check_annotation(elt, line_no)
            else:
                self.check_annotation(annotation.slice, line_no)


# ---------------- ENTRY POINT ----------------

def validate_code_quality(file_path: str):
    """Validate code for potential runtime errors and quality issues."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
    except SyntaxError as e:
        return [{"code": "E901", "message": e.msg, "line": e.lineno}]

    validator = CodeValidator()
    validator.visit(tree)
    validator.issues.sort(key=lambda x: x["line"])
    return validator.issues
