import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import os
import chardet  # Encoding detection

# Configure Tesseract OCR Path (Modify for Windows users)
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# Define input and output directories
INPUT_DIR = "input_pdfs"  # Folder for input PDFs
OUTPUT_DIR_TEXT = "extracted_text"  # Folder for normal text extraction
OUTPUT_DIR_OCR = "ocr_extracted_text"  # Folder for OCR-extracted text

# Ensure output directories exist
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR_TEXT, exist_ok=True)
os.makedirs(OUTPUT_DIR_OCR, exist_ok=True)


def detect_encoding(text):
    """Detects the encoding of extracted text."""
    result = chardet.detect(text.encode())
    return result["encoding"] if result["encoding"] else "utf-8"


def extract_text_from_pdf(pdf_path):
    """Extracts selectable text from a PDF and saves it to a text file."""
    try:
        if not os.path.exists(pdf_path):
            print(f"❌ File not found: {pdf_path}")
            return

        doc = fitz.open(pdf_path)
        pdf_name = os.path.basename(pdf_path).replace(".pdf", "")
        full_text = ""

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text").strip()

            if text:
                full_text += f"\n-- Page {page_num + 1} --\n{text}"
            else:
                print(f"⚠️ No selectable text on Page {page_num + 1}.")

        if not full_text.strip():
            print(f"⚠️ No selectable text found in {pdf_path}, skipping...")
            return

        # Detect encoding
        encoding = detect_encoding(full_text)

        # Save extracted text
        output_file = os.path.join(OUTPUT_DIR_TEXT, f"{pdf_name}.txt")
        with open(output_file, "w", encoding=encoding) as file:
            file.write(full_text)

        print(f"✅ Extracted text saved to {output_file}")

    except Exception as e:
        print(f"❌ Error processing {pdf_path}: {str(e)}")


def extract_text_from_image(image):
    """Extracts text from an image using OCR."""
    text = pytesseract.image_to_string(image)
    return text.strip()


def extract_text_from_scanned_pdf(pdf_path):
    """Extracts text from scanned PDFs using OCR and saves as .txt files."""
    try:
        if not os.path.exists(pdf_path):
            print(f"❌ File not found: {pdf_path}")
            return

        doc = fitz.open(pdf_path)
        pdf_name = os.path.basename(pdf_path).replace(".pdf", "")

        for page_num in range(len(doc)):
            page = doc[page_num]

            # Convert page to an image
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # Extract text using OCR
            extracted_text = extract_text_from_image(img)

            if not extracted_text.strip():
                print(f"⚠️ No text found on Page {page_num + 1}.")
                continue

            # Save OCR text to a file
            output_file = os.path.join(OUTPUT_DIR_OCR, f"{pdf_name}_page_{page_num + 1}.txt")
            with open(output_file, "w", encoding="utf-8") as file:
                file.write(f"-- Page {page_num + 1} --\n{extracted_text}")

            print(f"✅ OCR text extracted and saved to {output_file}")

    except Exception as e:
        print(f"❌ Error processing {pdf_path}: {str(e)}")


if __name__ == "__main__":
    print("\n📌 Starting PDF Text Extraction...\n")

    # Ensure input folder has PDFs
    pdf_files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".pdf")]
    if not pdf_files:
        print("❌ No PDF files found in 'input_pdfs' folder. Please add some PDFs.")
        exit()

    for filename in pdf_files:
        pdf_path = os.path.join(INPUT_DIR, filename)

        print(f"\n🔹 Processing: {filename}")

        # Step 1: Extract selectable text
        extract_text_from_pdf(pdf_path)

        # Step 2: Extract text from scanned pages using OCR
        extract_text_from_scanned_pdf(pdf_path)

    print("\n✅ All PDF files processed successfully!")
