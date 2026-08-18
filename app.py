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
    last_error = ""
    for idx, key in enumerate(API_KEYS):
        try:
            genai.configure(api_key=key)
            # استخدام موديل Flash المدعوم في المكتبة
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            last_error = f"مفتاح #{idx+1} خطأ: {str(e)}"
            continue
    raise Exception(f"فشلت جميع المفاتيح. آخر خطأ: {last_error}")

st.title("المحاسب الذكي - Flash")
txt = st.text_input("أدخل المعاملة:")

if st.button("تنفيذ") and txt:
    p = f"""
    حلل النص التالي محاسبياً بدقة: "{txt}"
    - إذا وجد عددين (مثل 10 كراتين الكرتونة ب 120)، اضرب الكمية في السعر لاستخراج الإجمالي (10 * 120 = 1200).
    - حدد النوع (REVENUE للمبيعات / EXPENSE للمصاريف).
    أعطني النتيجة في شكل نقاط: النوع، الكمية، سعر الوحدة، الإجمالي.
    """
    try:
        result = run_flash(p)
        st.markdown(result)
    except Exception as err:
        st.error(err)
