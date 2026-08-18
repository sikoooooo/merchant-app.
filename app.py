import streamlit as st
import json
import re
import uuid
import google.generativeai as genai
from supabase import create_client, Client

# --- 1. إعدادات الصفحة الاحترافية ---
st.set_page_config(
    page_title="المحاسب الصوتي الذكي - الإدارة الحديثة",
    page_icon="💎",
    layout="wide"
)

# --- 2. التصميم الفاخر (UI/UX) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .stApp { background: linear-gradient(135deg, #090d16 0%, #111827 100%); color: #f3f4f6; }
    .hero-header { background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); padding: 30px; border-radius: 20px; color: white; text-align: center; margin-bottom: 25px; box-shadow: 0 20px 25px -5px rgba(59, 130, 246, 0.2); }
    .metric-card { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.1); padding: 18px; border-radius: 16px; text-align: center; }
    .metric-card h3 { color: #60a5fa; font-size: 22px; font-weight: 700; margin-top: 5px; }
    .glass-card { background: #1e293b; border: 1px solid #334155; border-right: 6px solid #3b82f6; padding: 20px; border-radius: 16px; margin-bottom: 15px; }
    .stTextInput input { background-color: #0f172a !important; color: #ffffff !important; border-radius: 12px !important; border: 1px solid #475569 !important; padding: 12px !important; }
    .stButton button { background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important; color: white !important; border-radius: 12px !important; font-weight: 700 !important; border: none !important; padding: 12px 28px !important; width: 100%; }
    </style>
""", unsafe_allow_html=True)

# --- 3. بيانات الاتصال ---
SUPABASE_URL = "https://nqindgywshroejrcxtky.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5xaW5kZ3l3c2hyb2VqcmN4dGt5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NjgxNTExMCwiZXhwIjoyMTAyMzkxMTEwfQ.g-jpUzajE_OxGNNjF2QCFZINWjRfGSPCSHR2rtOtUTE"
API_KEYS = ["AQ.Ab8RN6Jy0DoPtrUG0NWxTlQhxbFGLWNiX0jIEPUiFunbvoA1KA"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
USER_ID = "855633fe-a3a8-400d-a9ae-9fe439e658bd"

def process_command_ai(text: str):
    """تحليل نصي حر ومفتوح بالذكاء الاصطناعي مع استخلاص دقيق للبيانات"""
    key = API_KEYS[0]
    genai.configure(api_key=key)
    
    system_instruction = """
    أنت نظام محاسبي ذكي وخبير مالي. قم بتحليل الجملة التجارية المدخلة واستخرج منها بدقة:
    1. type: "INCOME" إذا كانت عملية بيع، إيراد، أو قبض أموال. و "EXPENSE" إذا كانت شراء، مصروف، إيجار، أو دعاية.
    2. category: تصنيف دقيق حصرياً من بين (مبيعات، مصاريف تشغيلية، مصاريف دعاية وإعلان، مصاريف إدارية).
    3. item_or_person: اسم الصنف أو البيان الصافي بدون أرقام مبالغ.
    4. amount: الرقم المالي الإجمالي الصريح المرتبط بالمعاملة (لو لم يوجد مبلغ مالي واضح، اجعله 0).
    أجب بصيغة JSON فقط بدون أي نص إضافي أو علامات تMarkdown خارجية لو أمكن، أو نظيفة تماماً.
    """
    
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        system_instruction=system_instruction
    )
    
    prompt = f"حلل المعاملة التالية: '{text}'"
    
    try:
        res = model.generate_content(prompt)
        raw_text = res.text.strip()
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()
        
        data = json.loads(raw_text)
        
        # لو الـ AI جاب المبلغ 0 وفيه أرقام صريحة في النص، نلتقطها بذكاء محلي
        if not data.get("amount") or data.get("amount") == 0:
            numbers = re.findall(r'\d+', text)
            if numbers:
                # نأخذ الرقم الأخير باعتباره المبلغ الإجمالي غالباً في الجمل التجارية
                data["amount"] = int(numbers[-1])
                
        return data
        
    except Exception:
        # احتياطي لو حصل أي استثناء في الـ JSON
        numbers = re.findall(r'\d+', text)
        amt = int(numbers[-1]) if numbers else 0
        is_sale = any(w in text for w in ["بيع", "بعت", "باع", "قبضت", "مبيعات", "إيراد"])
        return {
            "intent": "ADD_TRANSACTION",
            "type": "INCOME" if is_sale else "EXPENSE",
            "category": "مبيعات" if is_sale else "مصاريف تشغيلية",
            "item_or_person": text,
            "quantity": 1,
            "amount": amt
        }

def post_journal_entry(tx_type, category, amount, description):
    """ترحيل القيد المزدوج لجدول journal_entries بطريقة صحيحة ومضبوطة محاسبياً"""
    entry_id = str(uuid.uuid4())
    id_cash = 1  # حساب النقدية ثابت
    
    if tx_type == "INCOME" or category == "مبيعات":
        id_target = 4  # المبيعات / الإيرادات
        journal_data = [
            {"entry_id": entry_id, "account_id": id_cash, "debit": amount, "credit": 0.00, "description": description},
            {"entry_id": entry_id, "account_id": id_target, "debit": 0.00, "credit": amount, "description": description}
        ]
    else:
        if "دعاية" in category:
            id_target = 5  # المصروفات أو الدعاية
        else:
            id_target = 5
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
        <p>تحليل مرن ومفتوح للعمليات التجارية بدقة تامة.</p>
    </div>
""", unsafe_allow_html=True)

voice_input = st.text_input("أدخل حركة التاجر:", placeholder="مثال: بعنا ١٢ علبة تونة العلبه بـ ١٠ جنيه", label_visibility="collapsed")

if st.button("🚀 تنفيذ وحفظ المعاملة"):
    if voice_input:
        with st.spinner("✨ جاري معالجة التحليل المالي الذكي..."):
            data = process_command_ai(voice_input)
            amt = data.get("amount", 0)
            
            # حماية صارمة: لو مفيش مبلغ مالي (amount == 0)، نوقف العملية ونبه التاجر فوراً
            if amt == 0:
                st.error("⚠️ عذراً، لم أستطع تحديد المبلغ المالي بوضوح في النص. من فضلك اكتب المبلغ (مثلاً: بعنا بـ 120 جنيه).")
            else:
                tx_type = data.get("type", "EXPENSE")
                tx_category = data.get("category", "مصاريف تشغيلية")
                item = data.get("item_or_person", voice_input)
                qty = data.get("quantity", 1)
                
                # تصحيح إضافي لو النص فيه بيع وصرح بـ INCOME
                if any(w in voice_input for w in ["بيع", "بعت", "باع", "قبضت", "مبيعات"]):
                    tx_type = "INCOME"
                    tx_category = "مبيعات"
                
                # 1. حفظ المعاملة في transactions
                supabase.table("transactions").insert({
                    "type": tx_type,
                    "item_or_person": item,
                    "quantity": qty,
                    "amount": amt,
                    "raw_text": voice_input,
                    "created_by_user_id": USER_ID,
                    "category": tx_category
                }).execute()
                
                # 2. ترحيل القيد المحاسبي المزدوج
                post_journal_entry(tx_type, tx_category, amt, voice_input)
                
                border_color = "#10b981" if tx_type == "INCOME" else "#f59e0b"
                st.markdown(f"""
                    <div style="background: rgba(15, 23, 42, 0.95); border: 2px solid {border_color}; padding: 16px; border-radius: 14px; margin-top: 15px;">
                        <p style="margin: 0; color: #f3f4f6; font-size: 16px; font-weight: bold; text-align: center;">
                            ✅ تم بنجاح تسجيل ({tx_category}) بقيمة ({amt} ج.م) كـ ({tx_type}) وترحيلها بدفتر القيود بدقة!
                        </p>
                    </div>
                """, unsafe_allow_html=True)
    else:
      st.error("الرجاء كتابة العملية أولاً.")
