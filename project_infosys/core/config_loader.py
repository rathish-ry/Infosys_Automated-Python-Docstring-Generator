"""Configuration loader for docstring generator from pyproject.toml."""

import os
from pathlib import Path


def load_project_config(workspace_root=None, file_dir=None):
    """
    Load project configuration from pyproject.toml.
    
    Searches for pyproject.toml in this order:
    1. Workspace root directory
    2. Uploaded file directory
    
    Args:
        workspace_root (str, optional): Workspace root directory path.
        file_dir (str, optional): Uploaded file directory path.
    
    Returns:
        dict: Configuration from [tool.docgen] section, or empty dict if not found.
    """
    try:
        import tomllib
    except ImportError:
        # Python < 3.11 fallback
        try:
            import tomli as tomllib
        except ImportError:
            # tomli not available, return empty config
            return {}
    
    search_dirs = []
    
    # Add workspace root if provided
    if workspace_root:
        search_dirs.append(Path(workspace_root))
    
    # Add file directory if provided
    if file_dir:
        search_dirs.append(Path(file_dir))
    
    # Add current working directory as fallback
    search_dirs.append(Path.cwd())
    
    # Search for pyproject.toml
    for directory in search_dirs:
        config_file = directory / "pyproject.toml"
        if config_file.exists():
            try:
                with open(config_file, "rb") as f:
                    pyproject = tomllib.load(f)
                
                # Extract [tool.docgen] section
                config = pyproject.get("tool", {}).get("docgen", {})
                return config
            except Exception as e:
                # Continue searching if there's an error reading the file
                continue
    
    # No pyproject.toml found or no [tool.docgen] section
    return {}


def get_config_with_defaults(project_config=None):
    """
    Merge project configuration with default values.
    
    Args:
        project_config (dict, optional): Configuration loaded from pyproject.toml.
    
    Returns:
        dict: Configuration with defaults applied.
    """
    if project_config is None:
        project_config = {}
    
    defaults = {
        "docstring_style": "google",
        "fix_code_errors": True,
        "normalize_existing_docstrings": True,
        "min_coverage": 80,
    }
    
    # Merge: project config overrides defaults
    config = {**defaults, **project_config}
    
    return config
