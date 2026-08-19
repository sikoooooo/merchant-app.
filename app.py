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
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5xaW5kZ3l3c2hyb2VqcmN4dGt5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NjgxNTExMCwiZXhwIjoyMTAyMzkxMTEwfQ.g-jpUzajE_OxGNNjF2QCFZINWjRfGSPCSHR2rtOtUTE"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

if "employees_list" not in st.session_state:
    st.session_state.employees_list = [
        {"id": 1, "name": "محمود", "role": "موظف مبيعات", "branch": "الفرع الرئيسي (القاهرة)", "permissions": ["تسجيل مبيعات", "استعلام عن الأسعار"]},
        {"id": 2, "name": "إسلام", "role": "مسؤول مخازن", "branch": "الفرع الرئيسي (القاهرة)", "permissions": ["متابعة وجرد المخازن"]}
    ]

ALL_AVAILABLE_PERMISSIONS = [
    "تسجيل مبيعات",
    "استعلام عن الأسعار",
    "متابعة وجرد المخازن",
    "تسجيل المصاريف",
    "متابعة التقارير المالية"
]

# --- 4. المحلل الذكي المبسط والآمن ---
def process_command_smart(text: str):
    query_keywords = ["بكام", "سعر", "عندنا", "كام", "فين", "رصيد", "إيه", "ايه"]
    is_query = any(k in text for k in query_keywords) and not any(w in text for w in ["اشترينا", "بعنا", "دفعنا", "قبضنا"])
    
    if is_query:
        return {"type": "QUERY", "query_text": text}

    income_keywords = ["بيع", "بعت", "بعنا", "باع", "مبيعات", "قبضت", "قبضنا", "حصلنا", "توريد"]
    is_sale = any(w in text for w in income_keywords)
    
    numbers = [float(n) for n in re.findall(r'\d+(?:\.\d+)?', text)]
    
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
        username = st.text_input("اسم المستخدم الإداري:", value="admin")
        password = st.text_input("كلمة المرور:", type="password", value="1234")
        
        if st.button("دخول لوحة التحكم"):
            if username == "admin" and password == "1234":
                st.session_state.logged_in = True
                st.session_state.role = "admin"
                st.session_state.user_name = "صاحب المؤسسة"
                st.session_state.branch = "الفرع الرئيسي (القاهرة)"
                st.rerun()
            else:
                st.error("خطأ في بيانات الدخول.")
else:
    if st.session_state.role == "admin":
        with st.sidebar:
            st.markdown("### 👑 لوحة التحكم الإدارية")
            st.write(f"مرحباً بك: **{st.session_state.user_name}**")
            st.markdown("---")
            admin_page = st.radio(
                "اختر القسم:",
                ["📊 متابعة العمليات والشات الذكي", "🛠️ إدارة الموظفين والصلاحيات"]
            )
            st.markdown("---")
            if st.button("🚪 تسجيل الخروج"):
                st.session_state.logged_in = False
                st.session_state.role = None
                st.rerun()
    else:
        admin_page = "📊 متابعة العمليات والشات الذكي"
        if st.button("🚪 خروج"):
            st.session_state.logged_in = False
            st.rerun()

    if st.session_state.role == "admin" and admin_page == "🛠️ إدارة الموظفين والصلاحيات":
        st.markdown("""
        <div class="hero-header">
            <h2>🛠️ إدارة الموظفين والصلاحيات</h2>
            <p>تعديل فروع وصلاحيات طاقم العمل</p>
        </div>
        """, unsafe_allow_html=True)
        
        for i, emp in enumerate(st.session_state.employees_list):
            c1, c2 = st.columns([1, 1])
            with c1:
                new_name = st.text_input(f"اسم الموظف {i+1}", value=emp["name"], key=f"name_{i}")
                new_branch = st.selectbox(f"الفرع {i+1}", ["الفرع الرئيسي (القاهرة)", "فرع الإسكندرية"], index=0 if emp["branch"]=="الفرع الرئيسي (القاهرة)" else 1, key=f"br_{i}")
            with c2:
                default_perms = [p for p in emp["permissions"] if p in ALL_AVAILABLE_PERMISSIONS]
                new_perms = st.multiselect(f"صلاحيات الموظف {i+1}", options=ALL_AVAILABLE_PERMISSIONS, default=default_perms, key=f"perms_{i}")
                
            if st.button(f"💾 حفظ التعديلات للموظف {i+1}", key=f"save_{i}"):
                st.session_state.employees_list[i]["name"] = new_name
                st.session_state.employees_list[i]["branch"] = new_branch
                st.session_state.employees_list[i]["permissions"] = new_perms
                st.success("تم الحفظ بنجاح!")
                st.rerun()
            st.markdown("---")
    else:
        target_branch = st.selectbox("📍 اختر الفرع:", ["الفرع الرئيسي (القاهرة)", "فرع الإسكندرية"])

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
                with st.spinner("جاري معالجة وحفظ العملية..."):
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
                                
                                # تحديث أو إضافة الصنف مباشرة في جدول inventory (المخزن)
                                existing_item = supabase.table("inventory").select("*").eq("branch", target_branch).ilike("item_name", f"%{item}%").execute()
                                
                                if existing_item.data and len(existing_item.data) > 0:
                                    current_qty = existing_item.data[0].get("quantity", 0)
                                    item_id = existing_item.data[0]["id"]
                                    
                                    new_qty = current_qty + qty if tx_type == "EXPENSE" else current_qty - qty
                                    supabase.table("inventory").update({"quantity": max(0, new_qty)}).eq("id", item_id).execute()
                                else:
                                    supabase.table("inventory").insert({
                                        "branch": target_branch,
                                        "item_name": item,
                                        "quantity": qty,
                                        "price": amt / qty if qty > 0 else amt
                                    }).execute()

                                response_text = f"✅ **تم تسجيل العملية وتحديث المخزن بنجاح في ({target_branch})!**\n- البيان: {item}\n- الكمية: {qty}\n- القيمة: {amt} ج.م"
                            except Exception as e:
                                response_text = f"❌ خطأ في حفظ البيانات: {str(e)}"

                    st.markdown(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
