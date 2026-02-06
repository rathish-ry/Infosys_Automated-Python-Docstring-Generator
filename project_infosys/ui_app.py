import streamlit as st
import os
import ast
from core.parser import parse_file, get_definitions
from core.extractor import extract_function_data, extract_class_data
from core.inference import infer_function_description, infer_class_description
from core.generator import generate_function_docstring, generate_class_docstring
from core.coverage import coverage_report
from core.validator import validate_code_quality, run_pydocstyle
from core.fixer import CodeFixer
from core.config_loader import load_project_config, get_config_with_defaults
from tempfile import NamedTemporaryFile


def calculate_coverage(all_functions, all_classes):
    """Calculate docstring coverage percentage.
    
    Formula: (classes with docstrings + functions with docstrings) 
             / (total classes + total functions) * 100
    """
    if not all_functions and not all_classes:
        return 0.0
    
    classes_with_docs = sum(1 for cls in all_classes if cls.get("has_docstring", False))
    funcs_with_docs = sum(1 for func in all_functions if func.get("has_docstring", False))
    
    total = len(all_classes) + len(all_functions)
    if total == 0:
        return 0.0
    
    coverage = (classes_with_docs + funcs_with_docs) / total * 100
    return round(coverage, 1)


def extract_original_docstrings(file_path):
    """Extract all docstrings from the original file.
    
    Returns a dict mapping (type, name) -> docstring_text
    """
    try:
        tree = parse_file(file_path)
    except:
        return {}
    
    docstrings = {}
    
    # Module docstring
    module_doc = ast.get_docstring(tree)
    if module_doc:
        docstrings[('module', 'module')] = module_doc
    
    # Class docstrings
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            doc = ast.get_docstring(node)
            if doc:
                docstrings[('class', node.name)] = doc
        elif isinstance(node, ast.FunctionDef):
            doc = ast.get_docstring(node)
            if doc:
                docstrings[('function', node.name)] = doc
    
    return docstrings


def generate_fix_summary(original_file_path, all_classes, all_functions, 
                        code_issues_before, coverage_before, coverage_after, 
                        normalize_docstrings, fix_code_errors):
    """Generate a summary of all fixes applied during the generation run.
    
    Returns a dictionary with fix counts and coverage changes.
    """
    # Get original docstrings
    original_docs = extract_original_docstrings(original_file_path)
    
    # Count docstrings generated (new ones for items that had none)
    docstrings_generated = sum(1 for func in all_functions if not func.get("has_docstring", False))
    docstrings_generated += sum(1 for cls in all_classes if not cls.get("has_docstring", False))
    
    # Count existing docstrings normalized (had docstring before, regenerated = changed)
    # In the current implementation with normalize_existing_docstrings=True,
    # all existing docstrings are regenerated, so count them if they existed before
    docstrings_normalized = 0
    if normalize_docstrings:
        docstrings_normalized = sum(1 for func in all_functions if func.get("has_docstring", False))
        docstrings_normalized += sum(1 for cls in all_classes if cls.get("has_docstring", False))
    
    # Count code fixes (E821 and W001)
    e821_count = 0
    w001_count = 0
    
    if fix_code_errors and code_issues_before:
        for issue in code_issues_before:
            if issue.get("code") == "E821":
                e821_count += 1
            elif issue.get("code") == "W001":
                w001_count += 1
    
    # Build summary
    summary = {
        "docstrings_generated": docstrings_generated,
        "docstrings_normalized": docstrings_normalized,
        "code_errors_fixed_e821": e821_count,
        "typos_fixed_w001": w001_count,
        "coverage_before": coverage_before,
        "coverage_after": coverage_after,
    }
    
    return summary


def _render_docstring_block(docstring: str, indent: str = ""):
    """Return a docstring block (with quotes) indented for stub generation."""
    if docstring is None:
        return []

    text = docstring or ""
    if text.strip().startswith('"""'):
        lines = text.splitlines()
    else:
        lines = ['"""'] + text.splitlines() + ['"""']

    return [f"{indent}{line}" for line in lines]


def generate_module_docstring(all_classes, all_functions):
    """Generate a PEP 257-compliant module-level docstring based on classes and functions."""
    # Simple, brief module docstring following PEP 257
    docstring = "Module providing utilities for data processing, validation, and analysis.\n"
    return docstring


def merge_docstrings_into_code(file_path, all_classes, all_functions, style_key):
    """Merge generated docstrings into the original Python file."""
    from core.fixer import remove_existing_docstrings
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # STEP 1: Remove all existing docstrings
    content = remove_existing_docstrings(content)
    
    # STEP 2: Parse the code WITHOUT docstrings to get CORRECT line numbers
    original_lines = content.splitlines(keepends=True)
    tree = ast.parse(content)  # Parse the content AFTER docstring removal
    
    # STEP 3: Re-extract classes and functions from the NEW parsed tree (with correct line numbers)
    new_classes, new_functions = get_definitions(tree)
    
    # Build lookup maps by name to get the corrected line numbers
    class_map = {cls.name: cls for cls in new_classes}
    func_map = {func.name: func for func in new_functions}
    
    # Create a list of (line_number, docstring) tuples for insertion
    insertions = []
    
    # Check if module docstring exists (PEP 257 requirement)
    module_docstring = ast.get_docstring(tree)
    if not module_docstring:
        # Generate module docstring if missing
        generated_module_doc = generate_module_docstring(all_classes, all_functions)
        if generated_module_doc:
            doc_lines = _render_docstring_block(generated_module_doc, "")
            insertions.append((0, '\n'.join(doc_lines) + '\n\n'))
    
    # STEP 4: Generate and insert ALL docstrings for functions
    for func_data in all_functions:
        func_name = func_data.get("name")
        class_name = func_data.get("class")
        
        # Find the function in the new parsed tree
        func_node = None
        if class_name:
            # Method in a class
            cls_node = class_map.get(class_name)
            if cls_node:
                for node in cls_node.body:
                    if hasattr(node, 'name') and node.name == func_name:
                        func_node = node
                        break
        else:
            # Top-level function
            func_node = func_map.get(func_name)
        
        if func_node:
            # Generate docstring for ALL functions
            docstring = generate_function_docstring(
                func_data,
                infer_function_description(func_data),
                style=style_key
            )
            
            # Use the CORRECTED line number from the new tree
            line_num = func_node.lineno
            if line_num > 0 and line_num <= len(original_lines):
                # Get the indent from the def line
                def_line = original_lines[line_num - 1]
                base_indent = len(def_line) - len(def_line.lstrip())
                docstring_indent = ' ' * (base_indent + 4)
                
                # Check if docstring is simple one-liner (for D200 compliance)
                docstring_lines = docstring.splitlines()
                if len(docstring_lines) == 3 and docstring_lines[0] == '"""' and docstring_lines[2] == '"""':
                    # Simple one-liner - format it on one line
                    summary = docstring_lines[1]
                    if len(docstring_indent + '"""' + summary + '"""') <= 88:  # PEP 8 line length
                        docstring = f'"""{summary}"""'
                        doc_lines = [f"{docstring_indent}{docstring}"]
                    else:
                        # Too long, keep multiline
                        doc_lines = _render_docstring_block(docstring, docstring_indent)
                else:
                    # Multi-line docstring with parameters
                    doc_lines = _render_docstring_block(docstring, docstring_indent)
                
                insertions.append((line_num, '\n'.join(doc_lines) + '\n'))
    
    # STEP 5: Generate and insert ALL docstrings for classes
    for cls_data in all_classes:
        cls_name = cls_data.get("name")
        cls_node = class_map.get(cls_name)
        
        if cls_node:
            # Generate docstring for ALL classes
            docstring = generate_class_docstring(
                infer_class_description(cls_name),
                attributes=cls_data.get("attributes", []),
                style=style_key
            )
            
            # Use the CORRECTED line number from the new tree
            line_num = cls_node.lineno
            if line_num > 0 and line_num <= len(original_lines):
                def_line = original_lines[line_num - 1]
                base_indent = len(def_line) - len(def_line.lstrip())
                docstring_indent = ' ' * (base_indent + 4)
                
                # Check if docstring is simple one-liner (for D200 compliance)
                docstring_lines = docstring.splitlines()
                if len(docstring_lines) == 3 and docstring_lines[0] == '"""' and docstring_lines[2] == '"""':
                    # Simple one-liner - format it on one line
                    summary = docstring_lines[1]
                    if len(docstring_indent + '"""' + summary + '"""') <= 88:  # PEP 8 line length
                        docstring = f'"""{summary}"""'
                        doc_lines = [f"{docstring_indent}{docstring}"]
                    else:
                        # Too long, keep multiline
                        doc_lines = _render_docstring_block(docstring, docstring_indent)
                else:
                    # Multi-line docstring with attributes
                    doc_lines = _render_docstring_block(docstring, docstring_indent)
                
                # Add blank line after class docstring (D204 compliance - exactly 1 blank line)
                insertions.append((line_num, '\n'.join(doc_lines) + '\n\n'))
    
    # STEP 6: Sort insertions by line number (reverse order to maintain line numbers)
    insertions.sort(key=lambda x: x[0], reverse=True)
    
    # STEP 7: Insert new docstrings into the code
    modified_lines = original_lines[:]
    for line_num, docstring_text in insertions:
        # Insert after the def/class line
        if line_num <= len(modified_lines):
            modified_lines.insert(line_num, docstring_text)
    
    return ''.join(modified_lines)


def build_pydocstyle_stub(module_docstring, classes, functions, style_key):
    """Build a temporary Python file containing docstrings to validate with pydocstyle."""
    lines = []

    if module_docstring:
        lines += _render_docstring_block(module_docstring)
        lines.append("")

    # Group methods by class
    methods_by_class = {}
    for func in functions:
        if func["class"]:
            methods_by_class.setdefault(func["class"], []).append(func)

    # Classes and their methods
    for cls in classes:
        lines.append(f"class {cls['name']}:")
        cls_doc = cls.get("docstring") or generate_class_docstring(
            infer_class_description(cls["name"]),
            attributes=cls.get("attributes", []),
            style=style_key,
        )
        lines += _render_docstring_block(cls_doc, indent="    ")

        class_methods = methods_by_class.get(cls["name"], [])
        if not class_methods:
            lines.append("    pass")
        else:
            for func in class_methods:
                params = ", ".join(func["params"]) if func["params"] else "self"
                lines.append("")
                lines.append(f"    def {func['name']}({params}):")
                func_doc = func.get("docstring") or generate_function_docstring(
                    func,
                    infer_function_description(func),
                    style=style_key,
                )
                lines += _render_docstring_block(func_doc, indent="        ")
                lines.append("        pass")

        lines.append("")

    # Top-level functions
    for func in [f for f in functions if not f["class"]]:
        params = ", ".join(func["params"]) if func["params"] else ""
        lines.append(f"def {func['name']}({params}):")
        func_doc = func.get("docstring") or generate_function_docstring(
            func,
            infer_function_description(func),
            style=style_key,
        )
        lines += _render_docstring_block(func_doc, indent="    ")
        lines.append("    pass")
        lines.append("")

    return "\n".join(lines)

st.set_page_config(page_title="Python Docstring Generator & Validator", layout="wide")

st.title("Python Docstring Generator & Validator")
st.caption("AI-Powered Documentation Generation with PEP 257 Compliance Analysis")

# -------- Load Project Configuration --------
project_config = load_project_config(workspace_root=os.getcwd())
config = get_config_with_defaults(project_config)

# Store config in session state for use throughout the app
if 'project_config' not in st.session_state:
    st.session_state.project_config = config

# Update with session state
config = st.session_state.project_config

# ---------------- Sidebar ----------------
st.sidebar.header("📁 Upload Python File")

uploaded_file = st.sidebar.file_uploader("Choose a Python file", type=["py"])

# Style selection
st.sidebar.header("🧾 Docstring Styles")
style_options = ["Google", "NumPy", "reST"]
default_style_index = style_options.index(config["docstring_style"].capitalize()) if config["docstring_style"].lower() in ["google", "numpy", "rest"] else 0
style = st.sidebar.radio("Select style", style_options, index=default_style_index)
style_key = {"Google": "google", "NumPy": "numpy", "reST": "rest"}[style]

# Display loaded configuration
st.sidebar.markdown("---")
st.sidebar.header("⚙️ Configuration")
with st.sidebar.expander("View Configuration", expanded=False):
    st.write("**Configuration Values:**")
    
    # Docstring Style
    config_style = config["docstring_style"]
    active_style = style_key
    st.write(f"**Docstring Style**")
    st.write(f"  - Config file: `{config_style}`")
    st.write(f"  - Active value: `{active_style}`")
    
    st.write("")
    
    # Code Error Fixing
    st.write(f"**Fix Code Errors:** `{config['fix_code_errors']}`")
    
    st.write("")
    
    # Normalize Docstrings
    st.write(f"**Normalize Docstrings:** `{config['normalize_existing_docstrings']}`")
    
    st.write("")
    
    # Min Coverage
    st.write(f"**Min Coverage:** `{config['min_coverage']}%`")
    
    st.write("")
    st.markdown("---")
    
    # Configuration source
    if project_config:
        st.write("**Source:** Loaded from `pyproject.toml` [tool.docgen]")
    else:
        st.write("**Source:** Default values (no `pyproject.toml` found)")

py_files = []
file_coverages = {}

if uploaded_file is None:
    st.info("👈 Please upload a Python file to get started")
    st.stop()

# Save uploaded file temporarily
temp_file_path = f"temp_{uploaded_file.name}"
with open(temp_file_path, "wb") as f:
    f.write(uploaded_file.getbuffer())

py_files = [temp_file_path]

# ---------------- Main Scan ----------------
all_functions = []
all_classes = []

ast_logs = []

for file in py_files:
    tree = parse_file(file)
    classes, functions = get_definitions(tree)

    ast_logs.append(f"Parsed {file}")
    ast_logs.append(f"Classes: {len(classes)}, Functions: {len(functions)}")

    for cls in classes:
        all_classes.append(extract_class_data(cls))

        for node in cls.body:
            if node.__class__.__name__ == "FunctionDef":
                all_functions.append(
                    extract_function_data(node, class_name=cls.name)
                )

    for func in functions:
        if not any(func in cls.body for cls in classes):
            all_functions.append(extract_function_data(func))

    file_coverages[file] = 100  # placeholder per-file score

# Track items missing docstrings (used to label generated items later)
generated_class_names = [cls["name"] for cls in all_classes if not cls["has_docstring"]]
generated_func_names = [
    f"{func['class']}.{func['name']}" if func["class"] else func["name"]
    for func in all_functions if not func["has_docstring"]
]
missing_count = len(generated_class_names) + len(generated_func_names)

# Calculate coverage BEFORE generation
coverage_before = calculate_coverage(all_functions, all_classes)

# Pre-generation: Validate the uploaded file (original code)
# This MUST be done BEFORE fixing issues, to show the "before" state
pydocstyle_issues_before = run_pydocstyle(temp_file_path)
code_issues_before = validate_code_quality(temp_file_path)

# AUTOMATIC CODE FIXING: Fix any code issues detected before generation
# Only apply fixes if fix_code_errors is enabled in configuration
# Create a separate fixed version - NEVER modify the original uploaded file
fixed_temp_path = temp_file_path  # Default to original if no fixes needed
if code_issues_before and config["fix_code_errors"]:
    st.info("🔧 Automatically fixing detected code issues...")
    fixer = CodeFixer(temp_file_path)
    fixed_code = fixer.fix_issues(code_issues_before)
    
    # Save the fixed code to a SEPARATE file - keep original untouched
    fixed_temp_path = f"fixed_{uploaded_file.name}"
    with open(fixed_temp_path, 'w', encoding='utf-8') as f:
        f.write(fixed_code)
    
    # Re-parse the fixed code to update AST data
    tree = parse_file(fixed_temp_path)
    classes, functions = get_definitions(tree)
    
    all_classes = []
    all_functions = []
    
    for cls in classes:
        all_classes.append(extract_class_data(cls))
        for node in cls.body:
            if node.__class__.__name__ == "FunctionDef":
                all_functions.append(
                    extract_function_data(node, class_name=cls.name)
                )
    
    for func in functions:
        if not any(func in cls.body for cls in classes):
            all_functions.append(extract_function_data(func))
    
    # Update tracking lists after fix
    generated_class_names = [cls["name"] for cls in all_classes if not cls["has_docstring"]]
    generated_func_names = [
        f"{func['class']}.{func['name']}" if func["class"] else func["name"]
        for func in all_functions if not func["has_docstring"]
    ]
    missing_count = len(generated_class_names) + len(generated_func_names)

# Build merged code based on configuration
# If normalize_existing_docstrings is True: regenerate docstrings for PEP 257 compliance
# If False: skip docstring processing entirely
if config["normalize_existing_docstrings"]:
    merged_code = merge_docstrings_into_code(fixed_temp_path, all_classes, all_functions, style_key)
else:
    # Skip docstring processing, just use the fixed code as-is
    with open(fixed_temp_path, 'r', encoding='utf-8') as f:
        merged_code = f.read()

# Create a temporary file for the generated output (for AFTER analysis)
generated_temp_path = None
with NamedTemporaryFile("w", suffix=".py", delete=False) as tmp:
    tmp.write(merged_code)
    generated_temp_path = tmp.name

# Sidebar file info
st.sidebar.success(f"✅ Uploaded: {uploaded_file.name}")

# ---------------- AST OUTPUT ----------------
st.subheader("🔗 AST Parsing Output")
with st.expander("View AST Parsing Logs", expanded=True):
    st.code("\n".join(ast_logs), language="text")

# Function to render validation and coverage analytics
def render_analytics(
    all_functions,
    all_classes,
    pydocstyle_issues_input,
    code_issues_input,
    style_key,
    title="Analytics",
    key_prefix="",
    is_after_generation=False,
    source_path=None,
    generated_class_names=None,
    generated_func_names=None,
    module_generated=False,
):
    """Render validation results and coverage analytics."""
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    
    st.subheader(title)
    
    errors_by_name = {}
    for issue in pydocstyle_issues_input:
        key = issue.get("name") or "module"
        errors_by_name.setdefault(key, []).append(issue)
    
    doc_results = []
    compliant = 0
    documented_count = 0  # Count of items with actual docstrings
    
    # Module entry
    source_path = source_path or temp_file_path
    module_docstring = ast.get_docstring(parse_file(source_path))
    module_issues = errors_by_name.get("module", [])
    has_module_doc = module_docstring is not None
    
    # For "Before", compliant means has docstring AND no issues
    # For "After", compliant means no issues (all should have docstrings)
    if has_module_doc:
        documented_count += 1
        if not module_issues:
            compliant += 1
    
    # Determine status based on whether this is before or after generation
    if has_module_doc:
        module_status = "✅ Existing"
    else:
        if is_after_generation and module_generated:
            module_status = "🆕 Generated"
        else:
            module_status = "❌ Missing"
    
    doc_results.append({
        "name": "module",
        "type": "module",
        "status": module_status,
        "issues": "; ".join([f"{i['code']}: {i['message']}" for i in module_issues]) if module_issues else "None",
        "compliant": has_module_doc and len(module_issues) == 0
    })

    # Classes
    for cls in all_classes:
        cls_key = cls["name"]
        issues = errors_by_name.get(cls_key, [])
        has_doc = cls["has_docstring"]
        
        if has_doc:
            documented_count += 1
            if len(issues) == 0:
                compliant += 1

        # Determine status
        if has_doc:
            if is_after_generation and generated_class_names and cls_key in generated_class_names:
                cls_status = "🆕 Generated"
            else:
                cls_status = "✅ Existing"
        else:
            cls_status = "❌ Missing"
        
        doc_results.append({
            "name": cls_key,
            "type": "class",
            "status": cls_status,
            "issues": "; ".join([f"{i['code']}: {i['message']}" for i in issues]) if issues else "None",
            "compliant": has_doc and len(issues) == 0
        })

    # Functions/Methods
    for func in all_functions:
        label = "Method" if func["class"] else "Function"
        name = f"{func['class']}.{func['name']}" if func["class"] else func["name"]
        func_key = name
        issues = errors_by_name.get(func_key, [])
        has_doc = func["has_docstring"]
        
        if has_doc:
            documented_count += 1
            if len(issues) == 0:
                compliant += 1

        # Determine status
        if has_doc:
            if is_after_generation and generated_func_names and name in generated_func_names:
                func_status = "🆕 Generated"
            else:
                func_status = "✅ Existing"
        else:
            func_status = "❌ Missing"
        
        doc_results.append({
            "name": name,
            "type": label.lower(),
            "status": func_status,
            "issues": "; ".join([f"{i['code']}: {i['message']}" for i in issues]) if issues else "None",
            "compliant": has_doc and len(issues) == 0
        })
    
    doc_errors = sum(1 for r in doc_results if not r["compliant"])
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Code Issues", len(code_issues_input), delta=None if len(code_issues_input) == 0 else f"-{len(code_issues_input)}", delta_color="inverse")
    with col2:
        st.metric("Documented Items", documented_count, delta=None if documented_count == 0 else f"+{documented_count}")
    with col3:
        st.metric("Fully Compliant", compliant, delta=None if compliant == 0 else f"+{compliant}", 
                 help="Items with docstrings AND no PEP 257 errors")
    with col4:
        total_issues = len(code_issues_input) + doc_errors
        status = "✅ PASS" if total_issues == 0 else "⚠️ ISSUES FOUND"
        st.metric("Overall Status", status)
    
    st.markdown("---")
    
    # Overall Validation Chart
    st.markdown("### 📊 Validation Summary")
    code_errors = [i for i in code_issues_input if i['code'].startswith('E')]
    code_warnings = [i for i in code_issues_input if i['code'].startswith('W')]
    
    summary_data = pd.DataFrame({
        "Category": ["Code Errors", "Code Warnings", "Documented Items", "Fully Compliant"],
        "Count": [len(code_errors), len(code_warnings), documented_count, compliant]
    })
    
    fig = px.bar(summary_data, x="Category", y="Count", 
                 color="Category",
                 color_discrete_map={
                     "Code Errors": "#ff4444",
                     "Code Warnings": "#ffaa00", 
                     "Documented Items": "#4488ff",
                     "Fully Compliant": "#44ff44"
                 })
    fig.update_layout(
        height=400,
        showlegend=False,
        xaxis_title="",
        yaxis_title="Count",
        dragmode=False
    )
    st.plotly_chart(fig, width='content', config={'staticPlot': True}, key=f"{key_prefix}_validation_bar")
    
    st.markdown("---")
    
    # Code Quality Issues Section
    st.markdown("### 💻 Code Quality Issues")
    if code_issues_input:
        errors = [i for i in code_issues_input if i['code'].startswith('E')]
        warnings = [i for i in code_issues_input if i['code'].startswith('W')]
        
        if errors:
            st.error(f"**{len(errors)} Error(s) Found:**")
            for issue in errors:
                st.markdown(f"- **Line {issue['line']}** - `{issue['code']}`: {issue['message']}")
        
        if warnings:
            st.warning(f"**{len(warnings)} Warning(s) Found:**")
            for issue in warnings:
                st.markdown(f"- **Line {issue['line']}** - `{issue['code']}`: {issue['message']}")
    else:
        st.success("✅ No code quality issues detected!")
    
    st.markdown("---")
    
    # Docstring Compliance Section
    st.markdown("### 📝 Docstring Compliance Details (PEP 257 via pydocstyle)")
    
    if not doc_results:
        st.info("No definitions found in the file.")
    else:
        total_items = len(doc_results)
        existing_items = len([r for r in doc_results if "Existing" in r["status"]])
        generated_items_count = len([r for r in doc_results if "Generated" in r["status"]])
        missing_items_count = len([r for r in doc_results if "Missing" in r["status"]])
        
        if is_after_generation:
            st.info(f"📊 Total: **{total_items}** items | ✅ **{existing_items}** existing | 🆕 **{generated_items_count}** generated")
        else:
            st.info(f"📊 Total: **{total_items}** items | ✅ **{existing_items}** existing | ❌ **{missing_items_count}** missing")
        
        st.dataframe(doc_results, width='stretch', key=f"{key_prefix}_doc_results_df")
    
    st.markdown("---")
    
    # Coverage Report
    report = coverage_report(all_functions, all_classes)
    
    st.markdown("### 📊 Documentation Coverage Report")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📁 Total Definitions", report['total_definitions'])
    with col2:
        st.metric("✅ Documented", report['documented'], delta=f"{report['documented']}")
    with col3:
        st.metric("❌ Missing Docs", report['total_definitions'] - report['documented'], 
                 delta=f"-{report['total_definitions'] - report['documented']}", delta_color="inverse")
    with col4:
        coverage_pct = report['coverage_percent']
        st.metric("📈 Coverage", f"{coverage_pct}%", 
                 delta="Good" if coverage_pct >= 80 else "Needs Work",
                 delta_color="normal" if coverage_pct >= 80 else "inverse")
    
    st.markdown("---")
    
    st.markdown("### Coverage Progress")
    progress_text = f"Documentation Coverage: {coverage_pct}% ({report['documented']}/{report['total_definitions']})"
    st.progress(coverage_pct / 100, text=progress_text)
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = coverage_pct,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Documentation Coverage", 'font': {'size': 24}},
        delta = {'reference': 80, 'increasing': {'color': "green"}},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "darkblue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 50], 'color': '#ffcccc'},
                {'range': [50, 80], 'color': '#ffffcc'},
                {'range': [80, 100], 'color': '#ccffcc'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 80
            }
        }
    ))
    
    fig.update_layout(height=300)
    st.plotly_chart(fig, width='stretch', config={'staticPlot': True}, key=f"{key_prefix}_coverage_gauge")
    
    st.markdown("---")
    
    # Breakdown by type
    st.markdown("### 📋 Breakdown by Definition Type")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Functions/Methods")
        func_documented = sum(1 for f in all_functions if f["has_docstring"])
        func_total = len(all_functions)
        func_pct = (func_documented / func_total * 100) if func_total else 0
        
        st.metric("Total Functions", func_total)
        st.metric("Documented", func_documented)
        st.metric("Coverage", f"{func_pct:.1f}%")
        st.progress(func_pct / 100)
    
    with col2:
        st.markdown("#### Classes")
        class_documented = sum(1 for c in all_classes if c["has_docstring"])
        class_total = len(all_classes)
        class_pct = (class_documented / class_total * 100) if class_total else 0
        
        st.metric("Total Classes", class_total)
        st.metric("Documented", class_documented)
        st.metric("Coverage", f"{class_pct:.1f}%")
        st.progress(class_pct / 100)
    
    st.markdown("---")
    
    # Pie chart
    st.markdown("### 🥧 Documentation Distribution")
    
    pie_data = pd.DataFrame({
        "Status": ["Documented", "Missing Documentation"],
        "Count": [report['documented'], report['total_definitions'] - report['documented']]
    })
    
    fig_pie = px.pie(pie_data, values='Count', names='Status',
                     color='Status',
                     color_discrete_map={'Documented': '#44ff44', 'Missing Documentation': '#ff4444'})
    fig_pie.update_layout(height=300)
    st.plotly_chart(fig_pie, width='stretch', config={'staticPlot': True}, key=f"{key_prefix}_pie_chart")
    
    st.markdown("---")
    
    # Compliance Report
    st.markdown("### 📋 Compliance Report (PEP 257)")
    
    total_items = 1 + len(all_classes) + len(all_functions)
    
    # Compliance means: has docstring AND no PEP 257 errors
    compliant_items = 0
    
    # Check module
    module_docstring = ast.get_docstring(parse_file(source_path))
    module_issues = errors_by_name.get("module", [])
    if module_docstring and not module_issues:
        compliant_items += 1
    
    # Check classes
    for cls in all_classes:
        cls_issues = errors_by_name.get(cls["name"], [])
        if cls["has_docstring"] and not cls_issues:
            compliant_items += 1
    
    # Check functions
    for func in all_functions:
        name = f"{func['class']}.{func['name']}" if func["class"] else func["name"]
        func_issues = errors_by_name.get(name, [])
        if func["has_docstring"] and not func_issues:
            compliant_items += 1
    
    compliance_pct = (compliant_items / total_items * 100) if total_items > 0 else 0
    non_compliant = total_items - compliant_items
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🎯 Total Items", total_items)
    with col2:
        st.metric("✅ Compliant", compliant_items, delta=f"+{compliant_items}")
    with col3:
        st.metric("❌ Non-Compliant", non_compliant, 
                 delta=f"-{non_compliant}" if non_compliant > 0 else None, 
                 delta_color="inverse" if non_compliant > 0 else "off")
    with col4:
        status = "✅ PASS" if compliance_pct >= 80 else "⚠️ NEEDS WORK"
        st.metric("Compliance Rate", f"{compliance_pct:.1f}%", delta=status)
    
    st.markdown("---")
    
    fig_compliance = go.Figure(go.Indicator(
        mode="gauge+number",
        value=compliance_pct,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "PEP 257 Compliance Rate", 'font': {'size': 20}},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "darkblue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 50], 'color': '#ffcccc'},
                {'range': [50, 80], 'color': '#ffffcc'},
                {'range': [80, 100], 'color': '#ccffcc'}
            ],
            'threshold': {
                'line': {'color': "orange", 'width': 4},
                'thickness': 0.75,
                'value': 80
            }
        }
    ))
    
    fig_compliance.update_layout(height=300)
    st.plotly_chart(fig_compliance, width='stretch', config={'staticPlot': True}, key=f"{key_prefix}_compliance_gauge")
    
    st.markdown("---")
    
    st.markdown("### 📊 Compliance Breakdown by Type")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### Module")
        module_compliant = 1 if (module_docstring and not module_issues) else 0
        st.metric("Compliant", module_compliant)
        if not module_docstring:
            st.warning("No module docstring")
        elif module_issues:
            st.warning(f"{len(module_issues)} Issue(s)")
            for issue in module_issues:
                st.caption(f"- {issue['code']}: {issue['message']}")
    
    with col2:
        st.markdown("#### Classes")
        class_compliant = sum(1 for cls in all_classes if cls["has_docstring"] and not errors_by_name.get(cls["name"], []))
        class_total = len(all_classes)
        st.metric("Compliant", class_compliant, delta=f"{class_compliant}/{class_total}")
        
        non_compliant_classes = [cls for cls in all_classes if not (cls["has_docstring"] and not errors_by_name.get(cls["name"], []))]
        if non_compliant_classes:
            st.warning(f"{len(non_compliant_classes)} Non-Compliant")
            for cls in non_compliant_classes:
                if not cls["has_docstring"]:
                    st.caption(f"- {cls['name']}: No docstring")
                else:
                    issues = errors_by_name.get(cls["name"], [])
                    st.caption(f"- {cls['name']}: {', '.join([i['code'] for i in issues])}")
    
    with col3:
        st.markdown("#### Functions/Methods")
        func_compliant = sum(1 for func in all_functions if func["has_docstring"] and not errors_by_name.get(
            f"{func['class']}.{func['name']}" if func["class"] else func["name"], []))
        func_total = len(all_functions)
        st.metric("Compliant", func_compliant, delta=f"{func_compliant}/{func_total}")
        
        non_compliant_funcs = [func for func in all_functions if not (func["has_docstring"] and not errors_by_name.get(
            f"{func['class']}.{func['name']}" if func["class"] else func["name"], []))]
        if non_compliant_funcs:
            st.warning(f"{len(non_compliant_funcs)} Non-Compliant")
            for func in non_compliant_funcs[:5]:
                name = f"{func['class']}.{func['name']}" if func["class"] else func["name"]
                if not func["has_docstring"]:
                    st.caption(f"- {name}: No docstring")
                else:
                    issues = errors_by_name.get(name, [])
                    st.caption(f"- {name}: {', '.join([i['code'] for i in issues])}")
            if len(non_compliant_funcs) > 5:
                st.caption(f"... and {len(non_compliant_funcs) - 5} more")
    
    st.markdown("---")
    
    st.markdown("### 🔍 Detailed Compliance Issues")
    
    if pydocstyle_issues_input:
        compliance_issues = []
        for issue in pydocstyle_issues_input:
            compliance_issues.append({
                "Item": issue.get("name") or "module",
                "Code": issue['code'],
                "Message": issue['message'],
                "Severity": "Error" if issue['code'].startswith('D1') else "Warning"
            })
        
        st.dataframe(compliance_issues, width='stretch', key=f"{key_prefix}_compliance_issues_df")
    else:
        st.success("✅ All items are fully compliant with PEP 257!")


# Pre-generation: Validate the uploaded file (original code)
pydocstyle_issues_before = run_pydocstyle(temp_file_path)
code_issues_before = validate_code_quality(temp_file_path)

# Post-generation: Validate the generated file (merged output)
pydocstyle_issues_after = run_pydocstyle(generated_temp_path)
code_issues_after = validate_code_quality(generated_temp_path)

# Parse generated file for accurate AFTER analytics
all_functions_after = []
all_classes_after = []

tree_after = parse_file(generated_temp_path)
classes_after, functions_after = get_definitions(tree_after)

for cls in classes_after:
    all_classes_after.append(extract_class_data(cls))
    for node in cls.body:
        if node.__class__.__name__ == "FunctionDef":
            
            all_functions_after.append(
                extract_function_data(node, class_name=cls.name)
            )

for func in functions_after:
    if not any(func in cls.body for cls in classes_after):
        all_functions_after.append(extract_function_data(func))

# Calculate coverage AFTER generation
coverage_after = calculate_coverage(all_functions_after, all_classes_after)

# Generate Fix Summary
fix_summary = generate_fix_summary(
    temp_file_path,
    all_classes,
    all_functions,
    code_issues_before,
    coverage_before,
    coverage_after,
    config["normalize_existing_docstrings"],
    config["fix_code_errors"]
)

# ---------------- TABS ----------------
tab1, tab2, tab3 = st.tabs(["Before Generation", "Docstring Generation", "After Generation"])

# ============== BEFORE GENERATION TAB ==============
with tab1:
    st.info("📌 This tab shows analytics **BEFORE** applying generated docstrings. Use this as a baseline to compare improvements.")
    render_analytics(
        all_functions,
        all_classes,
        pydocstyle_issues_before,
        code_issues_before,
        style_key,
        "📊 Before Generation - Analysis",
        key_prefix="before",
        is_after_generation=False,
        source_path=temp_file_path,
    )

# ============== DOCSTRING GENERATION TAB ==============
with tab2:
    st.markdown(f"### 📝 Complete Code with Generated Docstrings")
    st.info(f"📌 View and download your code with AI-generated docstrings inserted. Style: **{style}**")

    if missing_count == 0:
        st.success("✅ All items already have docstrings! No generation needed.")
        st.code(merged_code, language="python", line_numbers=True)
    else:
        # Display statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📄 Total Items", len(all_classes) + len(all_functions))
        with col2:
            st.metric("✅ Already Documented", len(all_classes) + len(all_functions) - missing_count)
        with col3:
            st.metric("🆕 Docstrings Generated", missing_count)
        
        st.markdown("---")
        
        # Display the merged code
        st.markdown("### 📄 Complete Python File with Docstrings")
        st.code(merged_code, language="python", line_numbers=True)
        
        st.markdown("---")
        
        st.success(f"✅ Ready to download! {missing_count} docstring(s) have been generated and merged into your code.")
    
    # Download button (always available)
    base_name = uploaded_file.name
    if base_name.endswith('.py'):
        download_name = base_name[:-3] + '_with_docstrings.py'
    else:
        download_name = base_name + '_with_docstrings.py'
    
    st.download_button(
        label="📥 Download Complete File with Docstrings",
        data=merged_code,
        file_name=download_name,
        mime="text/x-python",
        help="Download the complete Python file with docstrings"
    )


# ============== AFTER GENERATION TAB ==============
with tab3:
    st.info("📌 This tab shows analytics **AFTER** applying all generated docstrings. Compare with 'Before Generation' to see improvements!")
    render_analytics(
        all_functions_after,
        all_classes_after,
        pydocstyle_issues_after,
        code_issues_after,
        style_key,
        "📊 After Generation - Analysis",
        key_prefix="after",
        is_after_generation=True,
        source_path=generated_temp_path,
        generated_class_names=generated_class_names,
        generated_func_names=generated_func_names,
        module_generated=False,
    )
    
    # Display Fix Summary
    st.markdown("---")
    st.markdown("### 🛠 Fix Summary")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Docstrings Generated**")
        st.write(f"New docstrings added: `{fix_summary['docstrings_generated']}`")
        
        st.write("**Docstrings Normalized**")
        st.write(f"Existing docstrings reformatted: `{fix_summary['docstrings_normalized']}`")
        
        st.write("**Code Fixes Applied**")
        st.write(f"Undefined variables (E821): `{fix_summary['code_errors_fixed_e821']}`")
        st.write(f"Typos fixed (W001): `{fix_summary['typos_fixed_w001']}`")
    
    with col2:
        st.write("**Coverage Improvement**")
        coverage_change = fix_summary['coverage_after'] - fix_summary['coverage_before']
        
        st.metric(
            "Docstring Coverage",
            f"{fix_summary['coverage_after']}%",
            delta=f"{coverage_change:+.1f}%" if coverage_change != 0 else "No change"
        )
        
        st.write("")
        st.write(f"**Before:** {fix_summary['coverage_before']}%")
        st.write(f"**After:** {fix_summary['coverage_after']}%")
    
    # Add comparison summary for before/after
    st.markdown("---")
    st.markdown("### 📈 Before & After Comparison")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Before Generation**")
        before_errors = len(pydocstyle_issues_before)
        st.metric("Docstring Issues", before_errors)
    
    with col2:
        st.markdown("**Improvement**")
        after_errors = len(pydocstyle_issues_after)
        improvement = before_errors - after_errors
        improvement_pct = (improvement / before_errors * 100) if before_errors > 0 else 0
        st.metric("Issues Fixed", improvement, delta=f"{improvement_pct:.0f}%" if improvement > 0 else "0%")
    
    with col3:
        st.markdown("**After Generation**")
        st.metric("Docstring Issues", after_errors)

# Clean up temporary files
if os.path.exists(temp_file_path):
    os.remove(temp_file_path)

# Clean up the fixed temp file if it was created
if 'fixed_temp_path' in locals() and fixed_temp_path != temp_file_path and os.path.exists(fixed_temp_path):
    os.remove(fixed_temp_path)

if generated_temp_path and os.path.exists(generated_temp_path):
    os.remove(generated_temp_path)
