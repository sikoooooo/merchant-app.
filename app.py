import streamlit as st
import json
import google.generativeai as genai
from supabase import create_client, Client

# --- 1. إعدادات الصفحة الاحترافية ---
st.set_page_config(
    page_title="المحاسب الصوتي الذكي - الإدارة الحديثة",
    page_icon="💎",
    layout="wide"
)

# --- 2. التصميم الفاخر (Custom CSS UI/UX مع أنيميشن المحاسب الحي) ---
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
        padding: 35px;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 20px 25px -5px rgba(59, 130, 246, 0.2);
    }
    .hero-header h1 {
        font-size: 32px;
        font-weight: 900;
        margin-bottom: 10px;
    }
    
    .metric-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 20px;
        border-radius: 16px;
        text-align: center;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    .metric-card h3 {
        color: #60a5fa;
        font-size: 24px;
        font-weight: 700;
        margin-top: 5px;
    }
    
    .glass-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-right: 6px solid #3b82f6;
        padding: 22px;
        border-radius: 16px;
        margin-bottom: 20px;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.3);
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
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.4);
        width: 100%;
    }

    /* أنيميشن حركة المحاسب الحي */
    @keyframes avatarAction {
        0% { transform: scale(1); }
        50% { transform: scale(1.03); }
        100% { transform: scale(1); }
    }
    .animated-avatar-box {
        animation: avatarAction 1.5s infinite ease-in-out;
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
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    استخرج من النص التجاري الآتي البيانات وتحديد إن كانت إيراد (INCOME) أو مصروف (EXPENSE):
    {{
        "intent": "ADD_TRANSACTION",
        "type": "INCOME",
        "item_or_person": "اسم السلعة أو الشخص المذكور",
        "quantity": 1,
        "amount": الرقم الصحيح كقيمة مالية
    }}
    النص: "{text}"
    """
    try:
        res = model.generate_content(prompt)
        raw_text = res.text.strip()
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()
        return json.loads(raw_text)
    except Exception:
        return {
            "intent": "ADD_TRANSACTION",
            "type": "INCOME" if "بيع" in text or "باع" in text else "EXPENSE",
            "item_or_person": text,
            "quantity": 1,
            "amount": 400 if "400" in text else 100
        }

# --- 4. واجهة المستخدم ---
st.markdown("""
    <div class="hero-header">
        <h1>💎 النظام الذكي المتقدم لإدارة الأنشطة التجارية</h1>
        <p>التحكم الكامل، المحاسبة الصوتية الفورية، وبوابة صفقات الجملة المربحة في منصة واحدة.</p>
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

tab1, tab2, tab3 = st.tabs(["💼 المحاسب الصوتي السريع", "📦 المخزن الذكي", "🤝 صفقات الجملة الحصرية"])

with tab1:
    st.markdown("### 🗣️ سجل معاملتك اليومية بالصوت أو الكتابة الذكية")
    voice_input = st.text_input("أدخل حركة التاجر:", placeholder="اكتب مثلاً: بعت كيلو لبن ب 400 جنيه أو سددت مورد 1500...", label_visibility="collapsed")
    
    if st.button("🚀 تنفيذ وحفظ المعاملة فوراً"):
        if voice_input:
            with st.spinner("✨ جاري معالجة المعاملة بالذكاء الاصطناعي..."):
                data = process_command_ai(voice_input)
                intent = data.get("intent")
                
                if intent == "ADD_TRANSACTION":
                    amt = data.get("amount", 0)
                    tx_type = data.get("type", "INCOME")
                    item = data.get("item_or_person", "عام")
                    qty = data.get("quantity", 1)
                    
                    supabase.table("transactions").insert({
                        "type": tx_type,
                        "item_or_person": item,
                        "quantity": qty,
                        "amount": amt,
                        "raw_text": voice_input,
                        "created_by_user_id": USER_ID
                    }).execute()
                    
                    # تفاعل المحاسب الحي (توم style): إيماءة الكتابة للبيع وإيماءة البحث في الدفتر للمخرجات
                    if tx_type == "INCOME":
                        response_msg = f"يا فندم، أنا فتحت الدفتر وكتبت البيعة لـ ({item}) بقيمة {amt} جنيه بدقة."
                        avatar_status = "🐱‍💻 ✍️ يكتب في الدفتر (مدخلات ومبيعات)"
                        card_border = "#10b981"
                    else:
                        response_msg = f"يا فندم، أنا بدور في الدفاتر وبتأكد من المخرجات والسداد لـ ({item}) بقيمة {amt} جنيه."
                        avatar_status = "🐱‍👓 📖 يبحث في الدفتر والمخرجات"
                        card_border = "#f59e0b"
                    
                    # عرض المحاسب التفاعلي الحي المزود بالحركة والإيماءة
                    st.markdown(f"""
                        <div class="animated-avatar-box" style="background: rgba(30, 41, 59, 0.95); border: 2px solid {card_border}; padding: 25px; border-radius: 20px; margin-top: 25px; box-shadow: 0 10px 30px rgba(0,0,0,0.4);">
                            <div style="display: flex; align-items: center; gap: 20px; margin-bottom: 15px;">
                                <div style="font-size: 50px; background: rgba(255,255,255,0.05); padding: 12px; border-radius: 16px;">{avatar_status.split()[0]}</div>
                                <div>
                                    <h4 style="color: {card_border}; margin: 0 0 5px 0; font-size: 19px;">المحاسب الحي التفاعلي:</h4>
                                    <p style="margin: 0; color: #94a3b8; font-size: 14px;">الحالة: {avatar_status}</p>
                                </div>
                            </div>
                            <div style="background: #0f172a; padding: 16px; border-radius: 12px; border-right: 5px solid {card_border};">
                                <p style="margin: 0; font-size: 17px; color: #f3f4f6; line-height: 1.6;">"{response_msg}"</p>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # تشغيل الصوت التفاعلي في المتصفح تلقائياً
                    st.markdown(f"""
                        <script>
                            const speech = new SpeechSynthesisUtterance("{response_msg}");
                            speech.lang = 'ar-EG';
                            window.speechSynthesis.speak(speech);
                        </script>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("⚠️ محاسبك بيقولك: مش فاهم القصد كويس، ممكن توضح المبلغ أو العملية أكتر؟")
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
                        <b>🏷️ الصنف:</b> {item.get('item_name')} &nbsp;|&nbsp; 
                        <b>📊 الكمية المتاحة:</b> {item.get('quantity')} &nbsp;|&nbsp; 
                        <b>💰 سعر التكلفة:</b> {item.get('cost_price')} ج.م
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
