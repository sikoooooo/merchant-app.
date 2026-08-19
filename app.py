import streamlit as st
import re
from supabase import create_client, Client

# --- 1. إعدادات الصفحة ---
st.set_page_config(
    page_title="المحاسب الذكي - Enterprise Pro",
    page_icon="💼",
    layout="wide"
)

# --- 2. التصميم ---
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
    padding: 20px;
    border-radius: 16px;
    color: white;
    text-align: center;
    margin-bottom: 20px;
    border: 1px solid #3b82f6;
}
.stButton button {
    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
    color: white !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    border: none !important;
    padding: 10px 20px !important;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

# --- 3. بيانات الاتصال بقاعدة البيانات ---
SUPABASE_URL = "https://nqindgywshroejrcxtky.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6In5xaW5kZ3l3c2hyb2VqcmN4dGt5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NjgxNTExMCwiZXhwIjoyMTAyMzkxMTEwfQ.g-jpUzajE_OxGNNjF2QCFZINWjRfGSPCSHR2rtOtUTE"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# --- 4. المحلل الذكي المبسط والآمن ---
def process_command_smart(text: str):
    query_keywords = ["بكام", "سعر", "عندنا", "كام", "فين", "رصيد", "إيه", "ايه"]
    is_query = any(k in text for k in query_keywords) and not any(w in text for w in ["اشترينا", "بعنا", "دفعنا", "قبضنا"])
    
    if is_query:
        return {"type": "QUERY", "query_text": text}

    income_keywords = ["بيع", "بعت", "بعنا", "باع", "مبيعات", "قبضت", "قبضنا", "حصلنا", "توريد"]
    is_sale = any(w in text for w in income_keywords)
    
    # استخراج الأرقام من النص بطريقة دقيقة
    numbers = [float(n) for n in re.findall(r'\d+(?:\.\d+)?', text)]
    
    # تحليل الكمية والمبلغ بناءً على صيغة الجملة
    if len(numbers) >= 2 and ("كرتونة" in text or "قطعة" in text or "كيلو" in text):
        qty = numbers[0]
        amount = numbers[0] * numbers[1] if len(numbers) == 2 and numbers[1] < 1000 else numbers[-1]
    else:
        qty = numbers[0] if len(numbers) >= 2 and not ("بـ" in text or "بى" in text) else 1
        amount = numbers[-1] if numbers else 0

    return {
        "type": "INCOME" if is_sale else "EXPENSE",
        "category": "مبيعات" if is_sale else "مشتريات وبضاعة",
        "item_or_person": text,
        "quantity": int(qty),
        "amount": amount
    }

# --- 5. إدارة الجلسة والدخول ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.user_name = ""
    st.session_state.branch = ""

if "messages" not in st.session_state:
    st.session_state.messages = []

if not st.session_state.logged_in:
    st.markdown("""
    <div class="hero-header">
        <h1>🔐 نظام المحاسب الذكي - بوابة الدخول</h1>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username = st.text_input("اسم المستخدم:", value="admin")
        password = st.text_input("كلمة المرور:", type="password", value="1234")
        
        if st.button("دخول"):
            if username == "admin" and password == "1234":
                st.session_state.logged_in = True
                st.session_state.role = "admin"
                st.session_state.user_name = "صاحب المؤسسة"
                st.session_state.branch = "الفرع الرئيسي (القاهرة)"
                st.rerun()
            else:
                st.error("خطأ في بيانات الدخول.")
else:
    target_branch = st.selectbox("📍 اختر الفرع:", ["الفرع الرئيسي (القاهرة)", "فرع الإسكندرية"])
    
    if st.button("🚪 خروج"):
        st.session_state.logged_in = False
        st.rerun()

    st.markdown(f"""
    <div class="hero-header">
        <h2>🤖 المحاسب الذكي التفاعلي</h2>
        <p>الفرع الحالي: <b>{target_branch}</b></p>
    </div>
    """, unsafe_allow_html=True)

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("اكتب معاملتك هنا (مثال: بعنا 5 كرتونة بـ 1200)..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("جاري معالجة وتفظ العملية..."):
                data = process_command_smart(prompt)
                
                if data.get("type") == "QUERY":
                    response_text = f"🔍 تم استلام طلب البحث عن: {prompt} في فرع {target_branch}."
                else:
                    amt = data.get("amount", 0)
                    tx_type = data.get("type", "EXPENSE")
                    item = data.get("item_or_person", prompt)
                    qty = data.get("quantity", 1)
                    tx_category = data.get("category", "مشتريات")
                    
                    if amt == 0:
                        response_text = "⚠️ لم أستطع تحديد المبلغ بوضوح، يرجى كتابة الرقم مع العملية."
                    else:
                        try:
                            payload = {
                                "type": tx_type,
                                "item_or_person": item,
                                "quantity": qty,
                                "amount": amt,
                                "raw_text": prompt,
                                "category": tx_category,
                                "branch": target_branch,
                                "employee": st.session_state.user_name
                            }
                            supabase.table("transactions").insert(payload).execute()
                            response_text = f"✅ **تم تسجيل العملية بنجاح في قاعدة البيانات!**\n- البيان: {item}\n- الكمية: {qty}\n- القيمة: {amt} ج.م"
                        except Exception as e:
                            response_text = f"❌ خطأ في حفظ البيانات: {str(e)}"

                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
