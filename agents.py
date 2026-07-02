import os
import json
import google.generativeai as genai
import PIL.Image
from config import GEMINI_API_KEY
from utils import safe_json_parse

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

MASTER_PROMPT = """
ROLE: PHARMA-GUARD MASTER ORCHESTRATOR
Sen Gemini tabanlı, multimodal yeteneklere sahip ve çoklu ajan ekosistemini yöneten baş mimarsın.
Görevin; görsel veya metinsel girişi alınan bir ilacı sıfır hata toleransı ile analiz etmektir.
KURAL 1: Yazı okunmuyorsa asla tahmin etme. Kullanıcıyı daha net, ışıklı ve düz açıdan fotoğraf çekmesi için uyar.
KURAL 2: Tıbbi bilgileri kendi medikal bilgi dağarcığından en güncel, resmi prospektüslere dayanarak çıkar.
KURAL 3: Bu sistem tıbbi tavsiye vermez. Kullanıcıyı her zaman doktor veya eczacıya yönlendir.
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
                "form": "Form (Tablet, vb.)",
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

class KnowledgeSpecialist:
    @staticmethod
    def fetch_drug_info(query):
        if not GEMINI_API_KEY:
            return "API Hatası: Gemini API Anahtarı eksik."
        try:
            model = genai.GenerativeModel('gemini-1.5-pro')
            prompt = f"""
            Lütfen uzman bir farmakolog gibi davranarak "{query}" ilacının Türkiye'deki güncel Sağlık Bakanlığı onaylı prospektüs (kullanma talimatı) bilgilerini detaylıca listele.
            
            Şu başlıkları kesinlikle içermeli:
            - Endikasyonlar (Ne için kullanılır?)
            - Etkin Madde ve Dozaj
            - Yan Etkiler
            - Kontrendikasyonlar (Kimler kullanmamalı)
            - İlaç Etkileşimleri
            - Üretici ve Ruhsat Sahibi bilgisi
            """
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Bilgi alınamadı: {e}"

class FactChecker:
    @staticmethod
    def check(vision_data, ai_knowledge, manual_drug_name):
        if not vision_data and manual_drug_name:
            if not ai_knowledge or "Bilgi alınamadı" in ai_knowledge:
                return {"status": "BLOCKED", "reason": "Yapay Zeka bu ilaç hakkında bilgi bulamadı."}
            return {"status": "OK", "reason": "Metinsel arama yapıldı ve bilgi bulundu."}
        if not vision_data or vision_data.get("status") != "OK":
            return {"status": "BLOCKED", "reason": "Görsel doğrulanamadı veya okunamadı."}
        return {"status": "OK", "reason": "Görselden okunan ilaç AI bilgisiyle analiz edildi."}

class SafetyAuditor:
    @staticmethod
    def audit(ai_knowledge, user_context):
        if not GEMINI_API_KEY:
             return {"status": "ERROR", "notes": "API Key eksik."}
        prompt = f"""
        {MASTER_PROMPT}
        
        Kullanıcı Bağlamı: {user_context}
        İLAÇ PROSPEKTÜS BİLGİSİ (AI'den gelen):
        {ai_knowledge}
        
        GÖREV: Kullanıcının girdiği sağlık profiline göre ilacın risklerini değerlendir. Sadece JSON dön:
        {{
            "side_effects": "Yan etkiler",
            "critical_warnings": "Ciddi yan etkiler ve KIRMIZI ALARM niteliğindeki riskler",
            "interactions": "Etkileşimler",
            "contraindications": "Kimler kullanamaz?",
            "pregnancy_lactation": "Hamilelik uyarısı"
        }}
        """
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(prompt)
        return safe_json_parse(response.text) or {}

class CorporateAnalyst:
    @staticmethod
    def analyze(ai_knowledge):
        if not GEMINI_API_KEY:
            return {}
        prompt = f"Şu metinden üretici ve ruhsat sahibini çıkar. JSON dön: {{\"manufacturer\": \"\", \"license_holder\": \"\"}}.\nMetin: {ai_knowledge}"
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return safe_json_parse(response.text) or {}

class ReportSynthesizer:
    @staticmethod
    def synthesize(vision_data, fact_check, safety_data, corp_data, user_context, manual_name):
        if fact_check.get("status") == "BLOCKED":
            return f"# BLOKLANDI\n\n**Sebep:** {fact_check.get('reason')}"
            
        drug_name = manual_name if manual_name else vision_data.get("brand_name", "Bilinmeyen İlaç")
        
        report = f"""# Pharma-Guard AI İlaç Denetim Raporu

> **1. Tıbbi Güvenlik Notu**
> Bu çıktı tıbbi tavsiye değildir. İlaç kullanımı, doz değişikliği veya tedavi kararı için mutlaka doktorunuza veya eczacınıza danışınız.
> Bu rapor yapay zeka tarafından sağlanan güncel farmakolojik verilere dayanmaktadır.

## 2. İlaç Kimlik Özeti
- **Ticari Ad:** {drug_name}
- **Etken Madde:** {vision_data.get('active_ingredient', 'Bilinmiyor') if vision_data else 'AI Sorgusu ile Belirlendi'}
- **Dozaj:** {vision_data.get('dosage', 'Bilinmiyor') if vision_data else '-'}

## 3. Analiz Durumu
- **Durum:** {fact_check.get('status')}
- **Detay:** {fact_check.get('reason')}

## 4. Kullanıcı Bağlamına Göre Risk Değerlendirmesi
**Kullanıcı Profili:** {user_context if user_context else 'Belirtilmedi'}
> **Kritik Uyarılar:** {safety_data.get('critical_warnings', 'Bulunmuyor.')}

## 5. Yan Etkiler
{safety_data.get('side_effects', 'Belirtilmemiş.')}

## 6. Diğer İlaçlarla Etkileşim
{safety_data.get('interactions', 'Belirtilmemiş.')}

## 7. Kimler Kullanmamalı?
{safety_data.get('contraindications', 'Belirtilmemiş.')}

## 8. Üretici / Ruhsat Sahibi Bilgileri
- **Üretici:** {corp_data.get('manufacturer', 'Bulunamadı')}
- **Ruhsat Sahibi:** {corp_data.get('license_holder', 'Bulunamadı')}

## 9. Sonuç
Yapay zeka tarafından derlenen bu analiz bilgilendirme amaçlıdır. Lütfen ilacı kullanmadan önce bir uzmana danışınız.
"""
        return report

def run_pharma_guard_analysis(image_file_path=None, manual_drug_name=None, user_context=None):
    if not image_file_path and not manual_drug_name:
         return {"status": "ERROR", "block_reason": "Görsel veya ilaç ismi sağlandı."}

    vision_result = {}
    query_term = manual_drug_name
    
    if image_file_path:
        vision_result = VisionScanner.analyze_image(image_file_path)
        if vision_result.get("status") == "OK":
            query_term = f"{vision_result.get('brand_name', '')} {vision_result.get('active_ingredient', '')}"
            
    if not query_term:
        query_term = manual_drug_name

    ai_knowledge = KnowledgeSpecialist.fetch_drug_info(query_term)
    fact_check = FactChecker.check(vision_result, ai_knowledge, manual_drug_name)
    
    safety_audit = {}
    corporate_analysis = {}
    
    if fact_check.get("status") == "OK":
         safety_audit = SafetyAuditor.audit(ai_knowledge, user_context)
         corporate_analysis = CorporateAnalyst.analyze(ai_knowledge)
         
    final_report = ReportSynthesizer.synthesize(
        vision_data=vision_result,
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
        "ai_knowledge": ai_knowledge,
        "fact_check": fact_check,
        "safety_audit": safety_audit,
        "corporate_analysis": corporate_analysis,
        "final_markdown_report": final_report
    }
