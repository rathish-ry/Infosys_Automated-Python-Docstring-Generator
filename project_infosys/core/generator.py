def _google_params_section(info):
    from core.inference import infer_param_description
    lines = []
    if info["params"]:
        lines.append("Args:")
        for p in info["params"]:
            t = info["annotations"].get(p)
            defaults = info.get("defaults", {})
            default_val = defaults.get(p)
            desc = infer_param_description(p, t)
            
            if t:
                if default_val:
                    lines.append(f"    {p} ({t}, optional): {desc} Defaults to {default_val}.")
                else:
                    lines.append(f"    {p} ({t}): {desc}")
            else:
                if default_val:
                    lines.append(f"    {p} (optional): {desc} Defaults to {default_val}.")
                else:
                    lines.append(f"    {p}: {desc}")
    return lines

def _numpy_params_section(info):
    from core.inference import infer_param_description
    lines = []
    if info["params"]:
        lines.append("Parameters")
        lines.append("----------")
        for p in info["params"]:
            t = info["annotations"].get(p) or "Any"
            defaults = info.get("defaults", {})
            default_val = defaults.get(p)
            desc = infer_param_description(p, t)
            
            lines.append(f"{p} : {t}")
            if default_val:
                lines.append(f"    {desc} Defaults to {default_val}.")
            else:
                lines.append(f"    {desc}")
    return lines

def _rest_params_section(info):
    from core.inference import infer_param_description
    lines = []
    for p in info["params"]:
        t = info["annotations"].get(p)
        defaults = info.get("defaults", {})
        default_val = defaults.get(p)
        desc = infer_param_description(p, t)
        
        if default_val:
            lines.append(f":param {p}: {desc} Defaults to {default_val}.")
        else:
            lines.append(f":param {p}: {desc}")
        if t:
            lines.append(f":type {p}: {t}")
    return lines

def _google_returns_section(info):
    from core.inference import infer_return_description
    lines = []
    if info["return_type"]:
        func_name = info.get("name", "")
        desc = infer_return_description(info["return_type"], func_name)
        lines.append("Returns:")
        lines.append(f"    {info['return_type']}: {desc}")
    return lines

def _numpy_returns_section(info):
    from core.inference import infer_return_description
    lines = []
    if info["return_type"]:
        func_name = info.get("name", "")
        desc = infer_return_description(info["return_type"], func_name)
        lines.append("Returns")
        lines.append("-------")
        lines.append(f"{info['return_type']}")
        lines.append(f"    {desc}")
    return lines

def _rest_returns_section(info):
    from core.inference import infer_return_description
    lines = []
    if info["return_type"]:
        func_name = info.get("name", "")
        desc = infer_return_description(info["return_type"], func_name)
        lines.append(f":returns: {desc}")
        lines.append(f":rtype: {info['return_type']}")
    return lines

def _google_raises_section(info):
    from core.inference import infer_exception_description
    lines = []
    if info.get("raises"):
        lines.append("Raises:")
        for exc in info["raises"]:
            exc_clean = exc.replace("()", "")
            desc = infer_exception_description(exc_clean)
            lines.append(f"    {exc_clean}: {desc}")
    return lines

def _numpy_raises_section(info):
    from core.inference import infer_exception_description
    lines = []
    if info.get("raises"):
        lines.append("Raises")
        lines.append("------")
        for exc in info["raises"]:
            exc_clean = exc.replace("()", "")
            desc = infer_exception_description(exc_clean)
            lines.append(f"{exc_clean}")
            lines.append(f"    {desc}")
    return lines

def _rest_raises_section(info):
    from core.inference import infer_exception_description
    lines = []
    for exc in info.get("raises", []):
        exc_clean = exc.replace("()", "")
        desc = infer_exception_description(exc_clean)
        lines.append(f":raises {exc_clean}: {desc}")
    return lines

def _google_yields_section(info):
    lines = []
    if info.get("is_generator"):
        lines.append("Yields:")
        lines.append("    Any: Description.")
    return lines

def _numpy_yields_section(info):
    lines = []
    if info.get("is_generator"):
        lines.append("Yields")
        lines.append("------")
        lines.append("Any")
        lines.append("    Description")
    return lines

def _rest_yields_section(info):
    lines = []
    if info.get("is_generator"):
        lines.append(":yields: Description")
        lines.append(":yield type: Any")
    return lines


def _capitalize_first_word(text):
    """Capitalize the first word (PEP 257 D403 compliance)."""
    if not text:
        return text
    text = text.strip()
    if text and text[0].islower():
        return text[0].upper() + text[1:]
    return text


def generate_function_docstring(info, description, style="google"):
    """Generate a docstring for a function/method in given style.

    Supported styles: "google", "numpy", "rest" (reStructuredText)
    """
    style = (style or "google").lower()

    summary = (description or "").strip()
    # Capitalize first word (D403)
    summary = _capitalize_first_word(summary)
    # Add period if missing (D400)
    if summary and not summary.endswith("."):
        summary = f"{summary}."

    lines = ['"""', summary]

    sections = []

    if style == "google":
        google_sections = [
            _google_params_section(info),
            _google_returns_section(info),
            _google_raises_section(info),
            _google_yields_section(info),
        ]
        for section in google_sections:
            if section:
                if sections:
                    sections.append("")
                sections.extend(section)
    elif style == "numpy":
        numpy_sections = [
            _numpy_params_section(info),
            _numpy_returns_section(info),
            _numpy_raises_section(info),
            _numpy_yields_section(info),
        ]
        for section in numpy_sections:
            if section:
                if sections:
                    sections.append("")
                sections.extend(section)
    else:  # reStructuredText
        rest_sections = [
            _rest_params_section(info),
            _rest_returns_section(info),
            _rest_raises_section(info),
            _rest_yields_section(info),
        ]
        for section in rest_sections:
            if section:
                if sections:
                    sections.append("")
                sections.extend(section)

    if sections:
        lines.append("")
        lines += sections
    lines.append('"""')
    return "\n".join(lines)

def generate_class_docstring(description, attributes=None, style="google"):
    style = (style or "google").lower()
    summary = (description or "").strip()
    # Capitalize first word (D403)
    summary = _capitalize_first_word(summary)
    # Add period if missing (D400)
    if summary and not summary.endswith("."):
        summary = f"{summary}."

    lines = ['"""', summary]

    attributes = attributes or []
    if attributes:
        lines.append("")
        if style == "google":
            lines.append("Attributes:")
            for a in attributes:
                t = a.get("type")
                if t:
                    lines.append(f"    {a['name']} ({t}): Description.")
                else:
                    lines.append(f"    {a['name']}: Description.")
        elif style == "numpy":
            lines.append("Attributes")
            lines.append("----------")
            for a in attributes:
                t = a.get("type") or "Any"
                lines.append(f"{a['name']} : {t}")
                lines.append("    Description")
        else:
            for a in attributes:
                t = a.get("type")
                lines.append(f":ivar {a['name']}: Description")
                if t:
                    lines.append(f":vartype {a['name']}: {t}")

    lines.append('"""')
    return "\n".join(lines)
