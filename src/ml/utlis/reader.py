"""Module contains common parsers for PDFs."""
from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Iterator,
)

import pymupdf
import ocrmypdf
import io

from langchain_core.documents import Document

from langchain_community.document_loaders.blob_loaders import Blob
from langchain_community.document_loaders.parsers.pdf import PyMuPDFParser
from langchain_community.document_loaders import PyMuPDFLoader

if TYPE_CHECKING:
    import fitz.fitz


_PDF_FILTER_WITH_LOSS = ["DCTDecode", "DCT", "JPXDecode"]
_PDF_FILTER_WITHOUT_LOSS = [
    "LZWDecode",
    "LZW",
    "FlateDecode",
    "Fl",
    "ASCII85Decode",
    "A85",
    "ASCIIHexDecode",
    "AHx",
    "RunLengthDecode",
    "RL",
    "CCITTFaxDecode",
    "CCF",
    "JBIG2Decode",
]


def ocr_the_page(page):
    src = page.parent
    doc = pymupdf.open()
    doc.insert_pdf(src, from_page=page.number, to_page=page.number)
    pdfbytes = doc.tobytes()
    inbytes = io.BytesIO(pdfbytes)
    outbytes = io.BytesIO()
    ocrmypdf.ocr(
        inbytes,
        outbytes,
        language="rus",
        output_type="pdf",
    )
    ocr_pdf = pymupdf.open("pdf", outbytes.getvalue())
    text = ocr_pdf[0].get_text()
    return text


class RuParser(PyMuPDFParser):
    def lazy_parse(self, blob):  # type: ignore[valid-type]
        """Lazily parse the blob."""
        import fitz

        with blob.as_bytes_io() as file_path:  # type: ignore[attr-defined]
            if blob.data is None:  # type: ignore[attr-defined]
                doc = fitz.open(file_path)
                doc.set_language(language="ru")
            else:
                doc = fitz.open(stream=file_path, filetype="pdf")
                doc.set_language(language="ru")

            yield from [
                Document(
                    ocr_the_page(page),
                    metadata=dict(
                        {
                            "source": blob.source,  # type: ignore[attr-defined]
                            "file_path": blob.source,  # type: ignore[attr-defined]
                            "page": page.number,
                            "total_pages": len(doc),
                        },
                        **{
                            k: doc.metadata[k]
                            for k in doc.metadata
                            if type(doc.metadata[k]) in [str, int]
                        },
                    ),
                )
                for page in doc
            ]


class MyLoader(PyMuPDFLoader):
    def _lazy_load(self, **kwargs: Any) -> Iterator[Document]:

        text_kwargs = {**self.text_kwargs, **kwargs}
        parser = RuParser(
            text_kwargs=text_kwargs, extract_images=self.extract_images
        )
        if self.web_path:
            blob = Blob.from_data(open(self.file_path, "rb").read(), path=self.web_path)  # type: ignore[attr-defined]
        else:
            blob = Blob.from_path(self.file_path)  # type: ignore[attr-defined]
        yield from parser.lazy_parse(blob)


def is_scans(pdf_path):
    doc = pymupdf.open(pdf_path)
    text_pages = 0
    image_pages = 0

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text("text")
        images = page.get_images(full=True)

        if text.strip():
            text_pages += 1
        if images:
            image_pages += 1

    return image_pages



