import streamlit as st
import json
import re
import uuid
import google.generativeai as genai
from supabase import create_client, Client

# --- 1. إعدادات الصفحة الاحترافية ---
st.set_page_config(
    page_title="المحاسب الذكي - Multi-Branch Pro",
    page_icon="🏢",
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
    background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
    padding: 25px;
    border-radius: 20px;
    color: white;
    text-align: center;
    margin-bottom: 20px;
    box-shadow: 0 20px 25px -5px rgba(30, 58, 138, 0.3);
    border: 1px solid #3b82f6;
}
.stTextInput input, .stSelectbox select {
    background-color: #0f172a !important;
    color: #ffffff !important;
    border-radius: 12px !important;
    border: 1px solid #475569 !important;
    padding: 10px !important;
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

def search_item_price(query_text: str, branch: str):
    try:
        response = supabase.table("transactions").select("*").eq("branch", branch).order("created_at", desc=True).limit(50).execute()
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

    income_keywords = ["بيع", "بعت", "بعنا", "باع", "مبيعات", "قبضت", "قبضنا", "حصلنا", "توريد"]
    is_sale = any(w in text for w in income_keywords)
    
    for key in API_KEYS:
        try:
            genai.configure(api_key=key)
            system_instruction = """
            أنت محاسب ذكي وخبير في تجارة الجملة والمفرد باللهجة العامية المصرية.
            قواعد التصنيف الدقيقة:
            1. type: INCOME لو المعاملة بيع أو قبض، EXPENSE لو شراء أو مصاريف.
            2. category: حدد حصريا التصنيف من: مبيعات، مشتريات وبضاعة، أصول ثابتة، مصاريف تشغيلية، مصاريف دعاية وإعلان، مصاريف إدارية ورواتب.
            3. item_or_person: اسم الصنف أو البيان.
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

# --- 4. تقسيم التطبيق لشاشات (الإدارة العليا Vs شاشة الموظفين) ---
st.markdown("""
<div class="hero-header">
    <h1>💎 المحاسب الذكي - النظام الموحد للفروع</h1>
    <p>إدارة الحسابات الشاملة والمبيعات للفروع المتعددة</p>
</div>
""", unsafe_allow_html=True)

app_mode = st.sidebar.radio("اختر لوحة التحكم:", ["👑 لوحة تحكم الإدارة (صاحب الشركة)", "👤 بوابة تسجيل الموظفين (الكاشير / المبيعات)"])

if app_mode == "👑 لوحة تحكم الإدارة (صاحب الشركة)":
    st.subheader("🛠️ إعدادات الإدارة العليا ومتابعة الفروع")
    
    col1, col2 = st.columns(2)
    with col1:
        selected_branch = st.selectbox("📍 اختر الفرع للمتابعة:", ["الفرع الرئيسي (القاهرة)", "فرع الإسكندرية"])
    with col2:
        selected_employee = st.selectbox("👤 المشرف / المعتمد:", ["أحمد (مدير الفرع)", "إدارة عامة"])

    st.markdown("---")
    voice_input = st.text_input("✍️ أدخل معاملة إدارية أو استعلام عام:", placeholder="مثال: كرتونة البيض بكام؟ أو شراء أصل بـ 50000", key="admin_input")

    if st.button("🚀 تنفيذ الطلب (إدارة)", key="admin_btn"):
        if voice_input:
            with st.spinner("✨ جاري معالجة الطلب..."):
                data = process_command_ai(voice_input)
                
                if data.get("type") == "QUERY":
                    found_item = search_item_price(voice_input, selected_branch)
                    if found_item:
                        st.markdown(f"""
                        <div style="background: rgba(15, 23, 42, 0.95); border: 2px solid #3b82f6; padding: 16px; border-radius: 14px; margin-top: 15px;">
                            <p style="margin: 0; color: #f3f4f6; font-size: 16px; font-weight: bold; text-align: center;">
                                🔍 ({selected_branch}) - آخر حركة لـ ({found_item.get('item_or_person')}): الإجمالي ({found_item.get('amount')} ج.م)
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.warning(f"⚠️ عذراً، لم أجد تسجيلاً لهذا الصنف في {selected_branch}.")
                else:
                    amt = data.get("amount", 0)
                    tx_type = data.get("type", "EXPENSE")
                    tx_category = data.get("category", "مصاريف تشغيلية")
                    item = data.get("item_or_person", voice_input)
                    qty = data.get("quantity", 1)
                    
                    if amt == 0:
                        st.error("⚠️ عذراً، لم أستطع تحديد المبلغ.")
                    else:
                        supabase.table("transactions").insert({
                            "type": tx_type,
                            "item_or_person": item,
                            "quantity": qty,
                            "amount": amt,
                            "raw_text": voice_input,
                            "created_by_user_id": USER_ID,
                            "category": tx_category,
                            "branch": selected_branch,
                            "employee": selected_employee
                        }).execute()
                        
                        post_journal_entry(tx_type, tx_category, amt, voice_input)
                        st.success(f"✅ تم التسجيل بنجاح في {selected_branch} بقيمة {amt} ج.م")

else:
    st.subheader("👤 شاشة تسجيل الموظفين (المبيعات وحركة اليومية)")
    
    col1, col2 = st.columns(2)
    with col1:
        emp_branch = st.selectbox("📍 فرعك الحالي:", ["الفرع الرئيسي (القاهرة)", "فرع الإسكندرية"], key="emp_b")
    with col2:
        emp_name = st.selectbox("👤 اسمك كـ موظف:", ["محمود (مبيعات القاهرة)", "إسلام (مخازن القاهرة)", "خالد (مبيعات الإسكندرية)"], key="emp_n")

    st.markdown("---")
    emp_input = st.text_input("✍️ سجل عملية البيع أو اسأل عن سعر صنف:", placeholder="مثال: بعنا 5 كراتين بـ 600 أو كرتونة البيض بكام؟", key="emp_input")

    if st.button("🚀 تسجيل البيعة / الاستعلام", key="emp_btn"):
        if emp_input:
            with st.spinner("✨ جاري تسجيل العملية لفرعك..."):
                data = process_command_ai(emp_input)
                
                if data.get("type") == "QUERY":
                    found_item = search_item_price(emp_input, emp_branch)
                    if found_item:
                        st.markdown(f"""
                        <div style="background: rgba(15, 23, 42, 0.95); border: 2px solid #10b981; padding: 16px; border-radius: 14px; margin-top: 15px;">
                            <p style="margin: 0; color: #f3f4f6; font-size: 16px; font-weight: bold; text-align: center;">
                                🔍 السعر في فرعك ({emp_branch}): الصنف ({found_item.get('item_or_person')}) | الإجمالي: ({found_item.get('amount')} ج.م)
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.warning("⚠️ عذراً، هذا الصنف غير مسجل في فروعنا.")
                else:
                    amt = data.get("amount", 0)
                    tx_type = data.get("type", "INCOME")
                    tx_category = data.get("category", "مبيعات")
                    item = data.get("item_or_person", emp_input)
                    qty = data.get("quantity", 1)
                    
                    if amt == 0:
                        st.error("⚠️ عذراً، يرجى كتابة المبلغ أو السعر بوضوح.")
                    else:
                        supabase.table("transactions").insert({
                            "type": tx_type,
                            "item_or_person": item,
                            "quantity": qty,
                            "amount": amt,
                            "raw_text": emp_input,
                            "created_by_user_id": USER_ID,
                            "category": tx_category,
                            "branch": emp_branch,
                            "employee": emp_name
                        }).execute()
                        
                        post_journal_entry(tx_type, tx_category, amt, emp_input)
                        
                        st.markdown(f"""
                        <div style="background: rgba(15, 23, 42, 0.95); border: 2px solid #10b981; padding: 16px; border-radius: 14px; margin-top: 15px;">
                            <p style="margin: 0; color: #f3f4f6; font-size: 16px; font-weight: bold; text-align: center;">
                                ✅ تم تسجيل المبيعات بنجاح باسم ({emp_name}) في ({emp_branch}) بمبلغ ({amt} ج.م)!
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.error("الرجاء كتابة تفاصيل البيعة أو الاستعلام.")
