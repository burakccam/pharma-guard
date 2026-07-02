import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from config import CORPUS_DIR

def create_mock_pdf(filename, title, content_lines):
    os.makedirs(CORPUS_DIR, exist_ok=True)
    filepath = os.path.join(CORPUS_DIR, filename)
    c = canvas.Canvas(filepath, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, title)
    
    c.setFont("Helvetica", 12)
    y = 720
    for line in content_lines:
        c.drawString(50, y, line)
        y -= 20
        if y < 50:
            c.showPage()
            c.setFont("Helvetica", 12)
            y = 750
            
    c.save()
    print(f"Mock PDF oluşturuldu: {filepath}")

def generate_mock_data():
    parol_content = [
        "1. TIBBI GUVENLIK NOTU",
        "Bu ilac (Parol 500 mg Tablet) sadece doktor tavsiyesi ile kullanilmalidir.",
        "Etken Madde: Parasetamol (500mg)",
        "Farmasotik Form: Tablet",
        "Uretici: Atabay Kimya San. ve Tic. A.S.",
        "",
        "2. KULLANIM AMACI",
        "Hafif ve orta siddetli agrilar, ates dusurucu olarak kullanilir.",
        "",
        "3. YAN ETKILER",
        "Seyrek: Deri dokuntusu, alerjik reaksiyonlar.",
        "Ciddi yan etkiler: Karaciger hasari (asiri dozda).",
        "",
        "4. KIMLER KULLANMAMALI?",
        "Karaciger veya bobrek yetmezligi olanlar kullanmamalidir.",
        "Parasetamole karsi alerjisi olanlar kullanmamalidir.",
        "Hamilelik ve emzirme doneminde doktor kontrolunde kullanilabilir.",
        "",
        "5. DIGER ILACLARLA ETKILEŞIM",
        "Alkol ile birlikte alinmamalidir (karaciger toksisitesi riski).",
        "Bazi kan sulandirici ilaclarin etkisini artirabilir."
    ]
    
    aspirin_content = [
        "1. TIBBI GUVENLIK NOTU",
        "Aspirin 100 mg Enterik Kapli Tablet.",
        "Etken Madde: Asetilsalisilik asit (100mg)",
        "Farmasotik Form: Enterik Kapli Tablet",
        "Uretici: Bayer Turk Kimya San. Ltd. Sti.",
        "",
        "2. KULLANIM AMACI",
        "Kalp krizini onlemek, kan pihtilasmasini engellemek amaciyla kullanilir.",
        "",
        "3. YAN ETKILER",
        "Mide yanmasi, mide kanamasi riski, alerjik reaksiyonlar.",
        "",
        "4. KIMLER KULLANMAMALI?",
        "Mide ulseri olanlar KESINLIKLE KULLANMAMALIDIR.",
        "16 yasindan kucuk cocuklarda Reye Sendromu riski nedeniyle kullanilmamalidir.",
        "Hamileligin son 3 ayinda kullanilmamalidir.",
        "",
        "5. DIGER ILACLARLA ETKILEŞIM",
        "Diger kan sulandiricilarla (or: warfarin) birlikte alinmasi kanama riskini artirir."
    ]

    create_mock_pdf("mock_parol.pdf", "PAROL 500 mg TABLET KULLANMA TALIMATI", parol_content)
    create_mock_pdf("mock_aspirin.pdf", "ASPIRIN 100 mg TABLET KULLANMA TALIMATI", aspirin_content)

if __name__ == "__main__":
    generate_mock_data()
