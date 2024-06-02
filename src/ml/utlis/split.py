from typing import List
import spacy
from spacy.tokens import Span
from typing import List, Dict

nlp = spacy.load("ru_core_news_sm")


def extract_metadata(text: str) -> Dict[str, str]:
    doc = nlp(text)
    metadata = {"date": "", "name": "", "company": ""}

    for ent in doc.ents:
        if ent.label_ == "DATE" and metadata["date"] == "":
            metadata["date"] = ent.text
        elif ent.label_ == "PERSON" and metadata["name"] == "":
            metadata["name"] = ent.text
        elif ent.label_ == "ORG" and metadata["company"] == "":
            metadata["company"] = ent.text

    return metadata


def get_text_chunks(text: str, splitter) -> List[Dict[str, str]]:
    """Implement your text splitting logic and extract metadata here."""
    chunks = [x for x in splitter.split_text(text)]  # Assume this splits the text into chunks
    chunk_data = []
    for chunk in chunks:
        metadata = extract_metadata(chunk)
        chunk_data.append({"text": chunk, "metadata": metadata})
    return chunk_data


def split_chunks_and_metadata(chunk_data: List[Dict[str, str]]) -> (List[str], List[Dict[str, str]]):
    """
    Splits a list of dictionaries into two lists: one for text chunks and one for metadata.

    :param chunk_data: List of dictionaries with 'text' and 'metadata' keys.
    :return: A tuple of two lists: text_chunks and metadata_chunks.
    """
    text_chunks = [chunk["text"] for chunk in chunk_data]
    metadata_chunks = [chunk["metadata"] for chunk in chunk_data]
    return text_chunks, metadata_chunks
