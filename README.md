# Instructional Chatbot for UCR

Developed as part of the Pathway program during the summer of 2025.

## Getting It Running

If you are using `pip` to manage dependencies, run

```bash
pip install . && pip uninstall -y ucr_chatbot
flask --app ucr_chatbot run
```

from the root directory of this repository.

If you are using [uv](https://docs.astral.sh/uv/), which is highly recommended,
then you can use

```bash
uv run flask --app ucr_chatbot run
```

## See Also
- [CONTRIBUTING.md](https://github.com/joshua-zingale/ucr-chatbot-pathway-program/blob/master/CONTRIBUTING.md)
- [Project Outline](https://joshua-zingale.github.io/ucr-chatbot-pathway-program/project-plan/)
