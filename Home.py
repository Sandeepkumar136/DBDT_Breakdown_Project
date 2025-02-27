import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import os
import chardet  # Encoding detection
import logging
from datetime import datetime

# Configure Tesseract OCR Path (Modify for Windows users)
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# Define Directories
INPUT_DIR = "input_pdfs"
OUTPUT_DIR_TEXT = "extracted_text"
OUTPUT_DIR_OCR = "ocr_extracted_text"
LOG_DIR = "logs"

# Ensure all directories exist
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR_TEXT, exist_ok=True)
os.makedirs(OUTPUT_DIR_OCR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Create a log file with timestamp
log_filename = os.path.join(LOG_DIR, f"run_log_{datetime.now().strftime('%Y-%m-%d')}.txt")

# Configure Logging
logging.basicConfig(filename=log_filename, level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s", filemode="a")


def detect_encoding(text):
    """Detects the encoding of extracted text."""
    result = chardet.detect(text.encode())
    return result["encoding"] if result["encoding"] else "utf-8"


def extract_metadata(pdf_path):
    """Extracts metadata from a PDF file."""
    try:
        doc = fitz.open(pdf_path)
        metadata = doc.metadata
        pdf_name = os.path.basename(pdf_path)

        extracted_info = {
            "Title": metadata.get("title", "Unknown"),
            "Author": metadata.get("author", "Unknown"),
            "Creation Date": metadata.get("creationDate", "Unknown"),
            "Modification Date": metadata.get("modDate", "Unknown"),
        }

        logging.info(f"📄 Extracted metadata for {pdf_name}: {extracted_info}")
        return extracted_info

    except Exception as e:
        logging.error(f"❌ Error extracting metadata from {pdf_path}: {str(e)}")
        return None


def extract_text_from_pdf(pdf_path):
    """Extracts selectable text from a PDF and saves it to a text file."""
    try:
        if not os.path.exists(pdf_path):
            logging.warning(f"❌ File not found: {pdf_path}")
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
                logging.warning(f"⚠️ No selectable text on Page {page_num + 1} of {pdf_name}")

        if not full_text.strip():
            logging.warning(f"⚠️ No selectable text found in {pdf_path}")
            return

        encoding = detect_encoding(full_text)

        # Save extracted text
        output_file = os.path.join(OUTPUT_DIR_TEXT, f"{pdf_name}.txt")
        with open(output_file, "w", encoding=encoding) as file:
            file.write(full_text)

        logging.info(f"✅ Extracted text saved to {output_file}")

    except Exception as e:
        logging.error(f"❌ Error processing {pdf_path}: {str(e)}")


def extract_text_from_image(image):
    """Extracts text from an image using OCR."""
    return pytesseract.image_to_string(image).strip()


def extract_text_from_scanned_pdf(pdf_path):
    """Extracts text from scanned PDFs using OCR and saves as .txt files."""
    try:
        if not os.path.exists(pdf_path):
            logging.warning(f"❌ File not found: {pdf_path}")
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
                logging.warning(f"⚠️ No text found on Page {page_num + 1} of {pdf_name}")
                continue

            # Save OCR text to a file
            output_file = os.path.join(OUTPUT_DIR_OCR, f"{pdf_name}_page_{page_num + 1}.txt")
            with open(output_file, "w", encoding="utf-8") as file:
                file.write(f"-- Page {page_num + 1} --\n{extracted_text}")

            logging.info(f"✅ OCR text extracted and saved to {output_file}")

    except Exception as e:
        logging.error(f"❌ Error processing {pdf_path}: {str(e)}")


if __name__ == "__main__":
    logging.info("\n📌 Starting PDF Processing...\n")

    # Ensure input folder has PDFs
    pdf_files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".pdf")]
    if not pdf_files:
        logging.error("❌ No PDF files found in 'input_pdfs'. Please add PDFs.")
        exit()

    for filename in pdf_files:
        pdf_path = os.path.join(INPUT_DIR, filename)

        logging.info(f"\n🔹 Processing: {filename}")

        # Extract Metadata
        metadata = extract_metadata(pdf_path)
        if metadata:
            print(f"\n📄 Metadata for {filename}:")
            for key, value in metadata.items():
                print(f"   {key}: {value}")

        # Extract Selectable Text
        extract_text_from_pdf(pdf_path)

        # Extract OCR Text from Scanned PDFs
        extract_text_from_scanned_pdf(pdf_path)

    logging.info("\n✅ All PDFs processed successfully!")
