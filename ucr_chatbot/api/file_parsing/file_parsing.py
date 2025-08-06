# type: ignore

from io import BufferedIOBase
from io import BytesIO
import speech_recognition as sr
from pydub import AudioSegment
from pydub.silence import split_on_silence
import tempfile
from typing import List
from pypdf import PdfReader
from pathlib import Path


class FileParsingError(ValueError):
    """File cannot be parsed."""

    pass


class InvalidFileExtensionError(FileParsingError):
    """Bad file extension"""

    def __init__(self, extension: str):
        super().__init__(f'Cannot interpret file with extension "{extension}"')


def parse_file(path: str) -> list[str]:
    """Parses a file into text.

    :param path: A file path to the file to be parsed.
    :raises InvalidFileExtension: If the input path has an invalid file extension at the end.
    :return: A textual representation of the file.
    """
    extension = Path(path).suffix[1:]
    with open(path, "rb") as f:
        if extension == "txt":
            return _parse_txt(f, lenseg=1000)
        elif extension == "wav":
            return _parse_audio(path, segments=True)
        elif extension == "mp3":
            return _parse_audio(path, segments=True)
        elif extension == "md":
            return _parse_md(f, 1000)
        elif extension == "pdf":
            return _parse_pdf(f, chars_per_seg=1000, overlap=2)
        else:
            raise InvalidFileExtensionError(extension)


def _parse_txt(txt_file: BufferedIOBase, lenseg=None) -> List[str]:
    """Parses a text file and removes whitespace. The function either returns
    a list of strings or a string

    :param txt_file: text file to be parsed
    :type txt_file: .txt

    :param lenseg: for segmenting the text, maximum desired length in characters of the segment,
    defaults to None. Also an indicator if the user wants to segment the file
    :type lenseg: int

    :return: string of all the text in the document or list of strings, where each item in the
    list is a segment of the text file
    :rtype: List[str] or str
    """

    if lenseg is not None:
        l = []
        content = ""  # full file content
        bigline = ""  # for segmenting purposes

        count = 0  # working character count
        tempstr = str(txt_file.read())
        new = tempstr.replace("\\n", "\n")[2:-1]
        for line in new:
            count = count + len(line)
            bigline = bigline + line.strip() + ""

            if count > lenseg or bigline.endswith("."):
                l.append(bigline)
                # resetting
                count = 0
                bigline = ""
        if len(bigline) > 0:
            l.append(bigline)
        return l
    else:
        content = ""  # Full file content
        tempstr = str(txt_file.read())
        new = tempstr.replace("\\n", "\n")[2:-1]
        for line in new:
            content = content + line.strip() + ""
        return [content]


def _parse_audio(audio_file: str, time=None, segments=False) -> List[str]:
    """Parses a .wav file or a .mp3 file into text. This function utilizes
    the pydub and speech_recognition libraries to transcribe the audio.

    :param audio_file: .wav or .mp3 file of a lecture
    :type audio_file: .wav or .mp3

    :param time: the length in seconds each chunk should be split up into,
    also indicates if the user wants to split the audio into chunks by
    time or by silence, defaults to None
    :type time: int

    :param segments: indicator of if this function should return a list of strings,
    aka segments, or a full transcription of text, defaults to False
    :type segments: bool

    :return: List of strings (segments) or text transcription
    :rtype: List[str] or str
    """

    current_directory = Path.cwd()
    transcript = ""
    l = []

    # Load audio
    if audio_file.endswith(".mp3"):
        audio = AudioSegment.from_mp3(audio_file)
        print("Mp3 file loaded")
    else:
        audio = AudioSegment.from_wav(audio_file)
        print("Wav file loaded")

    print("let us begin")

    # Creating a temporary directory to store chunks in

    with tempfile.TemporaryDirectory(dir=str(current_directory)) as temp_dir_path:
        print(f"Temporary directory created at: {temp_dir_path}")

        if time is not None:
            # Setup chunking
            chunk_length_ms = time * 1000
            total_length_ms = len(audio)
            chunks = (total_length_ms + chunk_length_ms - 1) // chunk_length_ms

            for index in range(chunks):
                start_time = index * chunk_length_ms
                end_time = min((index + 1) * chunk_length_ms, total_length_ms)

                chunk = audio[start_time:end_time]
                chunkname = "{0}_".format(index) + audio_file
                chunk_path = str(Path(temp_dir_path) / chunkname)
                print("I am exporting", chunk_path)
                chunk.export(chunk_path, format="wav")

                r = sr.Recognizer()
                with sr.AudioFile(chunk_path) as source:
                    r.adjust_for_ambient_noise(source)
                    audio_data = r.record(source)

                try:
                    rec = r.recognize_google(audio_data, language="en-us")  # type: ignore
                    l.append(rec)

                    transcript = (
                        transcript
                        + "\nSegment {0}: ".format(index + 1)
                        + rec.capitalize()
                        + ". "
                    )

                except sr.UnknownValueError:
                    print(f"Could not understand audio segment {index + 1}")

        else:
            chunks = split_on_silence(audio, min_silence_len=1100, silence_thresh=-70)
            print("chunks are being made")
            # The above line splits the .wav file into chunks based on silence
            # min_silence_len and silence_thresh were chosen to detect the end of
            # a sentence
            for index, chunk in enumerate(chunks):
                chunkname = "{0}_".format(index) + audio_file
                chunk_path = str(Path(temp_dir_path) / chunkname)
                print("I am exporting", chunk_path)
                chunk.export(chunk_path, format="wav")

                r = sr.Recognizer()
                with sr.AudioFile(chunk_path) as source:
                    r.adjust_for_ambient_noise(source)
                    audio = r.record(source)
                try:
                    rec = r.recognize_google(audio, language="en-us")  # type: ignore
                    l.append(rec)
                    transcript = (  # type: ignore
                        transcript
                        + "\nSegment {0}: ".format(index + 1)
                        + rec.capitalize()  # type: ignore
                        + ". "
                    )
                except sr.UnknownValueError:  # type: ignore
                    print("I don't recognize your audio")
    print("Temporary directory and its contents have been removed.")
    if segments:
        return l  # type: ignore
    else:
        return [transcript]  # type: ignore


def _parse_pdf(pdf_file: BufferedIOBase, chars_per_seg: int, overlap: int) -> list[str]:
    """Parses a pdf file into text

    :param path: A file path to the file to be parsed.
    :param chars_per_seg: approximate amount of max characters per segment, with a bit of overlap between
    :param overlap: how many sentences should overlap per section
    :return: A list of segments of the textural representation of the pdf file.
    """
    reader = PdfReader(BytesIO(pdf_file.read()))
    all_text = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            all_text.append(page_text)
    text = "\n".join(all_text)

    # Do not strip first character, preserve newlines
    text = text.replace("  ", " ")
    total_text = text.rstrip()

    # Initial split of text by sentences
    sentences = total_text.split(".")
    if sentences and sentences[-1] == "":
        sentences.pop(-1)
    for i in range(len(sentences)):
        sentences[i] += "."

    # Making sure no sentence is too long or document doesn't use proper sentences (like a slide deck)
    i = 0
    while i < len(sentences):
        sentence = sentences[i]
        if len(sentence) > (chars_per_seg / 2):
            temp_sentence = sentence
            sentences.pop(i)
            for j in range(0, len(temp_sentence), chars_per_seg):
                sentences.insert(i, temp_sentence[j : j + chars_per_seg])
                i += 1
        else:
            i += 1

    # Combining into larger sections, about chars_per_split
    segments: list[str] = []
    curr_segment = ""
    for i, sentence in enumerate(sentences):
        if (len(curr_segment) + len(sentence)) < chars_per_seg:
            curr_segment += sentence
        else:
            segments.append(curr_segment)
            curr_segment = ""
            for k in range(overlap, 0, -1):
                if i - k >= 0:
                    curr_segment += sentences[i - k]
    if curr_segment:
        segments.append(curr_segment)

    return segments


def _parse_md(md_file: BufferedIOBase, chars_per_seg: int) -> list[str]:
    """Parses a markdown file into text

    :param path: A file path to the file to be parsed.
    :param chars_per_seg: approximate amount of max characters per segment, with a bit of overlap between
    :return: A list of segments of the textual representation of the markdown file.
    """
    raw_string = str(md_file.read())
    new_string = raw_string.replace("\\r\\n", "\n")
    new_string = new_string.replace("\\'", "'")

    total_text = new_string[2:-1]

    # Split by sections in markdown
    sections = total_text.split("#")
    for i, section in enumerate(sections):
        if section == "":
            sections.pop(i)

    # Making sure no sentence is too long or document doesn't us proper sentences (like a slide deck)
    for i, section in enumerate(sections):
        if len(section) > chars_per_seg:
            temp_section = section
            sections.pop(i)
            for j in range(0, len(temp_section), chars_per_seg):
                sections.append(temp_section[j : j + chars_per_seg])

    # Combining into larger sections, about chars_per_split
    segments: list[str] = []
    curr_segment = ""
    for i, section in enumerate(sections):
        if (len(curr_segment) + len(section)) < chars_per_seg:
            curr_segment += section
        else:
            segments.append(curr_segment)
            curr_segment = sections[i - 1]
    segments.append(curr_segment)

    # for segment in segments:
    #     print(segment)
    #     print("------------------------------------")

    return segments
