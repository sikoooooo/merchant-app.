import streamlit as st
import json
import re
import uuid
import google.generativeai as genai
from supabase import create_client, Client

# --- 1. إعدادات الصفحة الاحترافية ---
st.set_page_config(
    page_title="المحاسب الذكي - الإدارة الحديثة",
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

# --- 3. بيانات الاتصال ومفاتيح الـ API المتعددة (لضمان التشغيل المستمر) ---
SUPABASE_URL = "https://nqindgywshroejrcxtky.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5xaW5kZ3l3c2hyb2VqcmN4dGt5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NjgxNTExMCwiZXhwIjoyMTAyMzkxMTEwfQ.g-jpUzajE_OxGNNjF2QCFZINWjRfGSPCSHR2rtOtUTE"

# حط هنا مفاتيح إخواتك كلها عشان نوزع عليها الشغل وتبقي في الأمان تماماً
API_KEYS = [
    "AQ.Ab8RN6Jy0DoPtrUG0NWxTlQhxbFGLWNiX0jIEPUiFunbvoA1KA",
    # "حط المفتاح الثاني هنا",
    # "حط المفتاح الثالث هنا"
]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
USER_ID = "855633fe-a3a8-400d-a9ae-9fe439e658bd"

def process_command_ai(text: str):
    """المحاسب الذكي: يقوم بالتحليل واستخراج الحسابات والكميات وإجراء العمليات الحسابية في JSON نقي"""
    # نختار أول مفتاح أو نوزعهم
    key = API_KEYS[0]
    genai.configure(api_key=key)
    
    system_instruction = """
    أنت نظام محاسبي ذكي ومحترف، وخبير في استخلاص العمليات التجارية باللهجة العامية المصرية أو العربية.
    قم بتحليل الجملة التجارية المدخلة وقم بإجراء العمليات الحسابية اللازمة (مثل الكمية × السعر لو وجدوا) وأجب بصيغة JSON فقط يحتوي على الحقول التالية:
    1. "type": حدد "INCOME" لو كانت (بيع، إيراد، قبض أموال)، وحدد "EXPENSE" لو كانت (شراء، مصروف، دفع، إيجار، دعاية).
    2. "category": تصنيف دقيق حصرياً من بين (مبيعات، مصاريف تشغيلية، مصاريف دعاية وإعلان، مصاريف إدارية).
    3. "item_or_person": اسم الصنف أو البيان الصافي.
    4. "quantity": الكمية الرقمية الواردة في الجملة (لو لم تذكر، ضعها 1).
    5. "amount": المبلغ الإجمالي النهائي (ناتج ضرب الكمية في السعر لو جملة مثل '10 كراتين الكرتونة بـ 120' فيكون المبلغ 1200). لو لم يوجد مبلغ نهائي واضح، اجعله 0.
    
    أجب بصيغة JSON صحيح 100% بدون أي نص خارجه، وبدون علامات الـ markdown لو أمكن أو نظيف تماماً.
    """
    
    # ممكن نستخدم الـ flash أو نupgrade لـ pro زي ما اتفقنا
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash', 
        system_instruction=system_instruction
    )
    
    prompt = f"حلل المعاملة التجارية التالية بدقة تامة: '{text}'"
    
    try:
        res = model.generate_content(prompt)
        raw_text = res.text.strip()
        
        # تنظيف الـ JSON لو رجع في ماركداون
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()
            
        data = json.loads(raw_text)
        return data
        
    except Exception as e:
        # نظام احتياطي لو حصل أي خطأ في الـ AI
        numbers = re.findall(r'\d+', text)
        amt = int(numbers[-1]) if numbers else 0
        is_sale = any(w in text for w in ["بيع", "بعت", "باع", "قبضت", "مبيعات"])
        return {
            "type": "INCOME" if is_sale else "EXPENSE",
            "category": "مبيعات" if is_sale else "مصاريف تشغيلية",
            "item_or_person": text,
            "quantity": 1,
            "amount": amt
        }

def post_journal_entry(tx_type, category, amount, description):
    """ترحيل القيد المزدوج لجدول journal_entries"""
    entry_id = str(uuid.uuid4())
    id_cash = 1  # حساب النقدية ثابت
    
    if tx_type == "INCOME" or category == "مبيعات":
        id_target = 4  # المبيعات
        journal_data = [
            {"entry_id": entry_id, "account_id": id_cash, "debit": amount, "credit": 0.00, "description": description},
            {"entry_id": entry_id, "account_id": id_target, "debit": 0.00, "credit": amount, "description": description}
        ]
    else:
        id_target = 5  # المصروفات
        journal_data = [
            {"entry_id": entry_id, "account_id": id_target, "debit": amount, "credit": 0.00, "description": description},
            {"entry_id": entry_id, "account_id": id_cash, "debit": 0.00, "credit": amount, "description": description}
        ]
        
    supabase.table("journal_entries").insert(journal_data).execute()
    return True

# --- 4. واجهة المستخدم ---
st.markdown("""
<div class="hero-header">
    <h1>💎 النظام الذكي المحاسبي المطور</h1>
    <p>تحليل كامل ومباشر بالذكاء الاصطناعي مع الحسابات التلقائية للمخزن والقيود</p>
</div>
""", unsafe_allow_html=True)

voice_input = st.text_input("أدخل حركة التاجر:", placeholder="مثال: بعنا ١٠ كراتين بيض الكرتونه ب ١٢٠", label_visibility="collapsed")

if st.button("🚀 تنفيذ وحفظ المعاملة"):
    if voice_input:
        with st.spinner("✨ المحاسب الذكي يقوم بتحليل المعاملة وحساب الإجمالي..."):
            data = process_command_ai(voice_input)
            
            amt = data.get("amount", 0)
            tx_type = data.get("type", "EXPENSE")
            tx_category = data.get("category", "مصاريف تشغيلية")
            item = data.get("item_or_person", voice_input)
            qty = data.get("quantity", 1)
            
            # حماية صارمة للمبلغ
            if amt == 0:
                st.error("⚠️ عذراً، لم أستطع تحديد المبلغ بوضوح. من فضلك اكتب الجملة بوضوح (مثلاً: بعنا 5 كراتين بـ 100).")
            else:
                # 1. حفظ المعاملة في جدول transactions
                supabase.table("transactions").insert({
                    "type": tx_type,
                    "item_or_person": item,
                    "quantity": qty,
                    "amount": amt,
                    "raw_text": voice_input,
                    "created_by_user_id": USER_ID,
                    "category": tx_category
                }).execute()
                
                # 2. ترحيل القيود للدفتر المزدوج
                post_journal_entry(tx_type, tx_category, amt, voice_input)
                
                border_color = "#10b981" if tx_type == "INCOME" else "#f59e0b"
                st.markdown(f"""
                <div style="background: rgba(15, 23, 42, 0.95); border: 2px solid {border_color}; padding: 16px; border-radius: 14px; margin-top: 15px;">
                    <p style="margin: 0; color: #f3f4f6; font-size: 16px; font-weight: bold; text-align: center;">
                        ✅ تم بنجاح تسجيل ({tx_category}) للـ البيان ({item}) | الكمية: ({qty}) | بقيمة إجمالية ({amt} ج.م) كـ ({tx_type}) وترحيلها للدفتر!
                    </p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.error("الرجاء كتابة العملية أولاً.")
