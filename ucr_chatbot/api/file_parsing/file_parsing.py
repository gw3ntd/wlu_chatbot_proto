from io import BufferedIOBase
from pathlib import Path
import speech_recognition as sr
from pydub import AudioSegment
from pydub.silence import split_on_silence
import os
import tempfile
from typing import List


class FileParsingError(ValueError):
    """File cannot be parsed."""

    pass


class InvalidFileExtensionError(FileParsingError):
    """Bad file extension"""

    def __init__(self, extension: str):
        self.__init__(f'Cannot interpret file with extension "{extension}"')


# type: ignore


def parse_file(path: str) -> List[str]:
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

    current_directory = os.getcwd()
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

    with tempfile.TemporaryDirectory(dir=current_directory) as temp_dir_path:
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
                chunk_path = os.path.join(temp_dir_path, chunkname)
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
                chunk_path = os.path.join(temp_dir_path, chunkname)
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
