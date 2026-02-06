def coverage_report(functions, classes):
    total = len(functions) + len(classes)
    documented = (
        sum(1 for f in functions if f["has_docstring"]) +
        sum(1 for c in classes if c["has_docstring"])
    )

    percent = (documented / total * 100) if total else 0

    return {
        "total_definitions": total,
        "documented": documented,
        "coverage_percent": round(percent, 2)
    }
