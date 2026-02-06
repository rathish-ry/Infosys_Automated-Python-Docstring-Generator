# Docstring Generation Tool

A comprehensive Python tool for automatically generating and validating PEP 257-compliant docstrings with integrated code error fixing and configuration management.

## Features

- **Automatic Docstring Generation**: Generate docstrings for functions and classes using AI inference
- **Code Error Fixing**: Auto-fix common code issues:
  - E821: Undefined variables
  - W001: Method name typos
- **PEP 257 Compliance**: Ensure docstrings follow PEP 257 standards:
  - D400: First line ends with period
  - D403: First word capitalized
  - D204: Blank line after class docstring
  - D205: Blank line before parameters
- **Docstring Normalization**: Remove and regenerate all docstrings consistently
- **Coverage Tracking**: Monitor docstring coverage percentage
- **Configuration Management**: Load settings from `pyproject.toml`
- **Dual Interface**: Both Streamlit UI and CLI support

## Installation

### Requirements
- Python 3.8+

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Or individually
pip install streamlit pandas plotly pydocstyle
```

## Usage

### Command Line Interface (CLI)

Generate docstrings for a Python file:

```bash
python -m docgen <python_file>
```

**Example:**
```bash
python -m docgen sample.py
```

**Output:**
- Generated code printed to stdout
- Output saved to `<filename>_docgen.py`
- Fix Summary displayed showing:
  - Number of docstrings generated
  - Number of existing docstrings normalized
  - Code errors fixed (E821)
  - Typos fixed (W001)
  - Coverage percentage (before → after)

**Exit Codes:**
- `0`: Success (coverage >= minimum threshold)
- `1`: Failure (coverage < minimum threshold, file not found, syntax errors)

### Streamlit Web UI

Start the interactive web interface:

```bash
streamlit run ui_app.py
```

The interface provides three tabs:
1. **Before Generation**: View original code with detected issues
2. **Docstring Generation**: Configure generation options
3. **After Generation**: Review generated docstrings and fix summary

## Configuration

Configuration is loaded from `pyproject.toml` in the project root directory.

### pyproject.toml

```toml
[tool.docgen]
docstring_style = "google"  # Options: "google", "numpy", "rest"
fix_code_errors = true      # Auto-fix E821 and W001 errors
normalize_existing_docstrings = true  # Regenerate all docstrings
min_coverage = 80           # Minimum docstring coverage percentage
```

### Default Configuration (if no pyproject.toml)

```python
{
    "docstring_style": "google",
    "fix_code_errors": True,
    "normalize_existing_docstrings": True,
    "min_coverage": 80
}
```

## Project Structure

```
project_infosys/
├── core/
│   ├── parser.py           # AST parsing and code structure analysis
│   ├── extractor.py        # Extract function/class metadata
│   ├── inference.py        # AI-based description inference
│   ├── generator.py        # Docstring generation
│   ├── validator.py        # PEP 257 compliance validation
│   ├── fixer.py            # Auto-fix code errors
│   ├── coverage.py         # Coverage calculation
│   └── config_loader.py    # Configuration management
├── docgen/
│   ├── __init__.py         # Package initialization
│   └── __main__.py         # CLI entry point
├── ui_app.py               # Streamlit web interface
├── requirements.txt        # Python dependencies
├── pyproject.toml          # Project configuration
└── README.md               # This file
```

## Module Reference

### core/config_loader.py
- `load_project_config()`: Load configuration from pyproject.toml
- `get_config_with_defaults()`: Merge project config with defaults

### core/parser.py
- `parse_file()`: Parse Python file into AST
- `get_definitions()`: Extract classes and functions

### core/extractor.py
- `extract_function_data()`: Extract function metadata
- `extract_class_data()`: Extract class metadata

### core/inference.py
- `infer_function_description()`: Generate description for functions
- `infer_class_description()`: Generate description for classes

### core/generator.py
- `generate_function_docstring()`: Create function docstring
- `generate_class_docstring()`: Create class docstring

### core/validator.py
- `validate_code_quality()`: Find code issues (E821, W001)
- `validate_docstrings()`: Check PEP 257 compliance

### core/fixer.py
- `CodeFixer.fix_issues()`: Fix detected code errors
- `remove_existing_docstrings()`: Remove all docstrings from code

## Examples

### Example 1: Fix a file with errors

File: `test_errors.py`
```python
class DataValidator:
    def __init__(self, config: dict):
        # ERROR: undefined variable
        self.config = confg

    def validate_data(self, items: list) -> bool:
        # ERROR: undefined variable
        return len(item) > 0
```

Run CLI:
```bash
python -m docgen test_errors.py
```

Output:
- Generates docstrings for `DataValidator`, `__init__`, and `validate_data`
- Fixes E821 undefined variables (confg → config, item → items)
- Creates `test_errors_docgen.py` with corrected code and docstrings

### Example 2: Generate docstrings with web UI

```bash
streamlit run ui_app.py
```

1. Upload Python file in "Docstring Generation" tab
2. Select docstring style (Google, NumPy, or ReStructuredText)
3. View "Before Generation" tab for detected issues
4. Review "After Generation" tab for fixes applied
5. Export or copy generated code

## Error Handling

The CLI provides clean error messages:

```bash
$ python -m docgen nonexistent.py
Error: File not found: nonexistent.py

$ python -m docgen
Error: Please provide a Python file path
Usage: python -m docgen <python_file>
```

## Performance

- Typical processing time: < 1 second per file
- Handles files up to 10,000 lines efficiently
- Configuration is cached in Streamlit session state

## Troubleshooting

### Issue: "No module named 'pydocstyle'"
**Solution:** Install pydocstyle
```bash
pip install pydocstyle
```

### Issue: Low coverage percentage
**Solution:** Check if all functions/classes have docstrings
- Run CLI with verbose output
- Use the Streamlit UI to see which items need docstrings
- Adjust `min_coverage` in pyproject.toml if desired

### Issue: Generated docstrings are incomplete
**Solution:** Check if the inference model has enough context
- Provide more descriptive variable/parameter names
- Add inline comments for complex logic
- Use type hints (they improve inference)

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Code Style

- Python 3.8+ syntax
- Follow PEP 257 for docstrings
- Use type hints where possible

## License

MIT License - See LICENSE file for details

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Ensure tests pass
5. Submit a pull request

## Support

For issues, questions, or suggestions, please open an issue on GitHub.
