# Quick Start Guide

## Installation (1 minute)

```bash
# 1. Navigate to project directory
cd project_infosys

# 2. Install dependencies
pip install -r requirements.txt
```

## Using the CLI (2 minutes)

### Basic Usage

```bash
# Generate docstrings for any Python file
python -m docgen your_file.py
```

### What It Does

1. **Analyzes** your Python file for functions and classes without docstrings
2. **Generates** PEP 257-compliant docstrings
3. **Fixes** common code errors (undefined variables, typos)
4. **Reports** coverage metrics
5. **Saves** the result to `your_file_docgen.py`

### Example Output

```
class MyClass:
    """
    Description of MyClass.
    
    Attributes:
        name (str): Description.
    """
    def __init__(self, name: str):
        """
        Initialize MyClass.
        
        Args:
            name (str): The name value.
        """
        self.name = name

def my_function(data: dict) -> str:
    """
    Process data.
    
    Args:
        data (dict): A dictionary containing data.
    
    Returns:
        str: The processed string.
    """
    return str(data)


Fix Summary
--------------------------------------------------
Docstrings generated: 3
Existing docstrings normalized: 0
Code errors fixed (E821): 0
Typos fixed (W001): 0
Coverage: 0.0% -> 100.0%
```

## Using the Web UI (3 minutes)

### Start the Interface

```bash
streamlit run ui_app.py
```

### Workflow

1. **Upload** a Python file in the "Docstring Generation" tab
2. **View** detected issues in the "Before Generation" tab
3. **Configure** generation options:
   - Docstring style (Google, NumPy, ReStructuredText)
   - Whether to fix code errors
   - Whether to regenerate all docstrings
4. **Review** results in the "After Generation" tab
5. **Copy** or download the generated code

## Configuration (optional)

Create a `pyproject.toml` file in your project root:

```toml
[tool.docgen]
docstring_style = "google"  # google, numpy, or rest
fix_code_errors = true      # Auto-fix undefined variables and typos
normalize_existing_docstrings = true  # Regenerate all docstrings
min_coverage = 80           # Minimum coverage % for success
```

If no configuration file exists, these defaults are used.

## Common Tasks

### Generate docstrings for a single file

```bash
python -m docgen myfile.py
```

### Check exit code

```bash
python -m docgen myfile.py
echo $LASTEXITCODE  # PowerShell: $LASTEXITCODE or $? on Linux
```

Exit 0 = success, Exit 1 = failure or low coverage

### View generated file

```bash
# The output is saved as myfile_docgen.py
cat myfile_docgen.py
```

### Lower coverage threshold

Edit `pyproject.toml`:
```toml
[tool.docgen]
min_coverage = 50  # Changed from 80
```

### Use specific docstring style

CLI: Uses style from `pyproject.toml` (default: google)

Web UI: Select from dropdown in "Docstring Generation" tab

## Troubleshooting

### Q: "No module named 'pydocstyle'"
A: Install dependencies: `pip install -r requirements.txt`

### Q: Coverage is low
A: The tool generates docstrings, but existing code may have fewer coverage-eligible items. Check the "Before Generation" tab to see what needs docs.

### Q: Exit code is 1
A: Check the error message. Likely causes:
- Coverage below minimum threshold
- File not found
- Syntax errors in Python file

### Q: Generated docstrings are too generic
A: Better results with:
- More descriptive variable names
- Type hints on parameters
- Inline comments explaining logic

## Next Steps

1. ✅ Try the CLI on a sample file
2. ✅ Try the web UI for interactive use
3. ✅ Configure `pyproject.toml` for your project
4. ✅ Integrate into your CI/CD pipeline (CLI)
5. ✅ Read [README.md](README.md) for detailed documentation

## Help

For detailed information, see:
- [README.md](README.md) - Complete documentation
- [CLI_VERIFICATION.md](CLI_VERIFICATION.md) - Test results and verification

Questions? Check the troubleshooting section or review the examples above.
