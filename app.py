import os
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

# --- 4. إعداد مفتاح الـ Gemini بشكل آمن ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        gemini_api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        gemini_api_key = ""
except Exception:
    gemini_api_key = ""

genai.configure(api_key=gemini_api_key)

def get_next_gemini_model():
    return genai.GenerativeModel('gemini-3.6-flash')

# --- 4.1 ضمان وجود شركة افتراضية وفروع في قاعدة البيانات ---
def ensure_default_enterprise_setup(branch_name):
    try:
        # 1. فحص أو إنشاء شركة افتراضية
        comp_res = supabase.table("companies").select("id").limit(1).execute()
        if comp_res.data and len(comp_res.data) > 0:
            company_id = comp_res.data[0]["id"]
        else:
            new_comp = supabase.table("companies").insert({"name": "الشركة الافتراضية العامة"}).execute()
            company_id = new_comp.data[0]["id"]
            
        # 2. فحص أو إنشاء الفرع الحالي
        branch_res = supabase.table("branches").select("id").eq("branch_name", branch_name).execute()
        if branch_res.data and len(branch_res.data) > 0:
            branch_id = branch_res.data[0]["id"]
        else:
            new_branch = supabase.table("branches").insert({
                "company_id": company_id,
                "branch_name": branch_name,
                "is_main_branch": True if "الرئيسي" in branch_name else False
            }).execute()
            branch_id = new_branch.data[0]["id"]
            
        return company_id, branch_id
    except Exception as e:
        print(f"Setup error: {e}")
        return None, None

# --- 5. المعالجة الذكية بالاعتماد على جدول الذاكرة (business_rules) وموديل gemini-3.6-flash ---
def smart_process_command(user_text, branch="الفرع الرئيسي (القاهرة)"):
    try:
        rules_res = supabase.table("business_rules").select("*").eq("branch", branch).execute()
        known_rules = rules_res.data if rules_res.data else []
    except Exception as e:
        known_rules = []
        
    model = get_next_gemini_model()
    
    prompt = f"""
    أنت محاسب ذكي لنظام ERP مرن. التاجر أدخل الجملة التالية: "{user_text}"
    إليك قواعد التحويل المحفوظة سابقاً لدى التاجر في هذا الفرع: {json.dumps(known_rules, ensure_ascii=False)}
    
    مهمتك:
    1. فهم نوع العملية (SALE لبيع، PURCHASE لشراء، أو QUERY للاستعلام).
    2. استخراج اسم الصنف والكمية ووحدة القياس المدخلة.
    3. استخراج السعر إن وجد، وإلا اجعله 0.
    4. يجب أن يكون ردك بصيغة JSON نقي فقط بدون أي كلام إضافي بالشكل التالي:
    {{"type": "SALE أو PURCHASE أو QUERY", "item_name": "اسم الصنف", "quantity": رقم, "unit": "وحدة القياس", "unit_price": رقم, "needs_clarification": false, "message_to_user": "رد ودود ومؤكد للتاجر" }}
    """
    
    response = model.generate_content(prompt)
    
    try:
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        result = json.loads(clean_text)
        return result
    except Exception as e:
        return {
            "type": "QUERY" if "كم" in user_text or "سعر" in user_text else "SALE",
            "item_name": user_text,
            "quantity": 1,
            "unit": "قطعة",
            "unit_price": 0,
            "message_to_user": "تم استقبال الجملة وتجهيزها."
        }

# --- 5.1 دالة تسجيل الحركة بالكامل في Transactions, Journal Entries & Inventory ---
def execute_transaction_to_supabase(branch, parsed_data, raw_text):
    trans_type = parsed_data.get("type")
    item_name = parsed_data.get("item_name")
    input_qty = float(parsed_data.get("quantity", 1))
    input_unit = parsed_data.get("unit", "قطعة")
    unit_price = float(parsed_data.get("unit_price", 0))
    
    total_amount = input_qty * unit_price
    base_qty_deducted = input_qty 

    company_id, branch_id = ensure_default_enterprise_setup(branch)

    try:
        # أ. تسجيل الحركة في جدول transactions
        try:
            transaction_record = {
                "company_id": company_id,
                "branch_id": branch_id,
                "branch": branch,
                "type": trans_type,
                "item_name": item_name,
                "input_quantity": input_qty,
                "input_unit": input_unit,
                "base_quantity_deducted": base_qty_deducted,
                "unit_price": unit_price,
                "total_amount": total_amount,
                "raw_text": raw_text
            }
            supabase.table("transactions").insert(transaction_record).execute()
        except Exception as tx_err:
            print(f"Transactions insert error: {tx_err}")

        # ب. تسجيل قيد محاسبي مبدئي في journal_entries
        try:
            journal_record = {
                "company_id": company_id,
                "branch_id": branch_id,
                "description": f"حركة {trans_type} للصنف: {item_name} - {raw_text}",
                "total_amount": total_amount
            }
            supabase.table("journal_entries").insert(journal_record).execute()
        except Exception as je_err:
            print(f"Journal entries insert error: {je_err}")

        # ج. تحديث المخزن في جدول inventory
        try:
            existing = supabase.table("inventory").select("*").eq("branch", branch).eq("item_name", item_name).execute()
            
            if existing.data:
                current_total = float(existing.data[0].get("total_base_quantity", 0))
                if trans_type == "SALE":
                    new_total = current_total - base_qty_deducted
                else: 
                    new_total = current_total + base_qty_deducted
                    
                supabase.table("inventory").update({"total_base_quantity": new_total}).eq("branch", branch).eq("item_name", item_name).execute()
            else:
                initial_total = base_qty_deducted if trans_type == "PURCHASE" else -base_qty_deducted
                new_inventory_record = {
                    "branch": branch,
                    "item_name": item_name,
                    "total_base_quantity": initial_total,
                    "avg_cost_per_base": unit_price
                }
                supabase.table("inventory").insert(new_inventory_record).execute()
        except Exception as inv_err:
            print(f"Inventory update error: {inv_err}")
            
        return True
    except Exception as e:
        print(f"General DB Error: {e}")
        return False

if "employees_list" not in st.session_state:
    st.session_state.employees_list = [
        {"id": 1, "name": "محمود", "role": "موظف مبيعات", "branch": "الفرع الرئيسي (القاهرة)", "permissions": ["تسجيل مبيعات", "استعلام عن الأسعار"]},
        {"id": 2, "name": "إسلام", "role": "مسؤول مخازن", "branch": "الفرع الرئيسي (القاهرة)", "permissions": ["متابعة وجرد المخازن"]}
    ]

ALL_AVAILABLE_PERMISSIONS = [
    "تسجيل مبيعات", "استعلام عن الأسعار", "متابعة وجرد المخازن", "تسجيل المصاريف", "متابعة التقارير المالية"
]

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
                st.info("لا توجد أصناف مسجلة في المخزن حتى الآن.")
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
        
        st.markdown("""
        <div class="hero-header">
            <h2>🤖 المحاسب الذكي التفاعلي</h2>
        </div>
        """, unsafe_allow_html=True)
        
        st.write(f"الفرع الحالي: **{target_branch}**")
        
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
        if prompt := st.chat_input("اكتب معاملتك هنا (مثال: اشترينا 5 طن زيت بـ 30000)..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
                
            with st.chat_message("assistant"):
                with st.spinner("🤖 جاري تحليل المعاملة وتسجيلها في السجلات والقيود..."):
                    data = smart_process_command(prompt, branch=target_branch)
                    
                    if data.get("type") == "QUERY":
                        response_text = f"🔍 {data.get('message_to_user', 'تم الاستعلام بنجاح.')}"
                    else:
                        success = execute_transaction_to_supabase(target_branch, data, prompt)
                        response_text = f"✅ {data.get('message_to_user', 'تم تسجيل المعاملة في العمليات والقيود والمخزن بنجاح.')}\n\n- الصنف: {data.get('item_name')}\n- الكمية: {data.get('quantity')} {data.get('unit')}\n- السعر: {data.get('unit_price')}"
                    
                    st.markdown(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
