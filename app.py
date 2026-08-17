def process_command_ai(text: str):
    key = API_KEYS[0]
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    أنت محاسب تجاري محترف جداً في السوق المصري. افحص هذا النص التجاري بدقة واستخرج الآتي بصيغة JSON فقط:
    1. "type": حدد "INCOME" لو العملية بيع أو إيراد، أو "EXPENSE" لو العملية شراء، دفع أجور، أو مصروفات.
    2. "category": صنف الحركة بدقة لاختيار واحدة من هذه الأقسام: ("مشتريات بضاعة"، "أجور عمالة"، "مصروفات عامة").
    3. "item_or_person": استخرج اسم الصنف أو الخدمة فقط بدون الأفعال (يعني لو النص "دفعنا صنايعية تركيب بلاط 20000"، يكون اسم الصنف: "صنايعية تركيب بلاط" فقط بدون كلمة دفعنا أو المبلغ).
    4. "quantity": الكمية وافتراضها 1 إن لم تذكر.
    5. "amount": المبلغ المالي المذكور كأرقام صحيحة صريحة.
    
    أجب بصيغة JSON فقط بهذا الشكل وبدون أي نصوص أخرى:
    {{
        "intent": "ADD_TRANSACTION",
        "type": "INCOME أو EXPENSE",
        "category": "أجور عمالة أو مشتريات بضاعة",
        "item_or_person": "اسم الصنف الصافي",
        "quantity": 1,
        "amount": 0
    }}
    النص التجاري: "{text}"
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
            "category": "مصروفات عامة",
            "item_or_person": text,
            "quantity": 1,
            "amount": extracted_amount
        }
