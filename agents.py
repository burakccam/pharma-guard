import os
import json
import google.generativeai as genai
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import PIL.Image
from config import GEMINI_API_KEY, CHROMA_DB_DIR
from utils import safe_json_parse, compare_dosage

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

MASTER_PROMPT = """
ROLE: PHARMA-GUARD MASTER ORCHESTRATOR
Sen Gemini tabanlı, multimodal yeteneklere sahip ve çoklu ajan ekosistemini yöneten baş mimarsın.
Görevin; görsel veya metinsel girişi alınan bir ilacı sıfır hata toleransı ile analiz etmektir.
KURAL 1: Yazı okunmuyorsa asla tahmin etme. Kullanıcıyı daha net, ışıklı ve düz açıdan fotoğraf çekmesi için uyar.
KURAL 2: Tıbbi bilgi kaynağın yalnızca yerel PDF prospektüsleridir. İnternet yorumlarını vb. kullanma.
KURAL 3: Görselden çıkarılan ilaç bilgisi ile prospektüs bilgisi uyuşmuyorsa raporu blokla.
KURAL 4: Etken madde, dozaj veya form bilgisinde uyuşmazlık varsa 'VERİ UYUŞMAZLIĞI' alarmı ver.
KURAL 5: Her bilgi parçası için güven puanı üret. Ortalama güven 8'in altındaysa rapora 'DİKKAT: Bilgiler tam doğrulanamadı' uyarısı ekle.
KURAL 6: Bu sistem tıbbi tavsiye vermez. Kullanıcıyı her zaman doktor veya eczacıya yönlendir.
KURAL 7: Kaynaksız bilgi üretme. Kaynakta yoksa 'Kaynakta bulunamadı' de.
MİSYON: Sonuçta çıkacak rapor bir insanın sağlık kararını etkileyebilir. Bu yüzden doğruluk hızdan önemlidir.
"""

class VisionScanner:
    @staticmethod
    def analyze_image(image_path):
        if not GEMINI_API_KEY:
            return {"status": "ERROR", "notes": "Gemini API anahtarı bulunamadı."}
            
        try:
            img = PIL.Image.open(image_path)
            model = genai.GenerativeModel('gemini-1.5-pro')
            
            prompt = """
            Aşağıdaki ilaç kutusu veya prospektüs görselini incele.
            Kesin bir JSON formatında şu bilgileri dön. Eğer okunamıyorsa boş bırak ve status'u NEED_BETTER_IMAGE yap.
            Şema:
            {
                "status": "OK | NEED_BETTER_IMAGE | ERROR",
                "brand_name": "İlaç Adı",
                "active_ingredient": "Etken Madde",
                "dosage": "Dozaj (örn 500 mg)",
                "form": "Form (Tablet, Kapsül, Şurup vb.)",
                "barcode": "Varsa barkod",
                "visible_text": ["Kutudaki diğer okunan yazılar"],
                "confidence": 0-10 arası güven puanı,
                "notes": "Ek notlar"
            }
            """
            response = model.generate_content([prompt, img])
            result = safe_json_parse(response.text)
            if not result:
                return {"status": "ERROR", "notes": "JSON formatı çözümlenemedi."}
            return result
        except Exception as e:
            return {"status": "ERROR", "notes": str(e)}

class RAGSpecialist:
    @staticmethod
    def search(query):
        try:
            embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            vectorstore = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embeddings)
            docs = vectorstore.similarity_search(query, k=5)
            
            results = []
            for doc in docs:
                results.append({
                    "text": doc.page_content,
                    "metadata": doc.metadata
                })
            return results
        except Exception as e:
            print(f"RAG Error: {e}")
            return []

class FactChecker:
    @staticmethod
    def check(vision_data, rag_results, manual_drug_name):
        if not vision_data and manual_drug_name:
            if not rag_results:
                return {"status": "BLOCKED", "reason": "Veritabanında ilgili prospektüs bulunamadı."}
            return {"status": "OK", "reason": "Sadece metinsel arama yapıldı."}
            
        if not vision_data or vision_data.get("status") != "OK":
            return {"status": "BLOCKED", "reason": "Görsel doğrulanamadı veya okunamadı."}
            
        if not rag_results:
            return {"status": "BLOCKED", "reason": "RAG veritabanında bu ilaca ait kaynak bulunamadı."}
            
        return {"status": "OK", "reason": "Kontrol sağlandı."}

class SafetyAuditor:
    @staticmethod
    def audit(rag_results, user_context):
        if not GEMINI_API_KEY:
             return {"status": "ERROR", "notes": "API Key eksik."}
             
        combined_text = "\\n\\n".join([f"Kaynak ({r['metadata'].get('source_file')} S.{r['metadata'].get('page_number')}): {r['text']}" for r in rag_results])
        
        prompt = f"""
        {MASTER_PROMPT}
        
        Kullanıcı Bağlamı: {user_context}
        
        PROSPEKTÜS METİNLERİ:
        {combined_text}
        
        GÖREV: Sadece prospektüs metinlerine dayanarak şu bilgileri JSON olarak dön:
        {{
            "side_effects": "Yan etkiler özeti",
            "critical_warnings": "Ciddi yan etkiler ve KIRMIZI ALARM niteliğinde uyarılar (Özellikle Kullanıcı bağlamına göre risk varsa belirt)",
            "interactions": "Diğer ilaçlarla etkileşimi",
            "contraindications": "Kimler kullanamaz?",
            "pregnancy_lactation": "Hamilelik/Emzirme uyarısı",
            "driving_machinery": "Araç makine kullanımı",
            "overdose": "Doz aşımı",
            "storage": "Saklama koşulları"
        }}
        Asla prospektüste olmayan bilgiyi ekleme. Yoksa 'Kaynakta bulunamadı' de.
        """
        
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(prompt)
        return safe_json_parse(response.text) or {}

class CorporateAnalyst:
    @staticmethod
    def analyze(rag_results):
        if not GEMINI_API_KEY:
            return {}
            
        combined_text = "\\n\\n".join([r['text'] for r in rag_results])
        prompt = f"Şu metinden üretici, ruhsat sahibi ve üretim yerini çıkar. Sadece JSON dön: {{\"manufacturer\": \"\", \"license_holder\": \"\", \"origin\": \"\"}}.\\nMetin: {combined_text}"
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return safe_json_parse(response.text) or {}

class ReportSynthesizer:
    @staticmethod
    def synthesize(vision_data, rag_results, fact_check, safety_data, corp_data, user_context, manual_name):
        if fact_check.get("status") == "BLOCKED":
            return f"# BLOKLANDI\\n\\n**Sebep:** {fact_check.get('reason')}\\n\\nLütfen net bir fotoğraf yükleyin veya veritabanını güncelleyin."
            
        drug_name = manual_name if manual_name else vision_data.get("brand_name", "Bilinmeyen İlaç")
        
        sources = "\\n".join([f"- {r['metadata'].get('source_file')} (Sayfa {r['metadata'].get('page_number')})" for r in rag_results])
        
        report = f"""# Pharma-Guard AI İlaç Denetim Raporu

> **1. Tıbbi Güvenlik Notu**
> Bu çıktı tıbbi tavsiye değildir. İlaç kullanımı, doz değişikliği veya tedavi kararı için mutlaka doktorunuza veya eczacınıza danışınız.
> Bu sistem yalnızca PDF prospektüs kaynaklı bilgi sunar.

## 2. İlaç Kimlik Özeti
- **Ticari Ad:** {drug_name}
- **Etken Madde:** {vision_data.get('active_ingredient', 'Bilinmiyor') if vision_data else 'Sadece Metin Araması'}
- **Dozaj:** {vision_data.get('dosage', 'Bilinmiyor') if vision_data else '-'}
- **Form:** {vision_data.get('form', 'Bilinmiyor') if vision_data else '-'}
- **Güven Puanı:** {vision_data.get('confidence', 'N/A') if vision_data else 'N/A'}/10

## 3. Kaynak Eşleşme Durumu
- **Durum:** {fact_check.get('status')}
- **Detay:** {fact_check.get('reason')}

## 4. Kritik Uyarılar
{safety_data.get('critical_warnings', 'Kaynakta bulunamadı.')}

## 5. Yan Etkiler
{safety_data.get('side_effects', 'Kaynakta bulunamadı.')}

## 6. Diğer İlaçlarla Etkileşim
{safety_data.get('interactions', 'Kaynakta bulunamadı.')}

## 7. Kimler Kullanmamalı?
{safety_data.get('contraindications', 'Kaynakta bulunamadı.')}

## 8. Kullanıcı Bağlamına Göre Risk Değerlendirmesi
**Kullanıcı Profili:** {user_context if user_context else 'Belirtilmedi'}
_Dikkat: Kullanıcı profiline göre olası riskler yukarıdaki kritik uyarılar bölümünde belirtilmiştir. Kesin değerlendirme için hekime başvurunuz._

## 9. Üretici / Ruhsat Sahibi Bilgileri
- **Üretici:** {corp_data.get('manufacturer', 'Bulunamadı')}
- **Ruhsat Sahibi:** {corp_data.get('license_holder', 'Bulunamadı')}

## 10. RAG Kaynakça
{sources if sources else "Kaynak bulunamadı."}

## 11. Sonuç
Prospektüste belirtilen bilgiye göre yukarıdaki analiz oluşturulmuştur. Bu durum doktor/eczacı değerlendirmesi gerektirir. Lütfen ilacı kullanmadan önce bir uzmana danışınız.
"""
        return report

def run_pharma_guard_analysis(image_file_path=None, manual_drug_name=None, user_context=None):
    if not image_file_path and not manual_drug_name:
         return {"status": "ERROR", "block_reason": "Ne görsel ne de ilaç ismi sağlandı."}

    vision_result = {}
    query_term = manual_drug_name
    
    if image_file_path:
        vision_result = VisionScanner.analyze_image(image_file_path)
        if vision_result.get("status") == "OK":
            query_term = f"{vision_result.get('brand_name', '')} {vision_result.get('active_ingredient', '')}"
            
    if not query_term:
        query_term = manual_drug_name

    rag_results = RAGSpecialist.search(query_term)
    
    fact_check = FactChecker.check(vision_result, rag_results, manual_drug_name)
    
    safety_audit = {}
    corporate_analysis = {}
    
    if fact_check.get("status") == "OK":
         safety_audit = SafetyAuditor.audit(rag_results, user_context)
         corporate_analysis = CorporateAnalyst.analyze(rag_results)
         
    final_report = ReportSynthesizer.synthesize(
        vision_data=vision_result,
        rag_results=rag_results,
        fact_check=fact_check,
        safety_data=safety_audit,
        corp_data=corporate_analysis,
        user_context=user_context,
        manual_name=manual_drug_name
    )
    
    return {
        "status": fact_check.get("status"),
        "block_reason": fact_check.get("reason") if fact_check.get("status") == "BLOCKED" else "",
        "vision_result": vision_result,
        "rag_results": rag_results,
        "fact_check": fact_check,
        "safety_audit": safety_audit,
        "corporate_analysis": corporate_analysis,
        "final_markdown_report": final_report
    }
