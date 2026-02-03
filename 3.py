import ollama
import os
from bs4 import BeautifulSoup
import re

# ======================
# الإعدادات (عدّل حسب احتياجاتك)
# ======================
INPUT_FILE = "111.html"        # اسم ملف الإدخال
OUTPUT_FILE = "output_ar.html"   # اسم ملف الإخراج
OLLAMA_MODEL = "translategemma:4b"    # النموذج المستخدم
TARGET_LANG = "العربية"          # اللغة الهدف

def translate_text(text, model=OLLAMA_MODEL):
    """ترجمة نص باستخدام Ollama مع معالجة الأخطاء"""
    if not text.strip():
        return text
    
    try:
        prompt = f"""ترجم النص التالي إلى {TARGET_LANG} مع الحفاظ على:
- المعنى الأصلي
- الأسماء العلمية والتقنية بالإنجليزية
- الرموز والأرقام كما هي
- لا تضف أي تعليقات أو شرح

النص:
"{text}"

الترجمة:"""
        
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.3}  # تقليل العشوائية للدقة
        )
        return response['message']['content'].strip()
    except Exception as e:
        print(f"⚠️ خطأ في الترجمة: {e}")
        return text

def extract_translatable_strings(soup):
    """استخراج النصوص القابلة للترجمة من عناصر HTML"""
    strings = []
    
    # العناصر التي تحتوي على نصوص رئيسية
    for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'td', 'th', 'span', 'div', 'a', 'button']):
        if tag.string and tag.string.strip() and not tag.find_parent(['script', 'style']):
            strings.append({
                'element': tag,
                'original': tag.string.strip(),
                'type': 'text'
            })
    
    # سمات تحتوي على نصوص (مثل alt, title)
    for tag in soup.find_all():
        for attr in ['alt', 'title', 'placeholder']:
            if tag.has_attr(attr) and tag[attr].strip():
                strings.append({
                    'element': tag,
                    'original': tag[attr].strip(),
                    'type': 'attr',
                    'attr': attr
                })
    
    return strings

def translate_html_file(input_path, output_path, model=OLLAMA_MODEL):
    """الوظيفة الرئيسية لترجمة ملف HTML"""
    print(f"✓ قراءة الملف: {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    strings_to_translate = extract_translatable_strings(soup)
    
    print(f"✓ تم العثور على {len(strings_to_translate)} جزء نصي للترجمة")
    
    # الترجمة (مع تجنب التكرار)
    cache = {}
    for i, item in enumerate(strings_to_translate, 1):
        original = item['original']
        
        # استخدام الكاش لتجنب ترجمة نفس النص مرتين
        if original in cache:
            translated = cache[original]
        else:
            print(f"[{i}/{len(strings_to_translate)}] ترجمة: {original[:50]}...")
            translated = translate_text(original, model)
            cache[original] = translated
        
        # إعادة الإدخال في العنصر
        if item['type'] == 'text':
            item['element'].string = translated
        elif item['type'] == 'attr':
            item['element'][item['attr']] = translated
    
    # حفظ الملف المترجم
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    
    print(f"\n✓ تم الحفظ في: {output_path}")
    print(f"✓ تمت ترجمة {len(cache)} نص فريد")

# ======================
# التشغيل
# ======================
if __name__ == "__main__":
    # تأكد من وجود الملف
    if not os.path.exists(INPUT_FILE):
        print(f"❌ الملف '{INPUT_FILE}' غير موجود!")
        print("ضع ملفك باسم 'input.html' في نفس مجلد هذا السكربت")
        exit(1)
    
    # تأكد من تشغيل خادم Ollama
    try:
        ollama.list()
    except:
        print("❌ Ollama غير قيد التشغيل!")
        print("افتح تطبيق Ollama أولاً، ثم أعد المحاولة")
        exit(1)
    
    translate_html_file(INPUT_FILE, OUTPUT_FILE, OLLAMA_MODEL)