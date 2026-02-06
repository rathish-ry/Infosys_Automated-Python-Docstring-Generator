"""Code fixer module to automatically correct common code issues."""

import re
from typing import List, Dict


class CodeFixer:
    """Fix common code quality issues like undefined variables, typos, etc."""

    def __init__(self, file_path: str):
        """Initialize fixer with file path."""
        with open(file_path, 'r', encoding='utf-8') as f:
            self.content = f.read()
        self.lines = self.content.splitlines(keepends=True)
        
        # Known method mappings for typo corrections
        self.method_corrections = {
            'uper': 'upper',
            'lwoer': 'lower',
            'kyes': 'keys',
            'vales': 'values',
            'itmes': 'items',
            'apennd': 'append',
            'extand': 'extend',
            'remve': 'remove',
            'cler': 'clear',
            'indx': 'index',
            'splt': 'split',
            'jion': 'join',
            'replce': 'replace',
            'fnd': 'find',
            'strtswith': 'startswith',
            'endwith': 'endswith',
            'capitlize': 'capitalize',
            'formatt': 'format',
            'encde': 'encode',
            'decde': 'decode',
            'lstrp': 'lstrip',
            'rstrp': 'rstrip',
            'cnt': 'count',
            'lowr': 'lower',
        }
        
        # Common undefined variable fixes
        self.common_fixes = {
            'confi': 'config',
            'item': 'items',
            'decimals': 'decimal_places',
            'lenght': 'length',
            'valu': 'value',
            'lst': 'list',
            'dct': 'dict',
            'nam': 'name',
            'user': 'users',
        }

    def fix_issues(self, issues: List[Dict]) -> str:
        """Fix identified code issues and return corrected content."""
        if not issues:
            return self.content

        # Sort issues by line number in reverse to maintain line integrity
        sorted_issues = sorted(issues, key=lambda x: x['line'], reverse=True)

        for issue in sorted_issues:
            line_num = issue['line'] - 1  # Convert to 0-indexed
            code = issue.get('code', '')
            message = issue.get('message', '')

            if line_num < 0 or line_num >= len(self.lines):
                continue

            # Fix undefined variable issues (E821)
            if code == 'E821':
                self._fix_undefined_variable(line_num, message)
            # Fix potential typos (W001)
            elif code == 'W001':
                self._fix_method_typo(line_num, message)

        return ''.join(self.lines)

    def _fix_undefined_variable(self, line_num: int, message: str):
        """Fix undefined variable references."""
        line = self.lines[line_num]

        # Extract variable name from message
        match = re.search(r"Undefined name '([^']+)'", message)
        if not match:
            return

        undefined_var = match.group(1)

        # Try to find suggestion in message
        suggestion_match = re.search(r"did you mean '([^']+)'", message)
        if suggestion_match:
            suggestion = suggestion_match.group(1)
            # Replace the undefined variable with suggestion
            new_line = re.sub(
                r'\b' + re.escape(undefined_var) + r'\b',
                suggestion,
                line
            )
            self.lines[line_num] = new_line
            return

        # Use common fixes mapping
        if undefined_var in self.common_fixes:
            correction = self.common_fixes[undefined_var]
            new_line = re.sub(
                r'\b' + re.escape(undefined_var) + r'\b',
                correction,
                line
            )
            self.lines[line_num] = new_line

    def _fix_method_typo(self, line_num: int, message: str):
        """Fix method name typos."""
        line = self.lines[line_num]

        # Extract typo from message: "did you mean 'correct_method'?"
        match = re.search(r"did you mean '([^']+)\(\)'", message)
        if match:
            correct_method = match.group(1)
            # Find and replace the typo with correct method
            for typo, correct in self.method_corrections.items():
                if correct == correct_method:
                    # Match both .typo() and typo() patterns
                    pattern = r'\.' + re.escape(typo) + r'\(\)'
                    replacement = '.' + correct + '()'
                    new_line = re.sub(pattern, replacement, line)
                    if new_line != line:
                        self.lines[line_num] = new_line
                        return

        # Direct replacement from known mappings
        for typo, correct in self.method_corrections.items():
            if f".{typo}()" in line:
                new_line = line.replace(f".{typo}()", f".{correct}()")
                self.lines[line_num] = new_line
                return


def remove_existing_docstrings(content: str) -> str:
    """Remove existing docstrings from Python code while preserving structure.
    
    This function removes docstring statements while keeping the rest of the code intact.
    It handles multi-line docstrings properly.
    """
    import ast
    import re
    
    try:
        tree = ast.parse(content)
    except:
        return content
    
    lines = content.splitlines(keepends=True)
    
    # Collect docstring ranges (start_line, end_line) as 0-indexed
    docstring_ranges = []
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if hasattr(node, 'body') and len(node.body) > 0:
                first_stmt = node.body[0]
                if isinstance(first_stmt, ast.Expr):
                    if isinstance(first_stmt.value, ast.Constant):
                        if isinstance(first_stmt.value.value, str):
                            # Found docstring - record range
                            start_line = first_stmt.lineno - 1
                            end_line = first_stmt.end_lineno - 1 if first_stmt.end_lineno else start_line
                            docstring_ranges.append((start_line, end_line))
    
    if not docstring_ranges:
        return content
    
    # Sort ranges by start line (reverse order for deletion)
    docstring_ranges.sort(reverse=True)
    
    # Build output by removing docstring lines
    for start_line, end_line in docstring_ranges:
        # Delete lines from end_line down to start_line to preserve indices
        for i in range(end_line, start_line - 1, -1):
            if i < len(lines):
                del lines[i]
    
    return ''.join(lines)


def fix_code_issues(file_path: str, issues: List[Dict]) -> str:
    """Convenience function to fix code issues in a file."""
    fixer = CodeFixer(file_path)
    return fixer.fix_issues(issues)
