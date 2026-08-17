import streamlit as st
import json
import google.generativeai as genai
from supabase import create_client, Client

# --- 1. إعدادات الصفحة ---
st.set_page_config(
    page_title="المحاسب الصوتي الذكي - للتجار",
    page_icon="🎙️",
    layout="centered"
)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif;
        direction: rtl;
        text-align: right;
    }
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
    }
    .card-box {
        background-color: #f8f9fa;
        border-right: 5px solid #2a5298;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. إعداد الاتصال بقاعدة البيانات و الـ AI ---
SUPABASE_URL = "https://nqindgywshroejrcxtky.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5xaW5kZ3l3c2hyb2VqcmN4dGt5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NjgxNTExMCwiZXhwIjoyMTAyMzkxMTEwfQ.g-jpUzajE_OxGNNjF2QCFZINWjRfGSPCSHR2rtOtUTE"

API_KEYS = [
    "AQ.Ab8RN6Jy0DoPtrUG0NWxTlQhxbFGLWNiX0jIEPUiFunbvoA1KA",
    "AQ.Ab8RN6KsmZlOVBitqBHl9MTKvhDTCrOkLckSZOLq5opLxEM97g",
    "AQ.Ab8RN6IOOQs421k9-f9CtpYl-b7mKWe1ID2e-VODE8WbGDLy0g",
    "AQ.Ab8RN6LDnxPObId4PxP_7RWvXtPSekj6ftHZ6AIwiVKyVQso5Q",
    "AQ.Ab8RN6IXSRGUETheaRkxa2JuolYCfGIL-888kwz8J9-OfWZ4Gw"
]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
USER_ID = "855633fe-a3a8-400d-a9ae-9fe439e658bd"

def process_command_ai(text: str):
    key = API_KEYS[0]
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    أنت محاسب ذكي لتطبيق تجاري مصري. قم بتحليل الجملة واستخرج منها البيانات بدقة:
    حدد الـ intent بدقة:
    - "ADD_TRANSACTION" (للبيع، الشراء، تسجيل إيراد، أو قبض)
    - "ADD_INVENTORY" (لإضافة بضاعة للمخزن)
    
    أرجع JSON نقي فقط بهذه الصيغة بدون أي markdown:
    {{
        "intent": "ADD_TRANSACTION",
        "type": "INCOME",
        "item_or_person": "اسم السلعة أو الشخص مثل لبن",
        "quantity": 1,
        "amount": الرقم الصحيح كقيمة مالية مستخرجة من النص
    }}
    النص: "{text}"
    """
    try:
        res = model.generate_content(prompt)
        clean = res.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except Exception as e:
        return {"intent": "ERROR", "message": str(e)}

# --- 3. تصميم واجهة Streamlit ---
st.markdown('<div class="main-header"><h1>🎙️ المحاسب الصوتي الذكي (للتاجر)</h1><p>تحدث أو اكتب معاملتك، وسيقوم المحاسب بتسجيلها وإدارتها فوراً!</p></div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["💼 لوحة المحاسب والصوت", "📦 إدارة المخزن", "🤝 بوابة عروض الجملة (Win-Win)"])

with tab1:
    st.subheader("🗣️ تحدث مع محاسبك الذكي")
    voice_input = st.text_input("اكتب أو قم بمحاكاة ما قاله التاجر صوتياً:", placeholder="مثال: بعت كيلو لبن ب 400 جنيه")
    
    if st.button("🚀 تنفيذ العملية", type="primary"):
        if voice_input:
            with st.spinner("🤖 جاري تحليل المعالجة وتسجيلها في السيرفر..."):
                data = process_command_ai(voice_input)
                intent = data.get("intent")
                
                if intent == "ADD_TRANSACTION":
                    amt = data.get("amount", 0)
                    tx_type = data.get("type", "INCOME")
                    item = data.get("item_or_person", "عام")
                    qty = data.get("quantity", 1)
                    
                    # حفظ مباشر في قاعدة بيانات Supabase
                    supabase.table("transactions").insert({
                        "type": tx_type,
                        "item_or_person": item,
                        "quantity": qty,
                        "amount": amt,
                        "raw_text": voice_input,
                        "created_by_user_id": USER_ID
                    }).execute()
                    
                    st.success(f"✅ تم بنجاح! تم تسجيل عملية لـ ({item}) بقيمة ({amt} ج.م) وحفظها في قاعدة البيانات.")
                else:
                    st.warning("⚠️ لم يتم فهم الطلب بدقة، حاول صياغته بشكل أبسط.")
        else:
            st.error("الرجاء إدخال نص الطلب أولاً.")

with tab2:
    st.subheader("📦 مخزن البضائع الحالي (متزامن مع Supabase)")
    try:
        inv_data = supabase.table("inventory").select("*").eq("created_by_user_id", USER_ID).execute().data
        if inv_data:
            for item in inv_data:
                st.markdown(f"""
                    <div class="card-box">
                        <b>الصنف:</b> {item.get('item_name')} | <b>الكمية:</b> {item.get('quantity')} | <b>السعر:</b> {item.get('cost_price')} ج.م
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("لا توجد أصناف حالياً، سيتم مزامنتها تلقائياً.")
    except Exception as e:
        st.error(f"خطأ في الاتصال بقاعدة البيانات: {e}")

with tab3:
    st.subheader("🤝 بوابة عروض الجملة الحصرية (توفير وأرباح مضاعفة)")
    st.markdown("عروض كبار الموردين المتاحة لمحلكم:")
    
    offers = [
        {"supplier": "شركة الأغذية الكبرى", "item": "كرتونة زيت توفير (12 زجاجة)", "market_price": 650, "our_offer": 600, "saving": "وفر 50 جنيه"},
        {"supplier": "مستودع المنهل", "item": "شوال سكر (50 كجم)", "market_price": 1800, "our_offer": 1700, "saving": "وفر 100 جنيه"},
    ]
    
    for off in offers:
        st.markdown(f"""
            <div class="card-box">
                <h4>🏷️ {off['item']}</h4>
                <p><b>المورد:</b> {off['supplier']}</p>
                <p><span style="text-decoration: line-through; color: gray;">السعر: {off['market_price']}</span> | <span style="color: green; font-weight: bold;">السعر الخاص: {off['our_offer']} ج.م</span></p>
                <p style="color: #d9534f;">🔥 {off['saving']}</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button(f"طلب العرض: {off['item']}", key=off['item']):
            st.success("🎉 تم إرسال طلبك للمورد بنجاح لتحقيق عمولتك وتوصيل البضاعة!")
