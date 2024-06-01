from typing import List
import spacy
from spacy.tokens import Span
from typing import List, Dict

nlp = spacy.load("ru_core_news_sm")


def extract_metadata(text: str) -> Dict[str, List[str]]:
    """
    Extracts metadata from the text using spaCy NER for Russian.
    """
    doc = nlp(text)
    metadata = {"dates": [], "names": [], "companies": []}

    for ent in doc.ents:
        if ent.label_ == "DATE":
            metadata["dates"].append(ent.text)
        elif ent.label_ == "PERSON":
            metadata["names"].append(ent.text)
        elif ent.label_ == "ORG":
            metadata["companies"].append(ent.text)

    return metadata


def get_text_chunks(text: str, text_splitter) -> List[Dict[str, str]]:
    """Implement your text splitting logic and extract metadata here."""
    chunks = text_splitter.split(text)  # Assume this splits the text into chunks
    chunk_data = []
    for chunk in chunks:
        metadata = extract_metadata(chunk)
        chunk_data.append({"text": chunk, "metadata": metadata})
    return chunk_data
