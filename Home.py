import fitz  # PyMuPDF
import os

# Define the output directory
OUTPUT_DIR = "extracted_text"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def extract_text(pdf_path):
    """Extracts text from a PDF file and saves it to a .txt file."""
    try:
        if not os.path.exists(pdf_path):
            print(f"❌ File not found: {pdf_path}")
            return

        # Open the PDF
        doc = fitz.open(pdf_path)
        extracted_text = ""

        # Iterate through pages
        for page_num in range(len(doc)):
            page = doc[page_num]  # Corrected variable
            extracted_text += f"\n-- Page {page_num + 1} --\n"
            extracted_text += page.get_text("text")  # Corrected function

        # Save extracted text to a file
        output_file = os.path.join(OUTPUT_DIR, "output.txt")  # Corrected file extension
        with open(output_file, "w", encoding="utf-8") as file:
            file.write(extracted_text)

        print(f"✅ Text extracted successfully! Saved to {output_file}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")


# Run script
if __name__ == "__main__":  # Fixed __name__ check
    pdf_path = r"C:\Users\ksund\PycharmProjects\PythonProject\DBDT_Breakdown_Project\INPUT\Certificate.pdf"  # Fixed path
    extract_text(pdf_path)
