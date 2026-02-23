# Install git hook templates into the repository's .git/hooks directory
$root = git rev-parse --show-toplevel
$hookSrc = Join-Path $root 'hooks' 'pre-commit.ps1'
$hookDst = Join-Path $root '.git' 'hooks' 'pre-commit'

Copy-Item -Path $hookSrc -Destination $hookDst -Force
Write-Host "Installed PowerShell pre-commit hook to $hookDst"

# Also copy unix shell hook if present
$unixHook = Join-Path $root 'hooks' 'pre-commit'
if (Test-Path $unixHook) {
    $unixDst = Join-Path $root '.git' 'hooks' 'pre-commit'
    Copy-Item -Path $unixHook -Destination $unixDst -Force
    Write-Host "Installed shell pre-commit hook to $unixDst"
}
