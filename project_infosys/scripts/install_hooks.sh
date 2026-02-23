#!/bin/sh
# Install git hook templates into the repository's .git/hooks directory
ROOT=$(git rev-parse --show-toplevel)
HOOK_SRC="$ROOT/hooks/pre-commit"
HOOK_DST="$ROOT/.git/hooks/pre-commit"

if [ -f "$HOOK_SRC" ]; then
    cp "$HOOK_SRC" "$HOOK_DST"
    chmod +x "$HOOK_DST"
    echo "Installed pre-commit hook to $HOOK_DST"
else
    echo "Shell hook not found at $HOOK_SRC"
fi

# Also install PowerShell hook if present
HOOK_PWSRC="$ROOT/hooks/pre-commit.ps1"
if [ -f "$HOOK_PWSRC" ]; then
    cp "$HOOK_PWSRC" "$ROOT/.git/hooks/pre-commit.ps1"
    echo "Installed PowerShell hook to $ROOT/.git/hooks/pre-commit.ps1"
fi
