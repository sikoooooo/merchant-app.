import os
import streamlit as st
import google.generativeai as genai
import json
from supabase import create_client, Client

# --- 1. إعدادات الصفحة ---
st.set_page_config(
    page_title="المحاسب الذكي - نواة علي بابا",
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
    return genai.GenerativeModel('gemini-2.5-flash')

# --- 4.1 ضمان وجود الشركة والفرع في الجداول (تجهيز الـ IDs) ---
def ensure_default_enterprise_setup(branch_name):
    try:
        comp_res = supabase.table("companies").select("id").limit(1).execute()
        if comp_res.data and len(comp_res.data) > 0:
            company_id = comp_res.data[0]["id"]
        else:
            new_comp = supabase.table("companies").insert({"name": "الشركة الافتراضية العامة"}).execute()
            company_id = new_comp.data[0]["id"]
            
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

# --- 5. المعالجة الذكية بالاعتماد على جدول الذاكرة (business_rules) ---
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

# --- 5.1 دالة التنفيذ مع حساب متوسط التكلفة المرجح (Weighted Average Cost) ---
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

        # ب. تسجيل القيد المحاسبي في journal_entries
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

        # ج. تحديث المخزن وحساب متوسط التكلفة المرجح (Weighted Average Cost)
        try:
            existing = supabase.table("inventory").select("*").eq("branch", branch).eq("item_name", item_name).execute()
            
            if existing.data:
                item_row = existing.data[0]
                current_total = float(item_row.get("total_base_quantity", 0))
                current_avg_cost = float(item_row.get("avg_cost_per_base", 0))
                
                if trans_type == "PURCHASE":
                    new_total = current_total + base_qty_deducted
                    # حساب متوسط التكلفة المتحرك الجديد
                    if new_total > 0:
                        new_avg_cost = ((current_total * current_avg_cost) + (base_qty_deducted * unit_price)) / new_total
                    else:
                        new_avg_cost = unit_price
                else: # SALE
                    new_total = current_total - base_qty_deducted
                    new_avg_cost = current_avg_cost # متوسط التكلفة لا يتغير عند البيع
                    
                supabase.table("inventory").update({
                    "total_base_quantity": new_total,
                    "avg_cost_per_base": new_avg_cost
                }).eq("branch", branch).eq("item_name", item_name).execute()
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

# --- 6. واجهة العرض وإدارة الجلسة ---
if "messages" not in st.session_state:
    st.session_state.messages = []

target_branch = st.selectbox("📍 اختر الفرع:", ["الفرع الرئيسي (القاهرة)", "فرع الإسكندرية"])

st.markdown("""
<div class="hero-header">
    <h2>🤖 المحاسب الذكي - نواة علي بابا</h2>
    <p>تخزين لحظي، قيود مزدوجة، وحسابات تكلفة متقدمة</p>
</div>
""", unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
if prompt := st.chat_input("اكتب معاملتك هنا (مثال: اشترينا 5 طن زيت بـ 30000)..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        
    with st.chat_message("assistant"):
        with st.spinner("🤖 جاري معالجة العملية وتسجيلها في نواة النظام..."):
            data = smart_process_command(prompt, branch=target_branch)
            
            if data.get("type") == "QUERY":
                response_text = f"🔍 {data.get('message_to_user', 'تم الاستعلام بنجاح.')}"
            else:
                success = execute_transaction_to_supabase(target_branch, data, prompt)
                response_text = f"✅ {data.get('message_to_user', 'تم تسجيل المعاملة وتحديث المخزن ومتوسط التكلفة بنجاح.')}\n\n- الصنف: {data.get('item_name')}\n- الكمية: {data.get('quantity')} {data.get('unit')}\n- السعر: {data.get('unit_price')}"
            
            st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
