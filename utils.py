import os
import re
import json
import base64
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from config import REPORTS_DIR

def save_uploaded_image(uploaded_file):
    """Streamlit UploadedFile objesini gecici olarak kaydeder ve yolunu doner."""
    os.makedirs("temp", exist_ok=True)
    file_path = os.path.join("temp", uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def safe_json_parse(text):
    """Metin icindeki olasi markdown bloklarini temizleyip JSON parse eder."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    try:
        return json.loads(text.strip())
    except Exception as e:
        print(f"JSON Parse Error: {e}")
        return None

def extract_dosage_number(dosage_str):
    """'500 mg', '500mg', '100' gibi string'lerden sadece sayiyi ceker."""
    if not dosage_str:
        return None
    match = re.search(r'(\d+)', str(dosage_str))
    return float(match.group(1)) if match else None

def compare_dosage(dos1, dos2):
    """Iki dozajin sayisal olarak ayni olup olmadigini kontrol eder."""
    num1 = extract_dosage_number(dos1)
    num2 = extract_dosage_number(dos2)
    if num1 is not None and num2 is not None:
        return num1 == num2
    return False

def create_pdf_report(markdown_text, report_name):
    """Basit bir PDF raporu uretir."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    pdf_path = os.path.join(REPORTS_DIR, report_name)
    c = canvas.Canvas(pdf_path, pagesize=letter)
    
    # Standart font ile (Turkce karakter destegi icin replace islemi eklendi)
    c.setFont("Helvetica", 10)
    
    y = 750
    lines = markdown_text.split('\n')
    for line in lines:
        while len(line) > 0:
            part = line[:90]
            line = line[90:]
            
            # Temel TR karakter donusumu
            part = part.replace('ı', 'i').replace('İ', 'I').replace('ğ', 'g').replace('Ğ', 'G')
            part = part.replace('ü', 'u').replace('Ü', 'U').replace('ş', 's').replace('Ş', 'S')
            part = part.replace('ö', 'o').replace('Ö', 'O').replace('ç', 'c').replace('Ç', 'C')
            
            c.drawString(50, y, part)
            y -= 15
            if y < 50:
                c.showPage()
                c.setFont("Helvetica", 10)
                y = 750
                
    c.save()
    return pdf_path
