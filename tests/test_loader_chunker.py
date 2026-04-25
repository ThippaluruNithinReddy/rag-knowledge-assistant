"""
This file manually tests the document loader and chunker services.

Why it exists:
We want one simple script that can be run directly with Python to verify
that Step 7 and Step 8 work correctly with a real PDF before moving on.
"""

import sys
from pathlib import Path


# Add the project root to Python's import path so this script can be run directly.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.chunker import chunk_documents
from app.services.document_loader import load_document


# Real PDF file used for manual Step 7 and Step 8 testing.
TEST_PDF_PATH = (
    PROJECT_ROOT / "tests" / "sample_docs" / "techcorp_handbook.pdf"
)


def print_header(title: str) -> None:
    """
    Print a clear section header so test output is easy to follow.
    """
    print(f"\n{'=' * 60}")
    print(title)
    print(f"{'=' * 60}")


def print_result(test_name: str, passed: bool, details: str) -> None:
    """
    Print a consistent PASS/FAIL result line.
    """
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {test_name}")
    print(f"      {details}")


def main() -> None:
    """
    Run manual checks for document loading and chunking.
    """
    print_header("Loader + Chunker Manual Test")
    print(f"Project root : {PROJECT_ROOT}")
    print(f"Test PDF path: {TEST_PDF_PATH}")

    if not TEST_PDF_PATH.exists():
        print_result(
            "Sample PDF exists",
            False,
            "Place a real PDF at tests/sample_docs/your_filename.pdf before running this script.",
        )
        return

    try:
        print_header("Step 1 - Load the PDF")
        documents = load_document(str(TEST_PDF_PATH))

        # Test 1: The loader returns one or more Document objects.
        load_success = len(documents) > 0
        print_result(
            "PDF loads successfully",
            load_success,
            f"Documents returned: {len(documents)}",
        )

        # Test 2: The loaded documents contain readable text.
        combined_text = " ".join(
            document.page_content.strip()
            for document in documents
            if document.page_content.strip()
        )
        has_text = len(combined_text) > 0
        print_result(
            "Loaded documents contain text",
            has_text,
            f"Combined text length: {len(combined_text)} characters",
        )

        # Test 3: Every document keeps the filename in source metadata.
        expected_source = TEST_PDF_PATH.name
        metadata_ok = all(
            document.metadata.get("source") == expected_source
            for document in documents
        )
        print_result(
            "Source metadata is attached correctly",
            metadata_ok,
            f"Expected source: {expected_source}",
        )

        print_header("Step 2 - Chunk the loaded documents")
        chunks = chunk_documents(documents)

        # Test 4: Chunking creates chunks and preserves source metadata.
        chunks_created = len(chunks) > 0
        chunk_metadata_ok = all(
            chunk.metadata.get("source") == expected_source
            for chunk in chunks
        )
        chunking_ok = chunks_created and chunk_metadata_ok
        print_result(
            "Chunking works and keeps metadata",
            chunking_ok,
            (
                f"Chunks created: {len(chunks)}, "
                f"all chunks keep source metadata: {chunk_metadata_ok}"
            ),
        )

        print_header("Sample Output Preview")
        if documents:
            print("First loaded document metadata:")
            print(documents[0].metadata)
            print("\nFirst loaded document text preview:")
            print(documents[0].page_content[:300] or "[No text found]")

        if chunks:
            print("\nFirst chunk metadata:")
            print(chunks[0].metadata)
            print("\nFirst chunk text preview:")
            print(chunks[0].page_content[:300] or "[No text found]")

        print_header("Final Summary")
        all_tests_passed = load_success and has_text and metadata_ok and chunking_ok
        if all_tests_passed:
            print("All four checks passed. Step 7 and Step 8 look good.")
        else:
            print("One or more checks failed. Review the output above before moving to Step 9.")

    except Exception as exc:
        print_header("Test Script Error")
        print(f"The script stopped because of an error: {exc}")


if __name__ == "__main__":
    main()
