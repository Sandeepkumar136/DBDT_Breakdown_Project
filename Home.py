import os
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import logging
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify

# Configure Flask App
app = Flask(__name__)

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


# Initialize SQLite Database
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pdf_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE,
            title TEXT,
            author TEXT,
            creation_date TEXT,
            modification_date TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pdf_text (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pdf_id INTEGER,
            page_number INTEGER,
            text_content TEXT,
            FOREIGN KEY (pdf_id) REFERENCES pdf_metadata(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ocr_text (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pdf_id INTEGER,
            page_number INTEGER,
            ocr_content TEXT,
            FOREIGN KEY (pdf_id) REFERENCES pdf_metadata(id)
        )
    ''')

    conn.commit()
    conn.close()


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
        return metadata
    except Exception as e:
        logging.error(f"❌ Error extracting metadata from {pdf_path}: {str(e)}")
        return None


# Extract Selectable Text
def extract_text_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        pdf_name = os.path.basename(pdf_path)

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM pdf_metadata WHERE filename = ?", (pdf_name,))
        pdf_id = cursor.fetchone()

        if not pdf_id:
            return "⚠️ No metadata found for this PDF."

        pdf_id = pdf_id[0]
        extracted_text = {}

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text").strip()

            if text:
                cursor.execute("""
                    INSERT INTO pdf_text (pdf_id, page_number, text_content)
                    VALUES (?, ?, ?)
                """, (pdf_id, page_num + 1, text))
                extracted_text[f"Page {page_num + 1}"] = text

        conn.commit()
        conn.close()

        return extracted_text
    except Exception as e:
        logging.error(f"❌ Error extracting text from {pdf_path}: {str(e)}")
        return None


# Extract OCR Text from Scanned PDFs
def extract_text_from_image(image):
    return pytesseract.image_to_string(image).strip()


def extract_text_from_scanned_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        pdf_name = os.path.basename(pdf_path)

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM pdf_metadata WHERE filename = ?", (pdf_name,))
        pdf_id = cursor.fetchone()

        if not pdf_id:
            return "⚠️ No metadata found for this PDF."

        pdf_id = pdf_id[0]
        ocr_text = {}

        for page_num in range(len(doc)):
            page = doc[page_num]
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            text = extract_text_from_image(img)

            if text:
                cursor.execute("""
                    INSERT INTO ocr_text (pdf_id, page_number, ocr_content)
                    VALUES (?, ?, ?)
                """, (pdf_id, page_num + 1, text))
                ocr_text[f"Page {page_num + 1}"] = text

        conn.commit()
        conn.close()

        return ocr_text
    except Exception as e:
        logging.error(f"❌ Error processing OCR for {pdf_path}: {str(e)}")
        return None


# Flask API Endpoints
@app.route('/upload', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    filepath = os.path.join(INPUT_DIR, file.filename)
    file.save(filepath)

    extract_metadata(filepath)
    return jsonify({"message": f"{file.filename} uploaded successfully"}), 200


@app.route('/metadata/<filename>', methods=['GET'])
def get_metadata(filename):
    filepath = os.path.join(INPUT_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404

    metadata = extract_metadata(filepath)
    if metadata:
        return jsonify(metadata)
    return jsonify({"error": "Failed to extract metadata"}), 500


@app.route('/extract/<filename>', methods=['GET'])
def extract_text(filename):
    filepath = os.path.join(INPUT_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404

    extracted_text = extract_text_from_pdf(filepath)
    if extracted_text:
        return jsonify({"text": extracted_text})
    return jsonify({"error": "Failed to extract text"}), 500


@app.route('/ocr/<filename>', methods=['GET'])
def extract_ocr_text(filename):
    filepath = os.path.join(INPUT_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404

    ocr_text = extract_text_from_scanned_pdf(filepath)
    if ocr_text:
        return jsonify({"ocr_text": ocr_text})
    return jsonify({"error": "Failed to extract OCR text"}), 500


# Run Flask App with Endpoint URLs Printed
if __name__ == '__main__':
    init_db()
    print("\n🚀 Flask API is running!\n")
    print("🔗 Upload PDF:       POST http://127.0.0.1:5000/upload")
    print("🔗 Get Metadata:     GET  http://127.0.0.1:5000/metadata/<filename>")
    print("🔗 Extract Text:     GET  http://127.0.0.1:5000/extract/<filename>")
    print("🔗 Extract OCR Text: GET  http://127.0.0.1:5000/ocr/<filename>")
    print("\n🌐 Open in Browser: http://127.0.0.1:5000\n")

    app.run(debug=True, port=5000)
