
import streamlit as st
import json
import time
from datetime import datetime
import google.generativeai as genai
from supabase import create_client, Client

# --- 1. إعدادات الصفحة والتصميم العام ---
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

# --- 2. إعداد الاتصال والـ APIs ---
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
    model = genai.GenerativeModel('gemini-3.6-flash')
    
    prompt = f"""
    أنت محاسب ذكي لتطبيق تجاري. حدد هدف التاجر بدقة من الجملة:
    1. "ADD_INVENTORY" (إضافة بضاعة أو مخزون)
    2. "ADD_TRANSACTION" (عملية بيع، شراء، خدمة، أو دين)
    3. "QUERY_SALES" (استعلام عن المبيعات)
    4. "QUERY_DEBT" (استعلام عن ديون)
    
    أرجع JSON فقط بهذه الصيغة الدقيقة:
    {{
        "intent": "ADD_TRANSACTION",
        "item_name": "اسم صنف المخزن",
        "quantity": 1,
        "cost_price": 0,
        "category": "GOODS",
        "type": "INCOME",
        "item_or_person": "الشخص أو الشيء",
        "amount": 0
    }}
    النص: "{text}"
    أرجع JSON بدون ```json.
    """
    try:
        res = model.generate_content(prompt)
        clean = res.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except Exception as e:
        return {"intent": "ERROR", "message": str(e)}

st.markdown('<div class="main-header"><h1>🎙️ المحاسب الصوتي الذكي (للتاجر)</h1><p>تحدث أو اكتب معاملتك، وسيقوم المحاسب بتسجيلها وإدارتها فوراً!</p></div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["💼 لوحة المحاسب والصوت", "📦 إدارة المخزن", "🤝 بوابة عروض الجملة (Win-Win)"])

with tab1:
    st.subheader("🗣️ تحدث مع محاسبك الذكي")
    voice_input = st.text_input("اكتب أو قم بمحاكاة ما قاله التاجر صوتياً:", placeholder="مثال: بعت 3 كراتين زيت بـ 900 جنيه كاش / محمود عليه 500 جنيه آجل")
    
    if st.button("🚀 تنفيذ العملية", type="primary"):
        if voice_input:
            with st.spinner("🤖 جاري تحليل المعالجة عبر الذكاء الاصطناعي..."):
                data = process_command_ai(voice_input)
                intent = data.get("intent")
                
                if intent == "ADD_TRANSACTION":
                    amt = data.get("amount", 0)
                    tx_type = data.get("type", "INCOME")
                    item = data.get("item_or_person", "عام")
                    
                    supabase.table("transactions").insert({
                        "type": tx_type,
                        "item_or_person": item,
                        "quantity": data.get("quantity", 1),
                        "amount": amt,
                        "raw_text": voice_input,
                        "created_by_user_id": USER_ID
                    }).execute()
                    
                    st.success(f"✅ تم بنجاح! تم تسجيل العملية لـ ({item}) بقيمة ({amt} ج.م)")
                    
                elif intent == "ADD_INVENTORY":
                    item_name = data.get("item_name", "صنف")
                    qty = data.get("quantity", 1)
                    cost = data.get("cost_price", 0)
                    
                    supabase.table("inventory").insert({
                        "item_name": item_name,
                        "quantity": qty,
                        "cost_price": cost,
                        "created_by_user_id": USER_ID
                    }).execute()
                    
                    st.success(f"📦 تم إضافة الصنف '{item_name}' بكمية {qty} للمخزن بنجاح.")
                    
                elif intent == "QUERY_SALES":
                    goods = supabase.table("transactions").select("*").eq("created_by_user_id", USER_ID).execute().data
                    total = sum(t.get('amount', 0) for t in goods if t.get('type') == 'INCOME')
                    st.info(f"📊 إجمالي المبيعات والمقبوضات حتى الآن: {total} جنيه.")
                else:
                    st.warning("⚠️ لم يتم فهم الطلب بدقة، حاول صياغته بشكل أبسط.")
        else:
            st.error("الرجاء إدخال نص الطلب أولاً.")

with tab2:
    st.subheader("📦 مخزن البضائع الحالي")
    try:
        inv_data = supabase.table("inventory").select("*").eq("created_by_user_id", USER_ID).execute().data
        if inv_data:
            for item in inv_data:
                st.markdown(f"""
                    <div class="card-box">
                        <b>الصنف:</b> {item.get('item_name')} | <b>الكمية المتاحة:</b> {item.get('quantity')} قطعة | <b>سعر التكلفة:</b> {item.get('cost_price')} ج.م
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("لا توجد أصناف مسجلة في المخزن حالياً.")
    except Exception as e:
        st.error(f"خطأ في جلب بيانات المخزن: {e}")

with tab3:
    st.subheader("🤝 بوابة عروض الجملة الحصرية (توفير وأرباح مضاعفة)")
    st.markdown("بناءً على تحليلات استهلاك محلك، نقدم لك أفضل عروض كبار الموردين بأرخص سعر في السوق:")
    
    offers = [
        {"supplier": "شركة الأغذية الكبرى", "item": "كرتونة زيت توفير (12 زجاجة)", "market_price": 650, "our_offer": 600, "saving": "وفر 50 جنيه في الكرتونة"},
        {"supplier": "مستودع المنهل للمواد الغذائية", "item": "شوال سكر (50 كجم)", "market_price": 1800, "our_offer": 1700, "saving": "وفر 100 جنيه في الشوال"},
    ]
    
    for off in offers:
        st.markdown(f"""
            <div class="card-box">
                <h4>🏷️ {off['item']}</h4>
                <p><b>المورد المعتمد:</b> {off['supplier']}</p>
                <p><span style="text-decoration: line-through; color: gray;">السعر في السوق: {off['market_price']} ج.م</span> | <span style="color: green; font-weight: bold;">سعر العرض الخاص: {off['our_offer']} ج.م</span></p>
                <p style="color: #d9534f;">🔥 {off['saving']}</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button(f"طلب عرض: {off['item']}", key=off['item']):
            st.success("🎉 تم إرسال طلبك للمورد بنجاح! سيقوم مندوب التوصيل بالتواصل معك وشحن الطلب لمحلكم قريباً.")
