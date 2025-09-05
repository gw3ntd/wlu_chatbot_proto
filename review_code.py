"""
This script provides a cross-platform way to run a series of development checks
and tests for this Python project using 'uv'. It performs type checking,
code style checks, formatting checks, package installation, and runs tests
with coverage reporting.

It returns a truthy value if all tests pass and returns a falsey value otherwise.
"""

import subprocess
import sys

def run_command(command: list[str]) -> bool:
    """
    Runs a shell command and prints its output.
    Returns False if the command fails.
    """
    print(f"Running command: {' '.join(command)}")
    try:
        subprocess.run(command, check=True, text=True)
    except subprocess.CalledProcessError:
        print(f"Error: Check '{' '.join(command)}' failed. Refer to the output above.")
        return False
    except FileNotFoundError:
        print(f"Error: Command '{command[0]}' not found. Make sure '{command[0]}' is installed and in your PATH.")
        return False
    
    return True

def main():
    """
    Run all the checks and tests.
    """
    commands = [
        ["uv", "run", "pyright"],          # Check types
        ["uv", "run", "ruff", "check"],    # Check common errors and docstrings
        ["uv", "run", "ruff", "format", "--check"], # Check formatting
        ["uv", "pip", "install", "-e", "."], # Install package for testing
        ["uv", "run", "coverage", "run", "-m", "pytest"], # Run tests while tracking coverage
        ["uv", "run", "coverage", "report"], # Get coverage statistics
    ]

    no_falures = True
    for cmd in commands:
        no_falures &= run_command(cmd)

    if no_falures:
        print("\nAll checks and tests passed successfully!")
        sys.exit(0)
    print("\nAt least one test failed.")
    sys.exit(1)


if __name__ == "__main__":
    main()