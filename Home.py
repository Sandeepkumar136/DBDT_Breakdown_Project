import fitz  # PyMuPDF
import os
import json
import chardet  # Encoding detection

# Define output directories
OUTPUT_DIR = "extracted_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

PAGEWISE_TEXT_DIR = os.path.join(OUTPUT_DIR, "pages")
os.makedirs(PAGEWISE_TEXT_DIR, exist_ok=True)


def detect_encoding(text):
    """Detects the encoding of the given text."""
    result = chardet.detect(text.encode())  # Convert to bytes for detection
    return result["encoding"] if result["encoding"] else "utf-8"


def extract_metadata(pdf_path):
    """Extracts metadata from a PDF and saves it as a JSON file."""
    try:
        if not os.path.exists(pdf_path):
            print(f"❌ File not found: {pdf_path}")
            return

        doc = fitz.open(pdf_path)
        metadata = doc.metadata  # Get metadata dictionary

        # Format metadata properly
        formatted_metadata = {
            "Title": metadata.get("title", "Unknown"),
            "Author": metadata.get("author", "Unknown"),
            "Subject": metadata.get("subject", "Unknown"),
            "Keywords": metadata.get("keywords", "None"),
            "CreationDate": metadata.get("creationDate", "Unknown"),
            "ModificationDate": metadata.get("modDate", "Unknown"),
            "Producer": metadata.get("producer", "Unknown"),
        }

        # Generate output filename dynamically
        pdf_name = os.path.basename(pdf_path).replace(".pdf", "")
        output_file = os.path.join(OUTPUT_DIR, f"{pdf_name}_metadata.json")

        # Save metadata to JSON file
        with open(output_file, "w", encoding="utf-8") as file:
            json.dump(formatted_metadata, file, indent=4)

        print(f"✅ Metadata extracted successfully! Saved to {output_file}")

    except Exception as e:
        print(f"❌ Error extracting metadata: {str(e)}")


def extract_text_pagewise(pdf_path):
    """Extracts text from each page and saves them as separate .txt files."""
    try:
        if not os.path.exists(pdf_path):
            print(f"❌ File not found: {pdf_path}")
            return

        doc = fitz.open(pdf_path)

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text").strip()

            if not text:
                print(f"⚠️ Page {page_num + 1} has no text.")
                continue

            # Detect text encoding
            encoding = detect_encoding(text)

            # Generate output filename
            pdf_name = os.path.basename(pdf_path).replace(".pdf", "")
            output_file = os.path.join(PAGEWISE_TEXT_DIR, f"{pdf_name}_page_{page_num + 1}.txt")

            # Save extracted text
            with open(output_file, "w", encoding=encoding) as file:
                file.write(text)

            print(f"✅ Page {page_num + 1} text extracted successfully! Saved to {output_file}")

    except Exception as e:
        print(f"❌ Error extracting text: {str(e)}")


# Run script
if __name__ == "__main__":
    # Change this path to your actual PDF file
    pdf_path = r"C:\Users\ksund\PycharmProjects\PythonProject\DBDT_Breakdown_Project\INPUT\Certificate.pdf"

    print("\n📌 Extracting PDF Metadata...")
    extract_metadata(pdf_path)

    print("\n📌 Extracting Page-wise Text...")
    extract_text_pagewise(pdf_path)
