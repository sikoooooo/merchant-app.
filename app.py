import streamlit as st
import json
import re
import uuid
import google.generativeai as genai
from supabase import create_client, Client

# --- 1. إعدادات الصفحة ---
st.set_page_config(
    page_title="المحاسب الذكي - Enterprise Pro",
    page_icon="💼",
    layout="wide"
)

# --- 2. التصميم وتثبيت القائمة الجانبية للآدمن ---
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

# --- 3. بيانات الاتصال ومفاتيح الـ API ---
SUPABASE_URL = "https://nqindgywshroejrcxtky.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6In5xaW5kZ3l3c2hyb2VqcmN4dGt5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NjgxNTExMCwiZXhwIjoyMTAyMzkxMTEwfQ.g-jpUzajE_OxGNNjF2QCFZINWjRfGSPCSHR2rtOtUTE"

API_KEYS = [
    "AQ.Ab8RN6KsmZlOVBitqBHl9MTKvhDTCrOkLckSZOLq5opLxEM97g",
    "AQ.Ab8RN6IOOQs421k9-f9CtpYl-b7mKWe1ID2e-VODE8WbGDLy0g",
    "AQ.Ab8RN6LDnxPObId4PxP_7RWvXtPSekj6ftHZ6AIwiVKyVQso5Q",
    "AQ.Ab8RN6IXSRGUETheaRkxa2JuolYCfGIL-888kwz8J9-OfWZ4Gw"
]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
USER_ID = "855633fe-a3a8-400d-a9ae-9fe439e658bd"

ALL_AVAILABLE_PERMISSIONS = [
    "تسجيل مبيعات",
    "استعلام عن الأسعار",
    "متابعة وجرد المخازن",
    "تسجيل المصاريف",
    "متابعة التقارير المالية"
]

def get_branch_id(branch_name: str):
    try:
        res = supabase.table("branches").select("id").eq("name", branch_name).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]["id"]
    except Exception:
        pass
    return None

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
    
    # محاولة التحليل بالذكاء الاصطناعي مع منع الأخطاء
    for key in API_KEYS:
        try:
            genai.configure(api_key=key)
            system_instruction = """
            أنت محاسب ذكي وخبير في تجارة الجملة والمفرد باللهجة العامية المصرية.
            أجب بصيغة JSON نقي فقط بدون أي نص خارجي وبدون علامات الـ markdown بالهيكل التالي:
            {
              "type": "INCOME أو EXPENSE",
              "category": "مبيعات أو مشتريات وبضاعة أو أصول ثابتة أو مصاريف تشغيلية",
              "item_or_person": "اسم الصنف",
              "quantity": رقم الكمية,
              "amount": المبلغ الاجمالي
            }
            """
            model = genai.GenerativeModel(model_name='gemini-1.5-flash', system_instruction=system_instruction)
            res = model.generate_content(f"حلل المعاملة: '{text}'")
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
            
    # الخطة البديلة الآمنة في حال فشل الـ AI أو إرجاع خطأ JSON
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
    try:
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
    except Exception:
        pass
    return True

# --- 4. إدارة الجلسة والدخول ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.user_name = ""
    st.session_state.branch = ""

if "employees_list" not in st.session_state:
    st.session_state.employees_list = [
        {"id": 1, "name": "محمود", "role": "موظف مبيعات", "branch": "الفرع الرئيسي (القاهرة)", "permissions": ["تسجيل مبيعات", "استعلام عن الأسعار"]},
        {"id": 2, "name": "إسلام", "role": "مسؤول مخازن", "branch": "الفرع الرئيسي (القاهرة)", "permissions": ["متابعة وجرد المخازن"]},
        {"id": 3, "name": "خالد", "role": "موظف مبيعات", "branch": "فرع الإسكندرية", "permissions": ["تسجيل مبيعات", "استعلام عن الأسعار"]}
    ]

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- شاشة تسجيل الدخول ---
if not st.session_state.logged_in:
    st.markdown("""
    <div class="hero-header">
        <h1>🔐 نظام المحاسب الذكي - بوابة الدخول الموحدة</h1>
        <p>اختر نوع حسابك للمتابعة</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        login_type = st.radio("نوع الدخول:", ["👑 صاحب المؤسسة (الآدمن)", "👤 موظف / كاشير الفرع"])
        
        if login_type == "👑 صاحب المؤسسة (الآدمن)":
            username = st.text_input("اسم المستخدم الإداري:", value="admin")
            password = st.text_input("كلمة المرور:", type="password", value="1234")
            
            if st.button("دخول لوحة تحكم الإدارة"):
                if username == "admin" and password == "1234":
                    st.session_state.logged_in = True
                    st.session_state.role = "admin"
                    st.session_state.user_name = "صاحب المؤسسة"
                    st.rerun()
                else:
                    st.error("خطأ في بيانات الآدمن.")
        else:
            emp_names_selection = [e["name"] + f" ({e['branch']})" for e in st.session_state.employees_list]
            emp_select = st.selectbox("اختر اسمك:", emp_names_selection)
            selected_emp_obj = next((e for e in st.session_state.employees_list if e["name"] in emp_select), None)
            
            pin_code = st.text_input("رمز الدخول السريع (PIN):", type="password", value="0000")
            
            if st.button("دخول بوابة الموظفين"):
                if selected_emp_obj:
                    st.session_state.logged_in = True
                    st.session_state.role = "employee"
                    st.session_state.user_name = selected_emp_obj["name"]
                    st.session_state.branch = selected_emp_obj["branch"]
                    st.rerun()

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
        top_c1, top_c2 = st.columns([4, 1])
        with top_c1:
            st.write(f"👤 الموظف: **{st.session_state.user_name}** | 📍 الفرع: **{st.session_state.branch}**")
        with top_c2:
            if st.button("🚪 خروج"):
                st.session_state.logged_in = False
                st.session_state.role = None
                st.rerun()
        st.markdown("---")

    if st.session_state.role == "admin" and admin_page == "🛠️ إدارة الموظفين والصلاحيات":
        st.markdown("""
        <div class="hero-header">
            <h2>🛠️ إدارة الموظفين والصلاحيات</h2>
            <p>تعديل بيانات وفروع وصلاحيات طاقم العمل بكل سهولة</p>
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
        if st.session_state.role == "admin":
            target_branch = st.selectbox("📍 اختر الفرع المراد متابعته عبر المساعد الآلي:", ["الفرع الرئيسي (القاهرة)", "فرع الإسكندرية"])
        else:
            target_branch = st.session_state.branch

        st.markdown(f"""
        <div class="hero-header">
            <h2>🤖 المحاسب الذكي التفاعلي</h2>
            <p>فرع التشغيل الحالي: <b>{target_branch}</b></p>
        </div>
        """, unsafe_allow_html=True)

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("اكتب معاملتك هنا (مثال: بعنا 10 كرتونة بـ 2500 أو كرتونة البيض بكام؟)..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("جاري معالجة العملية وتسجيلها..."):
                    data = process_command_ai(prompt)
                    
                    if data.get("type") == "QUERY":
                        found_item = search_item_price(prompt, target_branch)
                        if found_item:
                            response_text = f"🔍 **نتيجة الاستعلام في ({target_branch}):** الصنف ({found_item.get('item_or_person')}) بقيمة ({found_item.get('amount')} ج.م)."
                        else:
                            response_text = f"⚠️ عذراً، لم أجد تسجيلاً لهذا الصنف في بيانات {target_branch}."
                    else:
                        amt = data.get("amount", 0)
                        tx_type = data.get("type", "INCOME")
                        tx_category = data.get("category", "مبيعات")
                        item = data.get("item_or_person", prompt)
                        qty = data.get("quantity", 1)
                        
                        if amt == 0:
                            response_text = "⚠️ لم أستطع تحديد المبلغ بدقة، يرجى كتابة الرقم مع العملية بوضوح."
                        else:
                            branch_uuid = get_branch_id(target_branch)
                            
                            supabase.table("transactions").insert({
                                "type": tx_type,
                                "item_or_person": item,
                                "quantity": qty,
                                "amount": amt,
                                "raw_text": prompt,
                                "created_by_user_id": USER_ID,
                                "category": tx_category,
                                "branch_id": branch_uuid,
                                "branch": target_branch,
                                "employee": st.session_state.user_name
                            }).execute()
                            
                            post_journal_entry(tx_type, tx_category, amt, prompt)
                            response_text = f"✅ **تم تسجيل العملية بنجاح في ({target_branch})!**\n- البيان: {item}\n- القيمة: {amt} ج.م"

                    st.markdown(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
