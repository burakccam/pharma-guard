import streamlit as st
import os
from config import GEMINI_API_KEY
from agents import run_pharma_guard_analysis
from utils import save_uploaded_image, create_pdf_report
from build_rag import build_rag

st.set_page_config(
    page_title="Pharma-Guard AI",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("💊 Pharma-Guard AI")
st.subheader("Yapay Zeka Destekli Akıllı İlaç Denetçisi")

st.markdown("""
> **GÜVENLİK UYARISI:** Bu sistem tıbbi tavsiye vermez. Yalnızca PDF prospektüs kaynaklı bilgi sunar. 
> Emin olunmayan durumda rapor bloklanır. İlaç kullanımı için **mutlaka doktorunuza veya eczacınıza danışınız.**
""")

# Sidebar
with st.sidebar:
    st.header("⚙️ Sistem Durumu")
    if GEMINI_API_KEY:
        st.success("✅ Gemini API: Aktif")
    else:
        st.error("❌ Gemini API: Bulunamadı (Lütfen .env dosyanızı kontrol edin)")
        
    st.header("📚 RAG Veritabanı")
    st.info("İlk kurulumda veya yeni PDF eklediğinizde veritabanını güncelleyin.")
    if st.button("🔄 RAG Veritabanını Güncelle"):
        with st.spinner("PDF'ler işleniyor ve ChromaDB güncelleniyor..."):
            success = build_rag()
            if success:
                st.success("✅ Veritabanı başarıyla güncellendi!")
            else:
                st.warning("⚠️ PDF bulunamadı veya işlenemedi.")

# Ana Ekran - Formlar
col1, col2 = st.columns(2)

with col1:
    st.header("📸 İlaç Bilgisi")
    upload_file = st.file_uploader("İlaç kutusu veya prospektüs fotoğrafı yükle", type=["png", "jpg", "jpeg"])
    manual_drug = st.text_input("Veya manuel ilaç adı yazın (Örn: Parol, Aspirin)")

with col2:
    st.header("👤 Kullanıcı Sağlık Bağlamı")
    user_age = st.number_input("Yaşınız", min_value=0, max_value=120, value=30)
    is_pregnant = st.checkbox("Hamilelik / Emzirme Durumu")
    chronic_diseases = st.text_area("Kronik Hastalıklar (Varsa)", placeholder="Örn: Hipertansiyon, Diyabet")
    allergies = st.text_area("Alerjiler (Varsa)", placeholder="Örn: Penisilin alerjisi")
    other_drugs = st.text_area("Kullanılan Diğer İlaçlar", placeholder="Örn: Kan sulandırıcı, vitamin")

if st.button("🔍 Analiz Et", type="primary", use_container_width=True):
    if not upload_file and not manual_drug:
        st.error("Lütfen bir görsel yükleyin veya ilaç adı girin.")
    elif not GEMINI_API_KEY:
        st.error("API Key eksik. Lütfen yapılandırın.")
    else:
        # Kullanıcı bağlamını metinleştir
        context_parts = [f"Yaş: {user_age}"]
        if is_pregnant:
            context_parts.append("Durum: Hamile veya emziriyor.")
        if chronic_diseases:
            context_parts.append(f"Kronik Hastalıklar: {chronic_diseases}")
        if allergies:
            context_parts.append(f"Alerjiler: {allergies}")
        if other_drugs:
             context_parts.append(f"Diğer İlaçlar: {other_drugs}")
             
        user_context = " | ".join(context_parts)
        
        image_path = None
        if upload_file:
            image_path = save_uploaded_image(upload_file)
            st.image(image_path, caption="Yüklenen Görsel", width=300)
            
        with st.spinner("🤖 Pharma-Guard Ajanları devrede... Lütfen bekleyin."):
            results = run_pharma_guard_analysis(
                image_file_path=image_path,
                manual_drug_name=manual_drug,
                user_context=user_context
            )
            
        if results["status"] == "BLOCKED" or results["status"] == "ERROR":
            st.error(f"🚨 RAPOR BLOKLANDI VEYA HATA OLUŞTU")
            st.warning(f"Sebep: {results.get('block_reason') or results.get('vision_result', {}).get('notes')}")
        else:
            st.success("✅ Analiz Tamamlandı!")
            
            st.markdown("---")
            st.markdown(results["final_markdown_report"])
            
            # PDF Üret ve İndir
            pdf_name = f"report_{manual_drug or 'ilac'}.pdf".replace(" ", "_")
            pdf_path = create_pdf_report(results["final_markdown_report"], pdf_name)
            
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="📄 PDF Raporu İndir",
                    data=f,
                    file_name=os.path.basename(pdf_path),
                    mime="application/pdf"
                )
