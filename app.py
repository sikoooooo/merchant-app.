import uuid  # تأكد من استيراد مكتبة الـ uuid إذا لم تكن موجودة

def process_command_ai(text: str):
    key = API_KEYS[0]
    genai.configure(api_key=key)
    
    system_instruction = """
    أنت نظام محاسبي ذكي وخبير مالي مدرب على المعايير المحاسبية.
    مهمتك تحليل أي نص تجاري يدخله المستخدم وتصنيفه حصرياً إلى أحد البنود الآتية:
    1. "مصاريف تشغيلية" (مثل: شراء بضاعة، فواتير، إيجار، صيانة).
    2. "مصاريف إدارية" (مثل: مرتبات، أجور، أدوات مكتبية، رسوم).
    3. "مصاريف دعاية وإعلان" (مثل: إعلانات فيسبوك، حملات ترويجية، يافطات، تسويق).
    4. "مبيعات" (مثل: بيع بضاعة، قبض ثمن بضاعة).
    
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
    """
    تقوم بترحيل القيد المزدوج تلقائياً لجدول journal_entries 
    بناءً على دليل الحسابات الذي أنشأناه مسبقاً.
    """
    # ربط التصنيفات بأكواد الحسابات في Supabase (id الخاص بـ chart_of_accounts)
    # 110301 -> المدينون / النقدية (id=1 افتراضياً أو بنبحث عنه)
    # 410101 -> المبيعات الآجلة
    # 510101 -> المصروفات الإدارية / التشغيلية
    
    # للتسهيل المباشر، سنربطهم بالـ IDs الحقيقية بناءً على الجدول:
    # 410101 (المبيعات) | 510101 (المصروفات) | 110301 (النقدية/المدينون)
    
    # لجلب الـ IDs الفعلية من قاعدة البيانات ديناميكياً:
    try:
        accounts = supabase.table("chart_of_accounts").select("id, account_code").execute().data
        acc_map = {acc["account_code"]: acc["id"] for acc in accounts}
    except:
        return False

    id_cash = acc_map.get("110301")       # حساب النقدية / المدينون
    id_sales = acc_map.get("410101")      # حساب المبيعات
    id_expense = acc_map.get("510101")    # حساب المصروفات
    
    entry_id = str(uuid.uuid4())
    
    if category == "مبيعات":
        # من ح/ النقدية (مدين) إلى ح/ المبيعات (دائن)
        journal_data = [
            {"entry_id": entry_id, "account_id": id_cash, "debit": amount, "credit": 0.00, "description": description},
            {"entry_id": entry_id, "account_id": id_sales, "debit": 0.00, "credit": amount, "description": description}
        ]
    else:
        # من ح/ المصروفات (مدين) إلى ح/ النقدية (دائن)
        journal_data = [
            {"entry_id": entry_id, "account_id": id_expense, "debit": amount, "credit": 0.00, "description": description},
            {"entry_id": entry_id, "account_id": id_cash, "debit": 0.00, "credit": amount, "description": description}
        ]
        
    supabase.table("journal_entries").insert(journal_data).execute()
    return True
