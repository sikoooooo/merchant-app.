import streamlit as st
import google.generativeai as genai
import itertools
import json
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

# --- 4. إدارة المفاتيح المتعددة والتبديل الذكي لتوفير الاستهلاك ---
API_KEYS = [
    "AQ.Ab8RN6IOOQs421k9-f9CtpYl-b7mKWe1ID2e-VODE8WbGDLy0g", # hookapi
    "AQ.Ab8RN6LDnxPObId4PxP_7RWvXtPSekj6ftHZ6AIwiVKyVQso5Q", # mk
    "AQ.Ab8RN6IXSRGUETheaRkxa2JuolYCfGIL-888kwz8J9-OfWZ4Gw"  # kh
]

key_pool = itertools.cycle(API_KEYS)

def get_next_gemini_model():
    current_key = next(key_pool)
    genai.configure(api_key=current_key)
    return genai.GenerativeModel('gemini-1.5-flash')

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

# --- 5. المعالجة الذكية بالذكاء الاصطناعي ---
def process_command_with_ai(text: str):
    try:
        model = get_next_gemini_model()
        prompt_instruction = f"""
        أنت محاسب ذكي لنظام ERP مرن.
        حلل الجملة التالية واستخرج البيانات بتنسيق JSON حصرياً بدون أي نصوص إضافية:
        "{text}"
        
        الهيكل المطلوب:
        - "type": "SALE" (للبيع أو المنصرف)، "PURCHASE" (للشراء أو الوارد)، أو "QUERY" (للاستعلام عن رصيد أو سعر).
        - "item_name": اسم الصنف.
        - "quantity": الكمية كرقم (اعتبرها 1 إن لم تذكر).
        - "unit": وحدة القياس (مثل: طن، كيلو، توب، متر، كرتونة، قطعة).
        - "unit_price": السعر إن وجد، وإلا 0.
        """
        response = model.generate_content(prompt_instruction)
        cleaned_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_text)
    except Exception as e:
        return {
            "type": "QUERY" if "كم" in text or "سعر" in text else "SALE",
            "item_name": text,
            "quantity": 1,
            "unit": "قطعة",
            "unit_price": 0
        }

# --- 6. إدارة الجلسة والدخول ---
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
                ["📊 متابعة العمليات والشات الذكي", "📦 جرد ومتابعة المخزن", "🛠️ إدارة الموظفين والصلاحيات"]
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

    if st.session_state.role == "admin" and admin_page == "📦 جرد ومتابعة المخزن":
        st.markdown("""
        <div class="hero-header">
            <h2>📦 جرد ومتابعة المخزن اللحظي</h2>
            <p>أرصدة الأصناف والكميات الحالية متحدثة أوتوماتيكياً</p>
        </div>
        """, unsafe_allow_html=True)
        
        target_branch = st.selectbox("📍 تصفية حسب الفرع:", ["الكل", "الفرع الرئيسي (القاهرة)", "فرع الإسكندرية"])
        
        try:
            query = supabase.table("inventory").select("*")
            if target_branch != "الكل":
                query = query.eq("branch", target_branch)
            response = query.execute()
            inventory_data = response.data
            
            if inventory_data:
                st.dataframe(inventory_data, use_container_width=True)
            else:
                st.info("لا توجد أصناف مسجلة في المخزن حتى الآن. ابدأ بتسجيل عمليات بيع أو شراء وسيقوم السيستم بتعبئة المخزن تلقائياً!")
        except Exception as e:
            st.error(f"خطأ في جلب بيانات المخزن: {e}")

    elif st.session_state.role == "admin" and admin_page == "🛠️ إدارة الموظفين والصلاحيات":
        st.markdown("""
        <div class="hero-header">
            <h2>🛠️ إدارة الموظفين والصلاحيات</h2>
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

        if prompt := st.chat_input("اكتب معاملتك هنا (مثال: اشترينا 5 طن زيت بـ 30000 أو بعنا 2 توب قماش)..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("🤖 جاري تحليل المعاملة بالذكاء الاصطناعي وتحديث المخزن والقاعدة..."):
                    data = process_command_with_ai(prompt)
                    
                    if data.get("type") == "QUERY":
                        response_text = f"🔍 تم استلام استعلامك بشأن: **{data.get('item_name', prompt)}** في فرع {target_branch}."
                    else:
                        try:
                            qty = float(data.get("quantity", 1))
                            price = float(data.get("unit_price", 0))
                            total = qty * price if price > 0 else 0
                            
                            payload = {
                                "branch": target_branch,
                                "type": data.get("type", "SALE"),
                                "item_name": data.get("item_name", prompt),
                                "quantity": qty,
                                "unit": data.get("unit", "قطعة"),
                                "unit_price": price,
                                "total_amount": total,
                                "employee": st.session_state.user_name,
                                "raw_text": prompt
                            }
                            supabase.table("transactions").insert(payload).execute()
                            
                            response_text = f"""✅ **تمت معالجة العملية وتحديث المخزن أوتوماتيكياً ({target_branch})!**
- **النوع:** {'بيع / منصرف' if data.get('type')=='SALE' else 'شراء / وارد'}
- **الصنف:** {data.get('item_name')}
- **الكمية:** {qty} {data.get('unit')}
- **القيمة الإجمالية:** {total} ج.م"""
                        except Exception as e:
                            response_text = f"❌ خطأ أثناء الحفظ أو التحديث بالمخزن: {str(e)}"

                    st.markdown(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
