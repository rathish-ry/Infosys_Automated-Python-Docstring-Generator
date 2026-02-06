#!/usr/bin/env python
import sys
import os
import subprocess

def main():
    """Execute the operation."""
    if len(sys.argv) < 2:
        print("Error: No files provided", file=sys.stderr)
        return 1
    
    # Get all files from command line arguments
    files = sys.argv[1:]
    
    # Get the project directory (where this script is located)
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Set PYTHONPATH to include the project directory
    env = os.environ.copy()
    pythonpath = env.get('PYTHONPATH', '')
    if pythonpath:
        env['PYTHONPATH'] = f"{project_dir}{os.pathsep}{pythonpath}"
    else:
        env['PYTHONPATH'] = project_dir
    
    # Track if any file fails
    failed = False
    
    # Process each file
    for file_path in files:
        # Run the CLI with modified PYTHONPATH
        result = subprocess.run(
            [sys.executable, "-m", "docgen", file_path],
            env=env,
            capture_output=False,
        )
        
        # Check exit code
        if result.returncode != 0:
            failed = True
    
    # Return failure if any file failed
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(min())

