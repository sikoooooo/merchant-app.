import streamlit as st
import json
import re
import uuid
import google.generativeai as genai
from supabase import create_client, Client

# --- 1. إعدادات الصفحة الاحترافية ---
st.set_page_config(
    page_title="المحاسب الذكي - Pro",
    page_icon="💎",
    layout="wide"
)

# --- 2. التصميم الفاخر (UI/UX) ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');
html, body, [class*="css"] {
    font-family: 'Cairo', sans-serif;
    direction: rtl;
    text-align: right;
}
.stApp {
    background: linear-gradient(135deg, #090d16 0%, #111827 100%);
    color: #f3f4f6;
}
.hero-header {
    background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
    padding: 30px;
    border-radius: 20px;
    color: white;
    text-align: center;
    margin-bottom: 25px;
    box-shadow: 0 20px 25px -5px rgba(59, 130, 246, 0.2);
}
.stTextInput input {
    background-color: #0f172a !important;
    color: #ffffff !important;
    border-radius: 12px !important;
    border: 1px solid #475569 !important;
    padding: 12px !important;
}
.stButton button {
    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
    color: white !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    border: none !important;
    padding: 12px 28px !important;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

# --- 3. بيانات الاتصال ومفاتيح الـ API ---
SUPABASE_URL = "https://nqindgywshroejrcxtky.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5xaW5kZ3l3c2hyb2VqcmN4dGt5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NjgxNTExMCwiZXhwIjoyMTAyMzkxMTEwfQ.g-jpUzajE_OxGNNjF2QCFZINWjRfGSPCSHR2rtOtUTE"

API_KEYS = [
    "AQ.Ab8RN6KsmZlOVBitqBHl9MTKvhDTCrOkLckSZOLq5opLxEM97g",
    "AQ.Ab8RN6IOOQs421k9-f9CtpYl-b7mKWe1ID2e-VODE8WbGDLy0g",
    "AQ.Ab8RN6LDnxPObId4PxP_7RWvXtPSekj6ftHZ6AIwiVKyVQso5Q",
    "AQ.Ab8RN6IXSRGUETheaRkxa2JuolYCfGIL-888kwz8J9-OfWZ4Gw"
]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
USER_ID = "855633fe-a3a8-400d-a9ae-9fe439e658bd"

def search_item_price(query_text: str):
    try:
        response = supabase.table("transactions").select("*").order("created_at", desc=True).limit(50).execute()
        rows = response.data
        query_words = [w for w in query_text.split() if len(w) > 2 and w not in ["بكام", "سعر", "عندنا", "كام", "في", "ال"]]
        for row in rows:
            item_desc = row.get("item_or_person", "")
            raw = row.get("raw_text", "")
            if any(word in item_desc or word in raw for word in query_words):
                return row
        return None
    except Exception:
        return None

def process_command_ai(text: str):
    query_keywords = ["بكام", "سعر", "عندنا", "كام", "فين", "رصيد", "إيه", "ايه"]
    is_query = any(k in text for k in query_keywords) and not any(w in text for w in ["اشترينا", "بعنا", "دفعنا", "قبضنا"])
    
    if is_query:
        return {"type": "QUERY", "query_text": text}

    data = None
    income_keywords = ["بيع", "بعت", "بعنا", "باع", "مبيعات", "قبضت", "قبضنا", "حصلنا", "توريد"]
    is_sale = any(w in text for w in income_keywords)
    
    for key in API_KEYS:
        try:
            genai.configure(api_key=key)
            system_instruction = """
            أنت محاسب ذكي وخبير في تجارة الجملة والمفرد باللهجة العامية المصرية.
            قواعد التصنيف الدقيقة:
            1. type: INCOME لو المعاملة بيع او قبض، EXPENSE لو شراء او مصاريف.
            2. category: حدد حصريا التصنيف من: مبيعات، مشتريات وبضاعة، أصول ثابتة، مصاريف تشغيلية، مصاريف دعاية وإعلان، مصاريف إدارية ورواتب.
            3. item_or_person: اسم الصنف او البيان.
            4. quantity: الكمية الرقمية أو 1.
            5. amount: المبلغ الاجمالي النهائي للعملية.
            أجب بصيغة JSON نقي فقط بدون أي نص خارجي وبدون علامات الـ markdown.
            """
            model = genai.GenerativeModel(model_name='gemini-1.5-pro', system_instruction=system_instruction)
            res = model.generate_content(f"حلل المعاملة بدقة: '{text}'")
            raw_text = res.text.strip()
            
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0].strip()
                
            data = json.loads(raw_text)
            if data and "amount" in data:
                if is_sale:
                    data["type"] = "INCOME"
                    data["category"] = "مبيعات"
                return data
        except Exception:
            continue
            
    numbers = [int(n) for n in re.findall(r'\d+', text)]
    is_total_format = any(w in text for w in ["بـ", "ب ", "إجمالي"]) and len(numbers) >= 2
    
    if len(numbers) >= 2 and not is_total_format and ("الكرتونة" in text or "القطعة" in text):
        amount = numbers[0] * numbers[1]
        qty = numbers[0]
    elif len(numbers) >= 1:
        amount = numbers[-1]
        qty = numbers[0] if len(numbers) >= 2 and not is_total_format else 1
    else:
        amount = 0
        qty = 1
        
    is_asset = any(w in text for w in ["عربية", "سيارة", "ثلاجة", "معدات"])
    
    return {
        "type": "INCOME" if is_sale else "EXPENSE",
        "category": "مبيعات" if is_sale else ("أصول ثابتة" if is_asset else "مشتريات وبضاعة"),
        "item_or_person": text,
        "quantity": qty,
        "amount": amount
    }

def post_journal_entry(tx_type, category, amount, description):
    entry_id = str(uuid.uuid4())
    id_cash = 1
    
    if tx_type == "INCOME" or category == "مبيعات":
        id_target = 4
        journal_data = [
            {"entry_id": entry_id, "account_id": id_cash, "debit": amount, "credit": 0.00, "description": description},
            {"entry_id": entry_id, "account_id": id_target, "debit": 0.00, "credit": amount, "description": description}
        ]
    else:
        desc_lower = description.lower()
        if "دعاية" in desc_lower or "اعلان" in desc_lower or "إعلان" in desc_lower:
            id_target = 6
        elif category == "أصول ثابتة" or "عربية" in desc_lower or "سيارة" in desc_lower:
            id_target = 7
        else:
            id_target = 5

        journal_data = [
            {"entry_id": entry_id, "account_id": id_target, "debit": amount, "credit": 0.00, "description": description},
            {"entry_id": entry_id, "account_id": id_cash, "debit": 0.00, "credit": amount, "description": description}
        ]
    supabase.table("journal_entries").insert(journal_data).execute()
    return True

# --- 4. واجهة الاستخدام ---
st.markdown("""
<div class="hero-header">
    <h1>💎 المحاسب الذكي - النظام المطور</h1>
    <p>تحليل فوري للمعاملات التجارية، استعلامات الأسعار، وترحيل آلي للدفاتر</p>
</div>
""", unsafe_allow_html=True)

voice_input = st.text_input("أدخل المعاملة أو الاستعلام:", placeholder="مثال: كرتونة البيض بكام؟ أو بعنا 10 كراتين بـ 120", label_visibility="collapsed")

if st.button("🚀 تنفيذ الطلب"):
    if voice_input:
        with st.spinner("✨ جاري معالجة الطلب..."):
            data = process_command_ai(voice_input)
            
            if data.get("type") == "QUERY":
                found_item = search_item_price(voice_input)
                if found_item:
                    st.markdown(f"""
                    <div style="background: rgba(15, 23, 42, 0.95); border: 2px solid #3b82f6; padding: 16px; border-radius: 14px; margin-top: 15px;">
                        <p style="margin: 0; color: #f3f4f6; font-size: 16px; font-weight: bold; text-align: center;">
                            🔍 وجدنا آخر حركة لـ ({found_item.get('item_or_person')}): الإجمالي ({found_item.get('amount')} ج.م) | الكمية: ({found_item.get('quantity')})
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("⚠️ عذراً، لم أجد تسجيلاً سابقاً لهذا الصنف في قاعدة البيانات.")
            else:
                amt = data.get("amount", 0)
                tx_type = data.get("type", "EXPENSE")
                tx_category = data.get("category", "مصاريف تشغيلية")
                item = data.get("item_or_person", voice_input)
                qty = data.get("quantity", 1)
                
                if amt == 0:
                    st.error("⚠️ عذراً، لم أستطع تحديد المبلغ. من فضلك أدخل المبلغ أو السعر بوضوح.")
                else:
                    supabase.table("transactions").insert({
                        "type": tx_type,
                        "item_or_person": item,
                        "quantity": qty,
                        "amount": amt,
                        "raw_text": voice_input,
                        "created_by_user_id": USER_ID,
                        "category": tx_category
                    }).execute()
                    
                    post_journal_entry(tx_type, tx_category, amt, voice_input)
                    
                    border_color = "#10b981" if tx_type == "INCOME" else "#f59e0b"
                    st.markdown(f"""
                    <div style="background: rgba(15, 23, 42, 0.95); border: 2px solid {border_color}; padding: 16px; border-radius: 14px; margin-top: 15px;">
                        <p style="margin: 0; color: #f3f4f6; font-size: 16px; font-weight: bold; text-align: center;">
                            ✅ تم بنجاح تسجيل ({tx_category}) | البيان: ({item}) | الكمية: ({qty}) | الإجمالي: ({amt} ج.م)!
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.error("الرجاء كتابة العملية أو الاستعلام أولاً.")
