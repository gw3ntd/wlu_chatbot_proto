# AI Tutor

**Objective**: The objective of this research project is to develop a WLU themed chatbot tutor for introductory statistics. Our research plan aims to improve upon existing research conducted by undergraduate student Ms. Gwen Horzempa during the summer of 2025 [3]. Using theory and algorithms from machine learning and artificial intelligence, we aim to add image recognition functionality and improve response relevance. This chatbot tutor will have a web interface that students could log into and seek assistance from the AI tutor. 

**Keywords**: _Retreival Augmented Generation, Language Model, Web Development,
Data Management, API Integration._

## Introduction
Many of WLU’s programs require students to take MATH 160 - Introduction to Statistics in order to complete their degrees. In addition, some students take this course to fulfill their General Education requirements. With an annual enrollment of around 200 students, MATH 160 is the most sought after math course for tutoring. The enrollment mentioned above is the number of students who finish the course, with dozens of students withdrawing from the course. The Student Success Center (SSC) employs only a few statistics tutors, who are themselves WLU students with busy schedules. One benefit of this proposed AI tutor is that students could use it from anywhere. Many students are hesitant to make appointments with a personal tutor for various reasons. Some are shy; some are embarrassed; some encounter difficulty with the online scheduling platform, or are simply unavailable during all of the available time slots. With this software students would not have to go to the SSC to get help. Increasing the statistics tutoring capability of WLU should increase the retention of students in this course and improve the grades of those who remain in the course.

## The Project
The concept inspiration comes from the familiar AI chatbots that most of us are already familiar with, e.g., ChatGPT, Gemini, Copilot, etc. Most students are familiar with interacting with a chatbot, and many are now familiar with using generative AI to assist them in their education. Using a chatbot tutor is not the same as logging in to ChatGPT and asking it to do your statistics homework. The latter process will not foster long-term understanding and can produce spurious or hallucinatory responses. The AI tutor gives one-sentence responses and asks leading questions. Also, the proposed tutor will reference statistics content from authoritative sources uploaded to the tutor by WLU instructors, which increases the response relevance given to a student. This is known as  retrieval-augmented generation (RAG) [2]. RAG is an algorithmic way to optimize the output of a large language model (LLM) by referencing an authoritative knowledge database outside the LLM’s training dataset prior to generating an output response. Figure 1 (to the left) illustrates the process of using RAG with an LLM. This is a well understood procedure for improving LLM responses. Ms. Horzempa has already participated in research that successfully developed the proof of concept of this aspect of our proposed research.

Our proposed improvements lie mainly in improving the enhanced context input to the LLM by extending the repertoire of content modalities that may be input as a prompt or as an authoritative source. We plan to include handwritten content in the collection of files that may be parsed into segments and embeddings. The idea is that either a student or an instructor can scan handwritten notes, or images thereof, and the backend of the chatbot has the capability to convert the image (including mathematical symbols) into parseable information, similar to what can be parsed from a typed document, a .pdf file, or an audio file. This capability lies in the domain of computer vision, and specifically, computer image recognition and classification. For example, we want the algorithm to recognize the handwritten image of the word Variance and parse it as the text “Variance,” (Figure 2 to the left).  There is a tremendously important distinction between the two in terms of passing information to an LLM in order to elicit a response. We will do this using a deep convolutional neural network (CNN) [1]. CNNs emerged from the study of the human brain’s visual cortex and have been in use since the 1980s. CNNs have a layered architecture (hence, the word “deep”), with each layer consisting of a collection of artificial neurons. These neurons are not connected to all of the pixels in the entire image. Instead, they are only connected to the pixels in some receptive field, which is controlled by a parameter that needs to be learned during the training process. Each of these neural network layers is referred to as a “convolutional layer.” There is a sophisticated mathematical algorithm at play in this training process.

The final aim for this project will be to create a well-defined metric and a sequence of measurable tests that permit us to evaluate the response relevance of our AI chatbot. This effort will balance the objective correctness of chatbot responses with the subjective quality of those responses, with increasing scores converging to some idealistic, perfect tutor.

## Expected Outcomes
We expect to produce a local (on the researchers’ computers) operational version of the chatbot tutor by the end of the project. The chatbot will have a WLU theme and have all of the capabilities outlined in the Methods section of this proposal. Moreover, we expect that the chatbot will have successfully passed the evaluation sessions conducted by volunteer math students and faculty members. At the conclusion of this project the chatbot should be ready for deployment, but the logistics of integrating student authentication with an IT database, deploying on a WLU webpage for ease of student access, and any other required administrative tasks set forth by the institution are not included as part of this proposal. We are requesting funding only to create the chatbot tutor and make it ready for the process of deployment, which will likely need to be figured out over the Summer of 2026. Dr. Holsapple will assist in this process and work with IT, the SSC, and the Provost’s Office in his role as Chair of Physical Sciences and Mathematics.

## References
[1] Géron A. Hands-on machine learning with scikit-learn, keras, and tensorflow. 3rd ed. O’Reilly Media; 2022.  
[2] Wikipedia contributors. Retrieval-augmented generation. Wikipedia, The Free Encyclopedia. 2025 Sept 8. https://en.wikipedia.org/w/index.php?title=Retrieval-augmented_generation&oldid=1310173852.  
[3] Claborn C, Clark E, Horzempa G, et al. ScottGPT: A Generative-AI Instructional Chatbot for UCR. University of California, Riverside National Science Foundation Research Experience for Undergraduates. August 2025.

## Past Work
The following was written during the Pathway program, and this work is currently still implemented in the chatbot.
### Interaction Diagram

Here is how an interaction might go for a student using the chatbot.

![student-interaction-flowchart](student-interaction.png)

### Project breakdown

This project can be broken down into the following tasks:

- Web Design
  - User Authentication
  - Document Uploading
  - Chat Interface
  - Consistent Styling
- Language Model API
  - Expose an API to the Rest of Our Application for Accessing a Language Model
- Retrieval Augmented Generation
  - Document Parsing
  - Retrieval of Relevent Course Documents/Segments
  - Chatbot Message Generation

After a look on the database schema, each of these tasks will be explained
further.

## Database Schema

The database is the center of the entire application and is thus of highest
importance. For our system, we will need one database that stores everything
relevent to providing our service and logging interactions. Our system will have
the following entities:

- Users
- Courses
- Conversations
- Messages
- Documents
- Segments
- Embeddings

Segments are short portions of documents and embeddings are vector embeddings
for segments to be used for retrieval augmented generation.

### Entity Relationships

Refer the the following Entity Relationship (ER) diagram. Rectangles are
entities, diamonds are relationships, and ovals are attributes. All of the
attributes for each entity and relation are not included and this diagram only
gives a rough estimate of what our final schema may be. An arrow indicates a
one-to-many relation, where the arrow points to the "one".

![database-schema](data-model.png)

The purpose of this ER design is to allow us to track data about how students,
assistants, and the chatbot interact with the system. For example, we may learn
that the source of most chatbot failures is incorrectly referencing course
material.

### Technologies

For our central database, we will use [PostgreSQL](https://www.postgresql.org/).
To store vector embeddings, we could use the the
[pgvector](https://github.com/pgvector/pgvector/) extension. Alternatively, the
vector storage could be offloaded to a specialized vector database like
[ChromaDB](https://www.trychroma.com/). The choice for how to store the vectors
is yet to be made.

To simplify integration of the database into our Python code, we will use
[SQLAlchemy](https://www.sqlalchemy.org/). SQLAlchemy provides an Object
Relational Mapping (ORM) for the database, making code easier to read than it
would be were it to be riddled with SQL queries. Everyone on the team should get
comfortable with SQLAlchemy in Python because accessing the database is vital to
all aspects of this project.

## Web Design

Students and instructors will interface with the chatbot
system through a website. Users should be authenticated via a login procedure
that links our users to students and faculty at West Liberty University.

The chat interface is the central offering of this system. We want something
that looks like any of the other chatbots out there, like Gemini, where the
student can start a new conversation, write a message, and see past messages
from himself and from the chatbot. 

We also need an instructor portal, in which an instructor can upload documents
to be used by the chatbot as context for answering questions.


## Technologies

[Flask](https://flask.palletsprojects.com/en/stable/) is a light-weight
web-application framework for Python. Since Python is the language of choice for
all things machine learning and data science, using Python also for our
web-development increases uniformity for easier integration, as opposed to using
any of the many Javascript frameworks. We are using Flask because the our
feature set is not large enough to warrant a more heavy-duty framework like
Django. Flask provides all of the needed functions for setting up routing,
managing HTML with templates, and serving static files.

Our campus uses Google authentication for campus-wide accounts, including
emails. We want to use WLU email accounts as credentials to access the chatbot,
so we should look into integrating a
[Google login into our Flask application](https://realpython.com/flask-google-login/).

## Language Model API

There are many different API services for getting access to state-of-the-art
language models. There are OpenAI, Gemini, Claude, and more. While we may begin
using one API, we do not want to be overly coupled with any specific service. We
therefore want to develop an internal API service for getting completions from a
language model. Being thus decoupled would allow us to change vendors to meet
developing needs or to use emergent abilities of another provider, all without
modifying code elsewhere in our library, so long as our developed API remains
consistent.

### Technologies

[Flask](https://flask.palletsprojects.com/en/stable/) is to be used for the web
interface and it thus makes sense to use it here as well.

For testing, we could run a model locally with [Ollama](https://ollama.com/) or
[HuggingFace](https://huggingface.co/). For production, we are likely to opt for
an external API, like Google's [Gemini](https://ai.google.dev/gemini-api/docs).

## Retrieval Augmented Generation

Retrieval Augmented Generation (RAG) is a technique for reducing language-model
hallucination and increasing relevence of responses. With RAG, a prompt for the
language model, in this case a student's question, is used to find relevent text
segments from the data-store. After retrieving relevent segments of text, a new
prompt is constructed with the segments included for context. This new prompt is
finally fed to the language model for generation.

We will use this technique to help answer student questions in a way that is
appropriate to the course being taught. Therefore, each supported course will
have its own set of documents from which context is pulled.

Instructors will be uploading documents like powerpoint files, PDFs, and maybe
ebook formatted files. Current techniques for providing language models with
context work best with direct text input. We therefore shall want to parse these
documents of various formats into text. After converting these documents into
text, we will then need to split the document into segments to be used for RAG.

RAG typically works as follows: Each text segment in the database is stored
alongside a vector embedding of the text. When a user sends a query, this query
is embedded into a vector; then, the query embedding is compared against the
embeddings for the text segments; and, finally, the most similar text segments,
measured by vector similarity to the query's embedding, are added to the
original prompt for extra context. This updated prompt is then fed to a langauge
model for generation of the final response.

### Technologies

There are Python libraries like [PyPDF2](https://pypi.org/project/PyPDF2/) for
extracting text from documents.

Our method for finding relevent segments of text given a student query will
depend on how we opt to store the vector embeddings. Refer to the **Database
Schema** section.

For the actual language-model-powered text generation, we will use the
internally developed Language Model API.

