import ast

def parse_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return ast.parse(f.read())

def get_definitions(tree):
    functions = []
    classes = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes.append(node)
        elif isinstance(node, ast.FunctionDef):
            functions.append(node)

    return classes, functions
