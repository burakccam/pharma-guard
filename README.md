# Pharma-Guard AI 💊
Yapay Zeka Destekli Akıllı İlaç Denetçisi

Bu proje, görüntü işleme (Gemini Vision / LLaVA), doğal dil işleme (Gemini/Llama), RAG (Retrieval-Augmented Generation) ve Çoklu Ajan Mimarisi kullanarak ilaçları denetleyen bir Streamlit uygulamasıdır. 
Kullanıcının yüklediği ilaç fotoğrafını veya girdiği ilaç adını yerel PDF prospektüsleriyle eşleştirir, FactChecker ile doğrular ve SafetyAuditor ile risk analizi yapar.

## 🚀 Teknolojiler
- **Dil:** Python 3.10+
- **Arayüz:** Streamlit
- **LLM/Vision:** Google Gemini API (Ayrıca yerel Ollama/LLaVA entegrasyonu da desteklenir)
- **RAG & Vektör Veritabanı:** LangChain, ChromaDB, HuggingFace (`all-MiniLM-L6-v2`)
- **PDF İşleme:** pypdf, reportlab

## ⚙️ Kurulum Adımları

**1. Depoyu klonlayın veya indirin:**
```bash
cd PharmaAgent_Project
```

**2. Sanal Ortam Oluşturun ve Aktif Edin:**
```bash
python -m venv venv
# Mac/Linux için:
source venv/bin/activate
# Windows için:
venv\Scripts\activate
```

**3. Gerekli Kütüphaneleri Yükleyin:**
```bash
pip install -r requirements.txt
```

**4. .env Dosyasını Oluşturun:**
`.env.example` dosyasını `.env` olarak kopyalayın ve içine kendi API anahtarlarınızı girin.
Özellikle `GEMINI_API_KEY` zorunludur.

**5. Test (Mock) Verilerini Üretin:**
Sistemin veritabanının boş kalmaması için örnek Parol ve Aspirin PDF'lerini otomatik oluşturun:
```bash
python mock_data_generator.py
```

**6. RAG Veritabanını Oluşturun:**
`data/corpus/` klasöründeki PDF'leri işleyip ChromaDB vektör uzayına kaydetmek için:
```bash
python build_rag.py
```

**7. Uygulamayı Başlatın:**
```bash
streamlit run app.py
```

## ⚠️ Güvenlik ve Etik Notu
Bu sistem **TIBBİ TAVSİYE VERMEZ**. Oluşturulan tüm raporlar bilgilendirme amaçlıdır. Nihai tedavi, dozaj değişikliği ve kullanım kararları için daima bir tıp doktoruna veya eczacıya danışılmalıdır. 

## 🧪 Test Senaryoları
Sistemin farklı ajanlarını ve davranışlarını görmek için aşağıdaki senaryoları deneyebilirsiniz:
- **Senaryo 1 (Manuel Doğru Girdi):** Arama kutusuna "Parol" yazıp analiz edin. Sistem Parol prospektüsünü RAG'dan çekecek ve detaylı analiz sunacaktır.
- **Senaryo 2 (Veri Uyuşmazlığı / Risk):** Yaş olarak "70" girip Kronik hastalık olarak "Mide ülseri" yazın. İlaç olarak "Aspirin" aratın. SafetyAuditor ajanının KIRMIZI ALARM verdiğini görebilirsiniz.
- **Senaryo 3 (Görsel Test):** Bilgisayarınızdan rastgele bir ilaç kutusu resmi yükleyin. VisionScanner bunu analiz edecek ve yerel PDF'lerle karşılaştıracaktır. Eğer yerel veri tabanında (mock datalar haricinde) o ilacın PDF'i yoksa FactChecker işlemi bloklayacaktır.
