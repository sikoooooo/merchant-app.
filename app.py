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

# --- 2. التصميم الفاخر (UI/UX الاحترافي النظيف) ---
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
    
    .metric-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 18px;
        border-radius: 16px;
        text-align: center;
    }
    .metric-card h3 {
        color: #60a5fa;
        font-size: 22px;
        font-weight: 700;
        margin-top: 5px;
    }
    
    .glass-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-right: 6px solid #3b82f6;
        padding: 20px;
        border-radius: 16px;
        margin-bottom: 15px;
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

    @keyframes iconFloat {
        0%, 100% { transform: translateY(0px) scale(1); }
        50% { transform: translateY(-6px) scale(1.05); }
    }
    .accountant-3d-badge {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 20px;
        animation: iconFloat 3s infinite ease-in-out;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. بيانات الاتصال ---
SUPABASE_URL = "https://nqindgywshroejrcxtky.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5xaW5kZ3l3c2hyb2VqcmN4dGt5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NjgxNTExMCwiZXhwIjoyMTAyMzkxMTEwfQ.g-jpUzajE_OxGNNjF2QCFZINWjRfGSPCSHR2rtOtUTE"
API_KEYS = ["AQ.Ab8RN6Jy0DoPtrUG0NWxTlQhxbFGLWNiX0jIEPUiFunbvoA1KA"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
USER_ID = "855633fe-a3a8-400d-a9ae-9fe439e658bd"

def process_command_ai(text: str):
    key = API_KEYS[0]
    genai.configure(api_key=key)
    
    system_instruction = """
    أنت نظام محاسبي ذكي وخبير مالي مدرب على المعايير المحاسبية.
    مهمتك تحليل أي نص تجاري يدخله المستخدم واستخراج البيانات وتصنيفها كالتالي بحرص شديد:
    1. إذا كانت جملة تدل على دخل أو بيع أو قبض أموال (مثل: بيع، بعت، قبضت، باع، مبيعات): يجب أن تكون category حصرياً "مبيعات" و type تساوي "INCOME".
    2. إذا كانت مصروفات عامة أو شراء خامات أو إيجار أو فواتير: اختر حصرياً "مصاريف تشغيلية" و type تساوي "EXPENSE".
    3. إذا كانت مرتبات أو رسوم إدارية: اختر "مصاريف إدارية" و type تساوي "EXPENSE".
    4. إذا كانت إعلانات أو تسويق أو فيسبوك: اختر "مصاريف دعاية وإعلان" و type تساوي "EXPENSE".
    
    أجب بصيغة JSON فقط بدون أي نص إضافي.
    """
    
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        system_instruction=system_instruction
    )
    
    prompt = f"""
    حلل النص الآتي واستخرج الحقول المطلوبة:
    النص: "{text}"
    
    أجب فقط بصيغة JSON التالية:
    {{
        "intent": "ADD_TRANSACTION",
        "type": "INCOME أو EXPENSE",
        "category": "مصاريف تشغيلية أو مصاريف إدارية أو مصاريف دعاية وإعلان أو مبيعات",
        "item_or_person": "اسم الصنف أو الخدمة الصافي المستخلص",
        "quantity": 1,
        "amount": 0
    }}
    """
    
    try:
        res = model.generate_content(prompt)
        raw_text = res.text.strip()
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()
        
        data = json.loads(raw_text)
        
        if not data.get("amount") or data.get("amount") == 0:
            numbers = re.findall(r'\d+', text)
            if numbers:
                data["amount"] = int(numbers[-1])
                
        return data
        
    except Exception:
        is_sale = any(w in text for w in ["بيع", "بعت", "باع", "قبضت"])
        numbers = re.findall(r'\d+', text)
        extracted_amount = int(numbers[-1]) if numbers else 0
        
        return {
            "intent": "ADD_TRANSACTION",
            "type": "INCOME" if is_sale else "EXPENSE",
            "category": "مبيعات" if is_sale else "مصاريف تشغيلية",
            "item_or_person": text,
            "quantity": 1,
            "amount": extracted_amount
        }

def post_journal_entry(category, amount, description):
    try:
        # جلب جميع الحسابات من جدول chart_of_accounts
        accounts = supabase.table("chart_of_accounts").select("id, account_code, account_name").execute().data
        
        # إنشاء قاموس ذكي (Mapping) يربط الكود أو الاسم بالـ ID الحقيقي في الداتا بيز
        acc_map = {}
        for acc in accounts:
            acc_map[str(acc.get("account_code"))] = acc.get("id")
            acc_map[str(acc.get("account_name"))] = acc.get("id")
            
    except Exception as e:
        print(f"Error fetching accounts: {e}")
        return False

    # التقاط الـ IDs الحقيقية ديناميكياً بناءً على ما هو موجود فعلياً في الجدول
    id_cash = acc_map.get("110301") or acc_map.get("المدينون (حسابات القبض)") or 1
    id_sales = acc_map.get("410101") or acc_map.get("المبيعات الآجلة") or 4
    id_expense = acc_map.get("510101") or acc_map.get("المصروفات الإدارية والعمومية") or 5
    
    # لو التصنيف "مصاريف دعاية وإعلان"، ممكن نوجهه على حساب المصروفات أو نخليه يروح للصح
    entry_id = str(uuid.uuid4())
    
    if category == "مبيعات":
        # من ح/ النقدية أو المدينون (مدين) إلى ح/ المبيعات (دائن)
        journal_data = [
            {"entry_id": entry_id, "account_id": id_cash, "debit": amount, "credit": 0.00, "description": description},
            {"entry_id": entry_id, "account_id": id_sales, "debit": 0.00, "credit": amount, "description": description}
        ]
    else:
        # لأي مصروف (تشغيلي، إداري، أو دعاية وإعلان): من ح/ المصروفات إلى ح/ النقدية
        journal_data = [
            {"entry_id": entry_id, "account_id": id_expense, "debit": amount, "credit": 0.00, "description": description},
            {"entry_id": entry_id, "account_id": id_cash, "debit": 0.00, "credit": amount, "description": description}
        ]
        
    supabase.table("journal_entries").insert(journal_data).execute()
    return True
# --- 4. واجهة المستخدم ---
st.markdown("""
    <div class="hero-header">
        <h1>💎 النظام الذكي المتقدم لإدارة الأنشطة التجارية</h1>
        <p>المحاسب الصوتي التفاعلي، إدارة المخزن، وبوابة صفقات الجملة المربحة.</p>
    </div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown('<div class="metric-card"><span>إجمالي مبيعات اليوم</span><h3>12,450 ج.م</h3></div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="metric-card"><span>عدد الحركات المسجلة</span><h3>28 حركة</h3></div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="metric-card"><span>أرباح صفقات الجملة</span><h3>1,800 ج.م</h3></div>', unsafe_allow_html=True)

st.write("---")

tab1, tab2, tab3 = st.tabs(["💼 المحاسب الذكي", "📦 المخزن الذكي", "🤝 صفقات الجملة الحصرية"])

with tab1:
    st.markdown("""
        <div class="accountant-3d-badge">
            <div style="background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); width: 90px; height: 90px; border-radius: 50%; display: flex; align-items: center; justify-content: center; box-shadow: 0 10px 25px rgba(37, 99, 235, 0.5); border: 2px solid rgba(255,255,255,0.2);">
                <span style="font-size: 40px;">📊</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🗣️ سجل معاملتك التجارية بالصوت أو الكتابة:")
    voice_input = st.text_input("أدخل حركة التاجر:", placeholder="مثال: عملنا حملة دعاية على الفيس ب 500 جنية", label_visibility="collapsed")
    
    if st.button("🚀 تنفيذ وحفظ المعاملة"):
        if voice_input:
            with st.spinner("✨ جاري تحليل المعاملة بالذكاء الاصطناعي المحاسبي..."):
                data = process_command_ai(voice_input)
                intent = data.get("intent")
                
                if intent == "ADD_TRANSACTION":
                    amt = data.get("amount", 0)
                    tx_type = data.get("type", "EXPENSE")
                    tx_category = data.get("category", "مصاريف تشغيلية")
                    item = data.get("item_or_person", "عام")
                    qty = data.get("quantity", 1)
                    
                    supabase.table("transactions").insert({
                        "type": tx_type,
                        "item_or_person": item,
                        "quantity": qty,
                        "amount": amt,
                        "raw_text": voice_input,
                        "created_by_user_id": USER_ID,
                        "category": tx_category
                    }).execute()
                    
                    post_journal_entry(tx_category, amt, voice_input)
                    
                    if tx_type == "INCOME":
                        confirm_msg = f"✅ تم بنجاح! تسجيل مبيعات لـ ({item}) بقيمة ({amt} ج.م) وترحيله بدفتر القيود."
                        border_color = "#10b981"
                    else:
                        confirm_msg = f"✅ تم بنجاح! تسجيل ({tx_category}) لـ ({item}) بقيمة ({amt} ج.م) وترحيله بدفتر القيود."
                        border_color = "#f59e0b"
                    
                    st.markdown(f"""
                        <div style="background: rgba(15, 23, 42, 0.95); border: 2px solid {border_color}; padding: 16px; border-radius: 14px; margin-top: 15px;">
                            <p style="margin: 0; color: #f3f4f6; font-size: 15px; font-weight: bold; text-align: center;">{confirm_msg}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown(f"""
                        <script>
                            const speech = new SpeechSynthesisUtterance("{confirm_msg}");
                            speech.lang = 'ar-EG';
                            window.speechSynthesis.speak(speech);
                        </script>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("⚠️ عذراً، لم أستطع فهم العملية بدقة. جرب صياغة أبسط.")
        else:
            st.error("الرجاء كتابة العملية أولاً.")

with tab2:
    st.markdown("### 📦 أرصدة وحركات المخزن الحالية")
    try:
        inv_data = supabase.table("inventory").select("*").eq("created_by_user_id", USER_ID).execute().data
        if inv_data:
            for item in inv_data:
                st.markdown(f"""
                    <div class="glass-card">
                        <b>🏷️ الصنف:</b> {item.get('item_name')} &nbsp;|&nbsp; <b>📊 الكمية:</b> {item.get('quantity')} &nbsp;|&nbsp; <b>💰 التكلفة:</b> {item.get('cost_price')} ج.م
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("المخزن فارغ حالياً، سيتم تحديثه تلقائياً مع العمليات.")
    except Exception as e:
        st.error(f"خطأ في جلب بيانات المخزن: {e}")

with tab3:
    st.markdown("### 🤝 صفقات كبار الموردين (Win-Win)")
    offers = [
        {"supplier": "شركة الأغذية الكبرى", "item": "كرتونة زيت توفير (12 زجاجة)", "market_price": 650, "our_offer": 600, "saving": "وفر 50 جنيه"},
        {"supplier": "مستودع المنهل", "item": "شوال سكر فاخر (50 كجم)", "market_price": 1800, "our_offer": 1700, "saving": "وفر 100 جنيه"},
    ]
    
    for off in offers:
        st.markdown(f"""
            <div class="glass-card">
                <h3 style="color: #60a5fa; margin-bottom: 5px;">{off['item']}</h3>
                <p style="margin: 2px 0;"><b>المورد المعتمد:</b> {off['supplier']}</p>
                <p style="margin: 2px 0;">
                    <span style="text-decoration: line-through; color: #94a3b8;">السعر بالسوق: {off['market_price']} ج.م</span> &nbsp;|&nbsp; 
                    <span style="color: #4ade80; font-weight: bold; font-size: 18px;">سعر الجملة: {off['our_offer']} ج.م</span>
                </p>
                <p style="color: #f87171; font-weight: 600; margin-top: 5px;">🔥 {off['saving']}</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button(f"طلب صفقة: {off['item']}", key=off['item']):
            st.success("🚀 تم إرسال طلب الصفقة للمورد وتفعيل أرباح العرض لمحلكم بنجاح!")
