"""
This script provides a cross-platform way to run a series of development checks
and tests for this Python project using 'uv'. It performs type checking,
code style checks, formatting checks, package installation, and runs tests
with coverage reporting.

It returns a truthy value if all tests pass and returns a falsey value otherwise.
"""

import subprocess
import sys

def run_command(command: list[str]):
    """
    Runs a shell command and prints its output.
    Exits if the command fails.
    """
    print(f"Running command: {' '.join(command)}")
    try:
        subprocess.run(command, check=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: Check '{' '.join(command)}' failed. Refer to the output above.")
        sys.exit(e.returncode)
    except FileNotFoundError:
        print(f"Error: Command '{command[0]}' not found. Make sure '{command[0]}' is installed and in your PATH.")
        sys.exit(1)

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

    for cmd in commands:
        run_command(cmd)

    print("\nAll checks and tests passed successfully!")

if __name__ == "__main__":
    main()