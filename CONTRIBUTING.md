# Contributing

I highly recommend that you download and install [uv](https://docs.astral.sh/uv/) for managing the Python dependencies.
Managing them yourself can become challenging the second things start going awry.

## Checking Tools

We are using the following tools for checking our code:
- All code must pass [pyright](https://github.com/microsoft/pyright) on strict mode, which checks for correct type hints;
- The configured [Ruff](https://docs.astral.sh/ruff/) checks must pass, which checks for some common errors and verifies the existence of docstring comments;
- All unit tests, written in [pytest](https://docs.pytest.org/en/stable/), must pass;
- We strive to have 100% test coverage as measured by [coverage](https://coverage.readthedocs.io/en/7.9.1/).

To run these checks with `uv`, navigate to the root directory of this project and run

```bash
uv run pyright # Check types
uv run ruff check # Check common errors and docstrings
uv run ruff format --check # Check formatting
uv pip install -e . # Install package for testing
uv run coverage run -m pytest # Run tests while tracking coverage
uv run coverage report # Get coverage statistics
```

or, in the root directory, you can use code review script that runs all of the tests and checks:

```bash
uv run review_code.py
```

Run these before submitting a pull request.
Everything should pass and the coverage should be good, definitely above 80%, with higher being better.

The summary of these checks is given in the next two sections to help you abide thereby.

## Type Hints
All functions and methods must have their parameters' types stated explicitely via type hints.
Also, the return values must be explicitely typed or inferable by [pyright](https://github.com/microsoft/pyright).
For example,

```python
def add(a, b):
    return a + b
```

is not okay but

```python
def add(a: int, b: int):
    return a + b
```

or

```python
def add(a: int, b: int) -> int:
    return a + b
```

is okay. Explicitely stating the output type when convenient is prefered.


## Docstrings
Every class, method, and function must have docstring attached to it.

We are using [Sphinx-style](https://sphinx-rtd-tutorial.readthedocs.io/en/latest/docstrings.html) comments.
For obvious functions/methods, you do not need to explicitely document parameters or return values.
For example, there is no need to comment this `__init__` with `:param ...:` and `:return: ...`:

```python
class Document:
    ...
    def __init__(self, name: str, document_id: int):
        """Initializes a Document with a name and document_id."""
        self._name = name
        self._document_id = document_id
```

## Formatting

To format your code, simply run

```bash
uv run ruff format
```

from the root directory. This will fix the spacing, quote usage, and other aestetic features of your code.

## Tests

We are using [pytest](https://docs.pytest.org/en/stable/) to create unit tests for our code.
Additionally, we are using [coverage](https://coverage.readthedocs.io/en/7.9.1/) to track how much of our code is being tested.

Refer to the pytest documentation to learn how to write tests. It is not hard.

Our tests are all stored in the `tests/` directory. The folder structure should mirror that of ucr_chatbot,
with corresponding names for each file where applicable.

Note that 100% coverage does not mean that the code is without error, only that every line of code is run during testing.