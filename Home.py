import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import os
import chardet  # Encoding detection
import logging
import sqlite3
from datetime import datetime

# Configure Tesseract OCR Path (Modify for Windows users)
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# Define Directories
INPUT_DIR = "input_pdfs"
OUTPUT_DIR_TEXT = "extracted_text"
OUTPUT_DIR_OCR = "ocr_extracted_text"
LOG_DIR = "logs"
DB_DIR = "database"
DB_FILE = os.path.join(DB_DIR, "pdf_processing.db")

# Ensure all directories exist
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR_TEXT, exist_ok=True)
os.makedirs(OUTPUT_DIR_OCR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)

# Configure Logging
log_filename = os.path.join(LOG_DIR, f"run_log_{datetime.now().strftime('%Y-%m-%d')}.txt")
logging.basicConfig(filename=log_filename, level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s", filemode="a")


# SQLite Database Setup
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pdf_metadata (
            id INTEGER PRIMARY KEY,
            filename TEXT UNIQUE,
            title TEXT,
            author TEXT,
            creation_date TEXT,
            modification_date TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pdf_text (
            id INTEGER PRIMARY KEY,
            pdf_id INTEGER,
            page_number INTEGER,
            text_content TEXT,
            FOREIGN KEY (pdf_id) REFERENCES pdf_metadata(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ocr_text (
            id INTEGER PRIMARY KEY,
            pdf_id INTEGER,
            page_number INTEGER,
            ocr_content TEXT,
            FOREIGN KEY (pdf_id) REFERENCES pdf_metadata(id)
        )
    ''')

    conn.commit()
    conn.close()


# Detect Encoding
def detect_encoding(text):
    result = chardet.detect(text.encode())
    return result["encoding"] if result["encoding"] else "utf-8"


# Extract Metadata
def extract_metadata(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        metadata = doc.metadata
        pdf_name = os.path.basename(pdf_path)

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR IGNORE INTO pdf_metadata (filename, title, author, creation_date, modification_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (pdf_name, metadata.get("title", "Unknown"), metadata.get("author", "Unknown"),
              metadata.get("creationDate", "Unknown"), metadata.get("modDate", "Unknown")))

        conn.commit()
        conn.close()

        logging.info(f"📄 Extracted metadata for {pdf_name}")
    except Exception as e:
        logging.error(f"❌ Error extracting metadata from {pdf_path}: {str(e)}")


# Extract Selectable Text
def extract_text_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        pdf_name = os.path.basename(pdf_path).replace(".pdf", "")

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM pdf_metadata WHERE filename = ?", (pdf_name + ".pdf",))
        pdf_id = cursor.fetchone()

        if not pdf_id:
            logging.warning(f"⚠️ No metadata found for {pdf_name}, skipping text extraction")
            return

        pdf_id = pdf_id[0]

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text").strip()

            if text:
                cursor.execute("""
                    INSERT INTO pdf_text (pdf_id, page_number, text_content)
                    VALUES (?, ?, ?)
                """, (pdf_id, page_num + 1, text))

        conn.commit()
        conn.close()

        logging.info(f"✅ Text extracted from {pdf_name}")
    except Exception as e:
        logging.error(f"❌ Error extracting text from {pdf_path}: {str(e)}")


# Extract OCR Text
def extract_text_from_image(image):
    return pytesseract.image_to_string(image).strip()


def extract_text_from_scanned_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        pdf_name = os.path.basename(pdf_path).replace(".pdf", "")

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM pdf_metadata WHERE filename = ?", (pdf_name + ".pdf",))
        pdf_id = cursor.fetchone()

        if not pdf_id:
            logging.warning(f"⚠️ No metadata found for {pdf_name}, skipping OCR")
            return

        pdf_id = pdf_id[0]

        for page_num in range(len(doc)):
            page = doc[page_num]
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            ocr_text = extract_text_from_image(img)

            if ocr_text:
                cursor.execute("""
                    INSERT INTO ocr_text (pdf_id, page_number, ocr_content)
                    VALUES (?, ?, ?)
                """, (pdf_id, page_num + 1, ocr_text))

        conn.commit()
        conn.close()

        logging.info(f"✅ OCR text extracted from {pdf_name}")
    except Exception as e:
        logging.error(f"❌ Error processing OCR for {pdf_path}: {str(e)}")


# Main Execution
if __name__ == "__main__":
    logging.info("\n📌 Starting PDF Processing...\n")
    init_db()

    pdf_files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".pdf")]
    if not pdf_files:
        logging.error("❌ No PDF files found in 'input_pdfs'. Please add PDFs.")
        exit()

    for filename in pdf_files:
        pdf_path = os.path.join(INPUT_DIR, filename)
        logging.info(f"\n🔹 Processing: {filename}")
        extract_metadata(pdf_path)
        extract_text_from_pdf(pdf_path)
        extract_text_from_scanned_pdf(pdf_path)

    logging.info("\n✅ All PDFs processed successfully!")
