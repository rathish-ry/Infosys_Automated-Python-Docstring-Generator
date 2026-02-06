def infer_function_description(info):
    """Generate a meaningful description based on function name and type signature."""
    name = info["name"]
    return_type = info.get("return_type")
    params = info.get("params", [])

    # Remove 'self' from consideration
    params = [p for p in params if p != "self"]

    if name.startswith("get"):
        what = name[3:].lower().replace("_", " ").strip()
        return f"Retrieve and return {what}." if what else "Retrieve and return data."
    if name.startswith("set"):
        what = name[3:].lower().replace("_", " ").strip()
        if params:
            return f"Set or update {what}." if what else "Set or update the value."
        return f"Set {what}." if what else "Set the value."
    if name.startswith("is") or name.startswith("has"):
        what = (name[2:].lower().replace("_", " ") if name.startswith("is") else name[3:].lower().replace("_", " ")).strip()
        return f"Check if {what} and return a boolean result." if what else "Check a condition and return a boolean."
    if name.startswith("calculate") or name.startswith("compute"):
        what = (name[9:].lower().replace("_", " ") if name.startswith("calculate") else name[7:].lower().replace("_", " ")).strip()
        return f"Compute and return {what}." if what else "Compute and return a value."
    if name.startswith("process"):
        what = name[7:].lower().replace("_", " ").strip()
        if what:
            return f"Process {what}."
        elif params:
            param_name = params[0].lower().replace("_", " ")
            return f"Process a {param_name}."
        return "Process the provided input."
    if name.startswith("validate") or name.startswith("check"):
        what = (name[8:].lower().replace("_", " ") if name.startswith("validate") else name[5:].lower().replace("_", " ")).strip()
        return f"Validate or check {what}." if what else "Validate the input."
    if name.startswith("parse"):
        what = name[5:].lower().replace("_", " ").strip()
        return f"Parse {what}." if what else "Parse the input."
    if name.startswith("format") or name.startswith("convert"):
        what = (name[6:].lower().replace("_", " ") if name.startswith("format") else name[7:].lower().replace("_", " ")).strip()
        return f"Format or convert {what}." if what else "Format or convert the input."

    # Generic fallback based on return type
    if return_type:
        if "list" in return_type.lower():
            return "Return a list of results."
        elif "dict" in return_type.lower():
            return "Return a dictionary of results."
        elif "bool" in return_type.lower():
            return "Return a boolean result."
        elif "str" in return_type.lower():
            return "Return a string result."

    # Final fallback: describe based on params
    if params:
        param_desc = " and ".join(params)
        return f"Perform operation with {param_desc}."

    return "Execute the operation."

def infer_param_description(param_name, param_type=None):
    """Generate a meaningful parameter description."""
    name = param_name.lower().replace("_", " ").strip()
    
    if param_name in ("self", "cls"):
        return "The class or instance."
    
    if param_type:
        if "list" in param_type.lower():
            singular = name.rstrip("s") if name.endswith("s") else name
            return f"A list of {singular}."
        elif "dict" in param_type.lower():
            return f"A dictionary containing {name}."
        elif "bool" in param_type.lower():
            return f"Whether to {name}."
        elif "str" in param_type.lower():
            return f"The {name} as a string."
        elif "int" in param_type.lower():
            if "index" in name or "count" in name or "num" in name:
                return f"The {name}."
            return f"The {name} value."
        elif "float" in param_type.lower():
            return f"The {name} as a float."
    
    # Generic descriptions by parameter name patterns
    if "data" in param_name.lower():
        return f"The {name} to process."
    if "item" in param_name.lower():
        return f"A single {name}."
    if "index" in param_name.lower():
        return f"The {name}."
    if "value" in param_name.lower():
        return f"The {name} to set."
    if "count" in param_name.lower() or "num" in param_name.lower():
        return f"The number or {name}."
    if "flag" in param_name.lower() or "enabled" in param_name.lower() or "is_" in param_name.lower():
        clean_name = name.replace("is ", "").strip()
        return f"Whether to enable {clean_name}."
    if "path" in param_name.lower():
        return f"The file or directory {name}."
    if "name" in param_name.lower():
        return f"The {name}."

    return f"The {name}."

def infer_return_description(return_type, func_name):
    """Generate a meaningful return description."""
    if not return_type:
        return "The result of the operation."
    
    func_name_lower = func_name.lower()
    return_type_lower = return_type.lower()

    # Type-specific descriptions
    if "optional" in return_type_lower:
        inner_type = return_type_lower.replace("optional", "").replace("[", "").replace("]", "").strip()
        if inner_type:
            return f"The {inner_type}, or None if not available."
        return "The result, or None if not available."

    if "list" in return_type_lower:
        return "A list of results."
    if "dict" in return_type_lower:
        return "A dictionary of results."
    if "tuple" in return_type_lower:
        return "A tuple of results."
    if "bool" in return_type_lower:
        return "True if successful, False otherwise."
    if "str" in return_type_lower:
        if "process" in func_name_lower or "format" in func_name_lower:
            return "The processed or formatted string."
        return "The resulting string."
    if "int" in return_type_lower:
        return "The resulting integer value."
    if "float" in return_type_lower:
        return "The resulting float value."

    # Function pattern based
    if "process" in func_name_lower:
        return f"The processed {return_type}."
    if "calculate" in func_name_lower or "compute" in func_name_lower:
        return f"The calculated {return_type}."
    if "get" in func_name_lower:
        return f"The requested {return_type}."

    return f"The {return_type} result."

def infer_class_description(class_name):
    return f"Manages {class_name.lower()} functionality."

def infer_exception_description(exception_name):
    """Generate a meaningful exception description."""
    exc_name = exception_name.replace("Error", "").replace("Exception", "").lower().replace("_", " ")
    
    if "value" in exc_name:
        return f"If an invalid {exc_name} is provided."
    if "type" in exc_name:
        return f"If an incorrect type is provided."
    if "key" in exc_name:
        return f"If a required key is missing."
    if "attribute" in exc_name:
        return f"If an attribute does not exist."
    if "index" in exc_name:
        return f"If an index is out of range."
    if "argument" in exc_name or "arg" in exc_name:
        return f"If an invalid argument is provided."

    return f"If {exc_name} occurs."
