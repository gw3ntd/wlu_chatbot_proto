# AI Tutor

**Objective**: Develop a generative-AI-powered tutor with a web interface to answer student questions about course materials and logistics, with an ability to elevate to a human tutor for difficult questions and an ability to compose reports from tutor-student interactions.

**Technology Keywords**: *Retreival Augmented Generation, Language Model, Web Development, Data Management, API Integration.*

## Introduction
Universities across the nation are integrating generative-AI into their pedagicial tool belts. Some have developed specialized generative-AI systems for more specialized use. For example,

- [Atlas at Stanford](https://gse-it.stanford.edu/project/atlas-chatbot);
- [Harvard's CS50 Tutor](https://cs.harvard.edu/malan/publications/V1fp0567-liu.pdf);
- [UC Irvine's ZotGPT](https://zotgpt.uci.edu/).

The advantage of developing a specialized system lies in that the AI tutor may be more tuned to the needs of the institution. We therefore want to develop such an AI tutoring system for use at UC Riverside in order to meet the needs of our students, faculty, and institution. While addressing all needs of UC Riverside is the ultimate goal, for this project we shall focus on one aspect of our learning environment: the [Undergraduate Learning Assistant (ULA) program](https://ula.cs.ucr.edu/).

ULA offers peer tutoring for undergraduates in computer-science courses. ULA is staffed by former students of each supported course, positioning the tutors well to assist current students with the material. To receive aid with a ULA-supported course, a student may navigate to the ULA homepage and view the schedule of when tutors will be available for in-person tutoring.

We want to develop an AI-powered system to help meet the learning needs of more students by assisting the ULAs.

## The Project

We are to develop a chatbot system that has the following features:

* There should be a web endpoint for the chatbot with a user interface akin to ChatGPT, Gemini, or any other chatbot.
* An instructor for the course should be able to upload course materials for use by the chatbot.
* The chatbot should be able to answer student questions by referencing relevent course materials.
* If the chatbot cannot answer the student's question from the course materials, the conversation should be elevated to a human tutor.
    * Option one is to have a ULA join the conversation with abilities to read and writes messages.
    * The chatbot should also be able to provide the student with a schedule for upcoming office hours/ULA hours for the course.
* The system should be able to generate a report for the instructor across all interactions to learn what students needed help with for any given course.
