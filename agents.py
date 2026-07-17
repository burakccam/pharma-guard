import os
import json
import base64
from groq import Groq
from config import GROQ_API_KEY
from utils import safe_json_parse

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

MASTER_PROMPT = """
ROLE: PHARMA-GUARD MASTER ORCHESTRATOR
Sen Groq tabanlı (Llama 3), multimodal yeteneklere sahip ve çoklu ajan ekosistemini yöneten baş mimarsın.
Görevin; görsel veya metinsel girişi alınan bir ilacı sıfır hata toleransı ile analiz etmektir.
KURAL 1: Yazı okunmuyorsa asla tahmin etme.
KURAL 2: Tıbbi bilgileri kendi medikal bilgi dağarcığından en güncel, resmi prospektüslere dayanarak çıkar.
KURAL 3: Bu sistem tıbbi tavsiye vermez. Kullanıcıyı her zaman doktor veya eczacıya yönlendir.
MİSYON: Sonuçta çıkacak rapor bir insanın sağlık kararını etkileyebilir. Bu yüzden doğruluk hızdan önemlidir.
"""

def get_groq_response(prompt, model="llama-3.3-70b-versatile", is_json=False):
    if not client:
        return "API Hatası: Groq API Anahtarı eksik."
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Bilgi alınamadı: {e}"

def get_groq_vision_response(image_path, prompt, model="llama-3.2-11b-vision-preview"):
    if not client:
        return "API Hatası: Groq API Anahtarı eksik."
    try:
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                            },
                        },
                    ],
                }
            ],
            temperature=0.1,
        )
        return completion.choices[0].message.content
    except Exception as e:
         return f"Bilgi alınamadı: {e}"

class VisionScanner:
    @staticmethod
    def analyze_image(image_path):
        if not client:
            return {"status": "ERROR", "notes": "Groq API anahtarı bulunamadı."}
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
        response_text = get_groq_vision_response(image_path, prompt)
        result = safe_json_parse(response_text)
        if not result:
            return {"status": "ERROR", "notes": "JSON formatı çözümlenemedi veya görsel anlaşılamadı."}
        return result

class KnowledgeSpecialist:
    @staticmethod
    def fetch_drug_info(query):
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
        return get_groq_response(prompt)

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
        prompt = f"""
        {MASTER_PROMPT}
        
        Kullanıcı Bağlamı: {user_context}
        İLAÇ PROSPEKTÜS BİLGİSİ (AI'den gelen):
        {ai_knowledge}
        
        GÖREV: Kullanıcının girdiği sağlık profiline göre ilacın risklerini değerlendir. Sadece saf JSON formatında dön. (```json ... ``` markdown işaretleri olmadan doğrudan json dön):
        {{
            "side_effects": "Yan etkiler",
            "critical_warnings": "Ciddi yan etkiler ve KIRMIZI ALARM niteliğindeki riskler",
            "interactions": "Etkileşimler",
            "contraindications": "Kimler kullanamaz?",
            "pregnancy_lactation": "Hamilelik uyarısı"
        }}
        """
        response_text = get_groq_response(prompt)
        return safe_json_parse(response_text) or {}

class CorporateAnalyst:
    @staticmethod
    def analyze(ai_knowledge):
        prompt = f"Şu metinden üretici ve ruhsat sahibini çıkar. Sadece JSON dön: {{\"manufacturer\": \"\", \"license_holder\": \"\"}}.\nMetin: {ai_knowledge}"
        response_text = get_groq_response(prompt)
        return safe_json_parse(response_text) or {}

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
