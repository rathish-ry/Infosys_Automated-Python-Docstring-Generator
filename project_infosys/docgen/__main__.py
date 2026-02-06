"""CLI entry point for docstring generation tool.

Usage:
    python -m docgen <python_file>
"""

import sys
import os
import tempfile
from pathlib import Path

# Force UTF-8 encoding on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def calculate_coverage(all_functions, all_classes):
    """Calculate docstring coverage percentage."""
    if not all_functions and not all_classes:
        return 0.0
    
    classes_with_docs = sum(1 for cls in all_classes if cls.get("has_docstring", False))
    funcs_with_docs = sum(1 for func in all_functions if func.get("has_docstring", False))
    
    total = len(all_classes) + len(all_functions)
    if total == 0:
        return 0.0
    
    coverage = (classes_with_docs + funcs_with_docs) / total * 100
    return round(coverage, 1)


def print_fix_summary(fix_summary):
    """Print the fix summary in CLI-friendly format."""
    print("\nFix Summary")
    print("-" * 50)
    print(f"Docstrings generated: {fix_summary['docstrings_generated']}")
    print(f"Existing docstrings normalized: {fix_summary['docstrings_normalized']}")
    print(f"Code errors fixed (E821): {fix_summary['code_errors_fixed_e821']}")
    print(f"Typos fixed (W001): {fix_summary['typos_fixed_w001']}")
    print(f"Coverage: {fix_summary['coverage_before']}% -> {fix_summary['coverage_after']}%")
    print()


def main():
    """Main CLI entry point."""
    # Check arguments
    if len(sys.argv) < 2:
        print("Error: Please provide a Python file path", file=sys.stderr)
        print("Usage: python -m docgen <python_file>", file=sys.stderr)
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)
    
    # Check if it's a Python file
    if not file_path.endswith('.py'):
        print(f"Error: Not a Python file: {file_path}", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Import required modules
        from core.config_loader import load_project_config, get_config_with_defaults
        from core.parser import parse_file, get_definitions
        from core.extractor import extract_function_data, extract_class_data
        from core.validator import validate_code_quality
        from core.fixer import CodeFixer, remove_existing_docstrings
        from core.inference import infer_function_description, infer_class_description
        from core.generator import (
            generate_function_docstring, 
            generate_class_docstring
        )
        
        # Load configuration
        file_dir = os.path.dirname(os.path.abspath(file_path))
        workspace_root = os.getcwd()
        project_config = load_project_config(workspace_root=workspace_root, file_dir=file_dir)
        config = get_config_with_defaults(project_config)
        
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Parse original file
        tree = parse_file(file_path)
        classes, functions = get_definitions(tree)
        
        all_classes = [extract_class_data(cls) for cls in classes]
        all_functions = []
        for cls in classes:
            for node in cls.body:
                if node.__class__.__name__ == "FunctionDef":
                    all_functions.append(extract_function_data(node, class_name=cls.name))
        
        for func in functions:
            if not any(func in cls.body for cls in classes):
                all_functions.append(extract_function_data(func))
        
        # Calculate coverage BEFORE
        coverage_before = calculate_coverage(all_functions, all_classes)
        
        # Calculate docstring statistics BEFORE processing
        # Count docstrings to be generated (items without docstrings)
        docstrings_generated = sum(1 for func in all_functions if not func.get("has_docstring", False))
        docstrings_generated += sum(1 for cls in all_classes if not cls.get("has_docstring", False))
        
        # Count existing docstrings to be normalized (items with docstrings)
        docstrings_normalized = 0
        if config["normalize_existing_docstrings"]:
            docstrings_normalized = sum(1 for func in all_functions if func.get("has_docstring", False))
            docstrings_normalized += sum(1 for cls in all_classes if cls.get("has_docstring", False))
        
        # Validate and get code issues
        code_issues = validate_code_quality(file_path)
        
        # Apply code fixes if enabled
        processed_content = original_content
        e821_count = 0
        w001_count = 0
        
        if config["fix_code_errors"] and code_issues:
            fixer = CodeFixer(file_path)
            processed_content = fixer.fix_issues(code_issues)
            
            # Count fixed issues
            for issue in code_issues:
                if issue.get("code") == "E821":
                    e821_count += 1
                elif issue.get("code") == "W001":
                    w001_count += 1
        
        # Generate docstrings if enabled
        
        if config["normalize_existing_docstrings"]:
            # Remove existing docstrings
            processed_content = remove_existing_docstrings(processed_content)
            
            # Re-parse to get correct line numbers from processed content
            lines = processed_content.splitlines(keepends=True)
            
            # Write processed content to temp file for parsing
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp:
                tmp.write(processed_content)
                tmp_path = tmp.name
            
            tree = parse_file(tmp_path)
            os.unlink(tmp_path)
            
            # Helper function for rendering docstrings
            def render_docstring_block(docstring, indent=""):
                if docstring is None:
                    return []
                text = docstring or ""
                if text.strip().startswith('"""'):
                    block_lines = text.splitlines()
                else:
                    block_lines = ['"""'] + text.splitlines() + ['"""']
                return [f"{indent}{line}" for line in block_lines]
            
            # Extract definitions from the parsed tree (after docstring removal)
            classes_parsed, functions_parsed = get_definitions(tree)
            
            class_map = {cls.name: cls for cls in classes_parsed}
            func_map = {func.name: func for func in functions_parsed}
            
            insertions = []
            
            # Generate function docstrings
            for func_data in all_functions:
                func_name = func_data.get("name")
                class_name = func_data.get("class")
                
                func_node = None
                if class_name:
                    cls_node = class_map.get(class_name)
                    if cls_node:
                        for node in cls_node.body:
                            if hasattr(node, 'name') and node.name == func_name:
                                func_node = node
                                break
                else:
                    func_node = func_map.get(func_name)
                
                if func_node:
                    docstring = generate_function_docstring(
                        func_data,
                        infer_function_description(func_data),
                        style=config["docstring_style"]
                    )
                    
                    line_num = func_node.lineno
                    if line_num > 0 and line_num <= len(lines):
                        def_line = lines[line_num - 1]
                        base_indent = len(def_line) - len(def_line.lstrip())
                        docstring_indent = ' ' * (base_indent + 4)
                        
                        # Check for one-liner
                        docstring_lines = docstring.splitlines()
                        if len(docstring_lines) == 3 and docstring_lines[0] == '"""' and docstring_lines[2] == '"""':
                            summary = docstring_lines[1]
                            if len(docstring_indent + '"""' + summary + '"""') <= 88:
                                docstring = f'"""{summary}"""'
                                doc_lines = [f"{docstring_indent}{docstring}"]
                            else:
                                doc_lines = render_docstring_block(docstring, docstring_indent)
                        else:
                            doc_lines = render_docstring_block(docstring, docstring_indent)
                        
                        insertions.append((line_num, '\n'.join(doc_lines) + '\n'))
            
            # Generate class docstrings
            for cls_data in all_classes:
                cls_name = cls_data.get("name")
                cls_node = class_map.get(cls_name)
                
                if cls_node:
                    docstring = generate_class_docstring(
                        infer_class_description(cls_name),
                        attributes=cls_data.get("attributes", []),
                        style=config["docstring_style"]
                    )
                    
                    line_num = cls_node.lineno
                    if line_num > 0 and line_num <= len(lines):
                        def_line = lines[line_num - 1]
                        base_indent = len(def_line) - len(def_line.lstrip())
                        docstring_indent = ' ' * (base_indent + 4)
                        
                        # Check for one-liner
                        docstring_lines = docstring.splitlines()
                        if len(docstring_lines) == 3 and docstring_lines[0] == '"""' and docstring_lines[2] == '"""':
                            summary = docstring_lines[1]
                            if len(docstring_indent + '"""' + summary + '"""') <= 88:
                                docstring = f'"""{summary}"""'
                                doc_lines = [f"{docstring_indent}{docstring}"]
                            else:
                                doc_lines = render_docstring_block(docstring, docstring_indent)
                        else:
                            doc_lines = render_docstring_block(docstring, docstring_indent)
                        
                        insertions.append((line_num, '\n'.join(doc_lines) + '\n'))
            
            # Insert docstrings in reverse order
            insertions.sort(key=lambda x: x[0], reverse=True)
            modified_lines = lines[:]
            for line_num, docstring_text in insertions:
                if line_num <= len(modified_lines):
                    # Check if the def line has inline content (e.g., "def func(): pass")
                    def_line = modified_lines[line_num - 1]
                    stripped = def_line.rstrip()
                    
                    # If line ends with pass or ellipsis, remove it and preserve newline
                    if stripped.endswith(": pass"):
                        # Remove the " pass" part (keep the colon)
                        modified_lines[line_num - 1] = stripped[:-5] + "\n"
                    elif stripped.endswith(": ..."):
                        # Remove the " ..." part (keep the colon)
                        modified_lines[line_num - 1] = stripped[:-4] + "\n"
                    
                    modified_lines.insert(line_num, docstring_text)
            
            processed_content = ''.join(modified_lines)
        
        # Parse the final output to calculate coverage
        try:
            # Write processed content to a temp file for parsing
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp:
                tmp.write(processed_content)
                tmp_path = tmp.name
            
            tree_final = parse_file(tmp_path)
            classes_final, functions_final = get_definitions(tree_final)
            
            # Clean up temp file
            os.unlink(tmp_path)
            
            all_classes_final = [extract_class_data(cls) for cls in classes_final]
            all_functions_final = []
            for cls in classes_final:
                for node in cls.body:
                    if node.__class__.__name__ == "FunctionDef":
                        all_functions_final.append(extract_function_data(node, class_name=cls.name))
            
            for func in functions_final:
                if not any(func in cls.body for cls in classes_final):
                    all_functions_final.append(extract_function_data(func))
            
            coverage_after = calculate_coverage(all_functions_final, all_classes_final)
        except:
            coverage_after = coverage_before
        
        # Print generated code to stdout
        print(processed_content)
        
        # Save to output file
        output_file = file_path.replace('.py', '_docgen.py')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(processed_content)
        
        # Build and print fix summary
        fix_summary = {
            "docstrings_generated": docstrings_generated,
            "docstrings_normalized": docstrings_normalized,
            "code_errors_fixed_e821": e821_count,
            "typos_fixed_w001": w001_count,
            "coverage_before": coverage_before,
            "coverage_after": coverage_after,
        }
        
        print_fix_summary(fix_summary)
        
        # Check coverage against minimum
        if coverage_after < config["min_coverage"]:
            print(f"Error: Coverage {coverage_after}% is below minimum {config['min_coverage']}%", file=sys.stderr)
            sys.exit(1)
        
        # Success
        sys.exit(0)
    
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
