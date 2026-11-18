"""
file_validation.py - Check that an uploaded file is safe and really what it claims to be.

We never trust the file name alone. "virus.exe" renamed to "policy.pdf" must be rejected,
so we look at the first bytes of the file (its "magic number" / signature):
- PDF  files always start with  %PDF-
- DOCX files are ZIP archives that contain word/document.xml
- TXT  files must be readable text with no binary zero bytes
"""

import zipfile
from pathlib import Path

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}


class FileValidationError(Exception):
    """
    Raised when a file must be rejected. The message is safe to show to the user.
    'code' is one of: invalid, unsupported_type, too_large (the API turns it into a status code).
    """

    def __init__(self, message, code="invalid"):
        super().__init__(message)
        self.code = code


def get_extension(filename: str) -> str:
    return Path(filename or "").suffix.lower().lstrip(".")


def validate_file(path, original_filename, max_bytes, allowed=ALLOWED_EXTENSIONS):
    """
    Check type, size and real content. Returns the file type ("pdf", "docx" or "txt").
    Raises FileValidationError with a clear message if the file is not acceptable.
    """
    path = Path(path)
    ext = get_extension(original_filename)

    if ext not in allowed:
        raise FileValidationError(
            f"Unsupported file type '.{ext or '?'}'. Allowed types: "
            + ", ".join(f".{e}" for e in sorted(allowed)) + ".",
            code="unsupported_type",
        )

    size = path.stat().st_size
    if size == 0:
        raise FileValidationError("The file is empty.")
    if size > max_bytes:
        raise FileValidationError(
            f"The file is too large. Maximum size is {max_bytes // (1024 * 1024)} MB.", code="too_large"
        )

    with open(path, "rb") as f:
        head = f.read(8192)

    if ext == "pdf" and not head.startswith(b"%PDF-"):
        raise FileValidationError("The file has a .pdf name but is not a real PDF document.")

    if ext == "docx":
        if not zipfile.is_zipfile(path):
            raise FileValidationError("The file has a .docx name but is not a real Word document.")
        with zipfile.ZipFile(path) as z:
            if "word/document.xml" not in z.namelist():
                raise FileValidationError("The file has a .docx name but is not a real Word document.")

    if ext == "txt":
        if b"\x00" in head:
            raise FileValidationError("The .txt file contains binary data and is not a text file.")
        try:
            head.decode("utf-8")
        except UnicodeDecodeError as error:
            # A multi-byte character may be cut at the 8 KB border; only fail on real problems
            if error.start < len(head) - 4:
                try:
                    head.decode("cp1252")
                except UnicodeDecodeError:
                    raise FileValidationError("The .txt file is not readable text.") from None

    return ext
