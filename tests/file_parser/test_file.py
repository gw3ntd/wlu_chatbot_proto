from ucr_chatbot.api.file_parsing import parse_file

def test_md():
    test_string = """# My Markdown Example

Welcome to my Markdown file! Here's a simple demo of Markdown syntax.

## Features

- Easy to write
- Plain text format
- Converts to HTML
- Works well for documentation

## Formatting

You can *italicize* text, **bold** it, or even ***do both***.

> Markdown supports blockquotes.
> 
> Like this one!

## Code

Inline code looks like this: `print("Hello, World!")`

Multiline code blocks are easy too:

```python
def greet(name):
    return f"Hello, {name}!"

print(greet("Markdown"))
"""
    #print(parse_file("tests\\file_parser\\test.md"))
    #print(test_string)
    assert parse_file("tests\\file_parser\\test_files\\test.md") == ["".join(test_string.split("#"))]


def test_text_pdf():
    #print(parse_file("tests\\file_parser\\text_test_1.pdf"))
    assert isinstance(parse_file("tests\\file_parser\\test_files\\text_test_2.pdf"), list)
    #print(parse_file("tests\\file_parser\\text_test_2.pdf"))
    assert isinstance(parse_file("tests\\file_parser\\test_files\\text_test_2.pdf"), list)


def test_complex_pdf():
    result = parse_file("tests\\file_parser\\test_files\\test_textbook2.pdf")
    print(result)
    #assert result == ["dog"]
    assert isinstance(result, list)