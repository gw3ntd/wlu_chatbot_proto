# Instructional Chatbot for WLU

Developed as part of UCR's Pathway program during the summer of 2025.
Continued by Dr. Raymond Holsapple and Gwen Horzempa at WLU through a Research Enhancement Award.

## Getting It Running

If you are using `pip` to manage dependencies, run

```bash
pip install . && pip uninstall -y wlu_chatbot
flask --app wlu_chatbot run
```

from the root directory of this repository.

## Working with the Database
Starting the Database:
```bash
docker compose up -d app
docker compose exec app uv run wlu_chatbot db initialize --force
```

Adding Users, Courses, and Roles:
```bash
docker compose exec app uv run wlu_chatbot db create user ghorzempa@westliberty.edu yourpassword
docker compose exec app uv run wlu_chatbot db create course "MATH160-1"
docker compose exec app uv run wlu_chatbot db create participates_in ghorzempa@westliberty.edu 1 instructor
```

Resetting Docker Image:
```bash
docker compose down --rmi all --volumes --remove-orphans
```

If you are using [uv](https://docs.astral.sh/uv/), which is highly recommended,
then you can use

```bash
uv run flask --app wlu_chatbot run
```

## See Also

- [CONTRIBUTING.md](https://github.com/joshua-zingale/ucr-chatbot-pathway-program/blob/master/CONTRIBUTING.md)
- [Project Outline](https://joshua-zingale.github.io/ucr-chatbot-pathway-program/project-plan/)
