# PowerShell pre-commit hook template for Windows
# Place this file at .git\hooks\pre-commit (executable via PowerShell) to enable.
$python = $env:PYTHON -or 'python'
$root = git rev-parse --show-toplevel
& $python "$root\scripts\check_doc_coverage.py" --threshold 80
if ($LASTEXITCODE -ne 0) { Write-Host 'Pre-commit: docstring coverage check failed (see output above).' ; exit $LASTEXITCODE }
exit 0
