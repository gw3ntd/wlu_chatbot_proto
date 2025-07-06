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
    assert parse_file("tests\\file_parser\\test_files\\test.md") == test_string


def test_text_pdf():
    test_string = """I am graduating senior here at UCR with a B.S. degree in Computer Engineering and I 
plan to continue my education at UCR through the B.S.+M.S. program. My time at UCR under 
BCOE has been phenomenal as I have not only gained knowledge in an area of study that greatly 
interests me, but it has also helped me grow as a person, meeting so many new people who also 
aspire to do unbelievable things in their lives. Currently, I want to branch out into more practical 
areas with developing projects and I believe this summer opportunity with the data science 
fellowship will be an amazing experience where I plan to give my all to help this project 
succeed, and help UCR. Coming into university as a computer engineering major, I was going into an unfamiliar 
field, as I come from a family of teachers, so my background knowledge in this career was 
lacking. However, through my years here at BCOE, I feel as though I have learned a great deal, 
not only about the content within my major, but of engineering as a whole and the community 
around it. Especially in the last few years as I began to look beyond classes for other 
opportunities with my peers in engineering related opportunities, I began tutoring for computer 
science classes as it not only helped me reinforce my own course knowledge, but introduced me 
to a much wider range of peers in BCOE that I wouldn’t have otherwise. I want to continue this 
into my graduate year and I feel like this summer opportunity would be another great chance to 
not only grow my skillset, but my sense of community within engineering. My coursework relevant to machine learning and AI involves CS170, Introduction to AI, 
and CS171, Introduction to Machine Learning and Data Mining. CS170 sparked my interest in 
how I can apply the different efficient algorithms I have learned in previous classes to practical 
applications and models to solve problems in ways I haven’t seen before. Through this class, I 
produced a couple projects implementing AI techniques such as Minimax solving basic games 
such as Tic-Tac-Toe. At the beginning of my senior year, I took CS171, where I learned the 
structures and mathematics of several different machine learning models. This class was of great 
interest to me as the continuous assignments helped build the foundation of my understanding of 
probabilistic models, linear and nonlinear regression models, and neural networks. This interest 
accumulated towards my senior design project. Even though it was an embedded systems based 
project, my team and I wanted to integrate machine learning to take the capabilities of our 
project further. Our project was a pair of smart glasses that could take in audio input and live 
generate captions that the user would be able to read on a transparent screen in front of the lens 
using speech recognition. In addition to this feature, the glasses also had a small camera that 
could take pictures and detect letters in American Sign Language. With our limited time, we 
were able to develop a neural network model that integrated with the system to take a picture, 
detect which singular letter was shown, and output that letter to the screen. These various 
projects helped me develop a foundation within AI and machine learning in particular and I am 
excited to see what new projects I can help create with these past experiences as I develop my 
skills."""
    #print(parse_file("tests\\file_parser\\text_test_1.pdf"))
    assert parse_file("tests\\file_parser\\test_files\\text_test_1.pdf") == test_string.replace("\n","")
    #print(parse_file("tests\\file_parser\\text_test_2.pdf"))
    assert isinstance(parse_file("tests\\file_parser\\test_files\\text_test_2.pdf"), str)


def test_complex_pdf():
    result = parse_file("tests\\file_parser\\test_files\\test_textbook2.pdf")
    print(result)
    #assert result == "dog"
    assert isinstance(result, str)