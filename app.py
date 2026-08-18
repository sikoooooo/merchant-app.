import os
import streamlit as st
import google.generativeai as genai

# المفاتيح الأربعة بالترتيب
API_KEYS = [
    "AQ.Ab8RN6KsmZlOVBitqBHl9MTKvhDTCrOkLckSZOLq5opLxEM97g",
    "AQ.Ab8RN6IOOQs421k9-f9CtpYl-b7mKWe1ID2e-VODE8WbGDLy0g",
    "AQ.Ab8RN6LDnxPObId4PxP_7RWvXtPSekj6ftHZ6AIwiVKyVQso5Q",
    "AQ.Ab8RN6IXSRGUETheaRkxa2JuolYCfGIL-888kwz8J9-OfWZ4Gw"
]

def run_flash(prompt):
    for key in API_KEYS:
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel("gemini-3.6-flash")
            return model.generate_content(prompt).text
        except:
            continue
    raise Exception("فشلت جميع المفاتيح")

st.title("المحاسب الذكي - Flash")
txt = st.text_input("أدخل المعاملة:")

if st.button("تنفيذ") and txt:
    p = f"""
    حلل النص التالي محاسبياً بدقة: "{txt}"
    - إذا وجد عددين (مثل 10 كراتين الكرتونة ب 120)، اضرب الكمية في السعر لاستخراج الإجمالي (10 * 120 = 1200).
    - حدد النوع (REVENUE للمبيعات / EXPENSE للمصاريف).
    أعطني النتيجة: النوع، الكمية، سعر الوحدة، الإجمالي.
    """
    st.markdown(run_flash(p))
