import ast

def extract_function_data(func, class_name=None):
    params = []
    annotations = {}
    defaults = {}

    docstring = ast.get_docstring(func)

    # Extract defaults (they align with the last N parameters)
    num_defaults = len(func.args.defaults)
    num_args = len(func.args.args)
    
    for i, arg in enumerate(func.args.args):
        params.append(arg.arg)
        annotations[arg.arg] = ast.unparse(arg.annotation) if arg.annotation else None
        
        # Check if this arg has a default
        default_idx = i - (num_args - num_defaults)
        if default_idx >= 0:
            defaults[arg.arg] = ast.unparse(func.args.defaults[default_idx])

    return_type = ast.unparse(func.returns) if func.returns else None

    # Detect raises
    raises = []
    for node in ast.walk(func):
        if isinstance(node, ast.Raise) and node.exc is not None:
            try:
                raises.append(ast.unparse(node.exc))
            except Exception:
                raises.append("Exception")

    # Detect generator behavior
    is_generator = any(isinstance(n, (ast.Yield, ast.YieldFrom)) for n in ast.walk(func))

    return {
        "name": func.name,
        "class": class_name,
        "params": params,
        "annotations": annotations,
        "defaults": defaults,
        "return_type": return_type,
        "has_docstring": docstring is not None,
        "docstring": docstring,
        "type": "method" if class_name else "function",
        "raises": raises,
        "is_generator": is_generator,
        "line": func.lineno,
    }

def extract_class_data(cls):
    # Collect simple class-level attributes
    attributes = []
    docstring = ast.get_docstring(cls)
    for node in cls.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    inferred_type = None
                    if hasattr(node, 'value'):
                        inferred_type = _infer_type_from_value(node.value)
                    attributes.append({"name": target.id, "type": inferred_type})
    
    # Extract __init__ parameters as instance attributes
    for node in cls.body:
        if isinstance(node, ast.FunctionDef) and node.name == "__init__":
            for arg in node.args.args:
                if arg.arg != "self":
                    arg_type = ast.unparse(arg.annotation) if arg.annotation else None
                    if not any(a["name"] == arg.arg for a in attributes):
                        attributes.append({"name": arg.arg, "type": arg_type})

    return {
        "name": cls.name,
        "has_docstring": docstring is not None,
        "docstring": docstring,
        "attributes": attributes,
        "line": cls.lineno,
    }

def _infer_type_from_value(node):
    """Infer Python type name from AST value node."""
    if isinstance(node, ast.List):
        return "list"
    elif isinstance(node, ast.Dict):
        return "dict"
    elif isinstance(node, ast.Tuple):
        return "tuple"
    elif isinstance(node, ast.Constant):
        if isinstance(node.value, str):
            return "str"
        elif isinstance(node.value, bool):
            return "bool"
        elif isinstance(node.value, int):
            return "int"
        elif isinstance(node.value, float):
            return "float"
    elif isinstance(node, ast.Name):
        return node.id
    return None
