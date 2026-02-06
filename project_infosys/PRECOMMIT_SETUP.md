# Pre-commit Hook Setup Guide

## ⚠️ IMPORTANT: Activate Virtual Environment First

**You MUST activate the virtual environment before running git commands.**

### PowerShell
```powershell
. ../venv/Scripts/Activate.ps1
```

### Command Prompt
```cmd
..\venv\Scripts\activate.bat
```

### Bash/Git Bash
```bash
source ../venv/Scripts/activate
```

## Installation

### Step 1: Activate the virtual environment
```powershell
. ../venv/Scripts/Activate.ps1
```

### Step 2: Install pre-commit
```bash
pip install pre-commit
```

### Step 3: Install the git hooks
```bash
pre-commit install
```

## Usage

### Automatic (on every commit)
```bash
git add your_file.py
git commit -m "Your message"
# Hook runs automatically and checks docstring coverage
```

### Manual testing
```bash
# Test on all files
pre-commit run --all-files

# Test on specific files
pre-commit run --files sample.py test_errors.py

# Test only modified/staged files
pre-commit run
```

### Bypass hook (when needed)
```bash
git commit --no-verify -m "Skip pre-commit hooks"
```

## How It Works

1. **On commit**, pre-commit runs `python -m docgen` on all staged Python files
2. **The CLI**:
   - Generates missing docstrings
   - Fixes code errors (E821, W001)
   - Calculates coverage percentage
   - Compares against min_coverage from pyproject.toml (default: 80%)
3. **Exit code determines commit status**:
   - **Exit 0** (coverage ≥ 80%) → ✅ Commit proceeds
   - **Exit 1** (coverage < 80%) → ❌ Commit blocked with error message

## Example Output

### ✅ Success (commit allowed)
```
Check Docstring Coverage.....................................Passed
[main abc1234] Added new features
 1 file changed, 10 insertions(+)
```

### ❌ Failure (commit blocked)
```
Check Docstring Coverage.....................................Failed
- hook id: docstring-coverage
- exit code: 1

Fix Summary
--------------------------------------------------
Docstrings generated: 5
Existing docstrings normalized: 0
Code errors fixed (E821): 0
Typos fixed (W001): 0
Coverage: 0.0% -> 60.0%

Error: Coverage 60.0% is below minimum 80%
```

## Configuration

Modify `pyproject.toml` to adjust the coverage threshold:

```toml
[tool.docgen]
min_coverage = 80  # Change to your desired percentage
```

## Troubleshooting

### Hook not running
```bash
# Reinstall hooks
pre-commit uninstall
pre-commit install
```

### Want to update generated files
The hook only validates - it doesn't modify your source files. To apply changes:
```bash
python -m docgen your_file.py
# Review the generated your_file_docgen.py
# Manually copy changes if desired
```

### Disable hook temporarily
```bash
# For one commit
git commit --no-verify

# Disable permanently (not recommended)
pre-commit uninstall
```

## Best Practices

1. **Run manually before committing** to catch issues early:
   ```bash
   pre-commit run --files your_file.py
   ```

2. **Fix issues incrementally** rather than committing large changes

3. **Review generated docstrings** - they may need manual refinement

4. **Adjust min_coverage** in pyproject.toml to match your project standards

5. **Keep pyproject.toml in version control** so the team uses consistent settings
