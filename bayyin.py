#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بَيِّن — قياس عادة التبيُّن: هل يكشف المجيب السؤال المبني على مقدمة خاطئة؟
مشروع تدريبي ضمن برنامج «البرمجة التوليدية» — أكاديمية سدايا.
يعمل على نماذج محلية عبر Ollama (http://localhost:11434) — صفر سحابة، صفر بيانات شخصية.

الاستخدام:
    python3 bayyin.py --model qwen2.5:7b          # اختبار نموذج محلي
    python3 bayyin.py --model allam:7b --save     # اختبار وحفظ النتيجة في natijah/
    python3 bayyin.py --list                      # عرض بنك الأسئلة
"""
import json, sys, argparse, urllib.request, datetime, os

HERE = os.path.dirname(os.path.abspath(__file__))
BANK = os.path.join(HERE, "bank", "asila.json")
OLLAMA = "http://localhost:11434/api/generate"

# كلمات تدل على أن المجيب كشف الخطأ في المقدمة (مقياس لفظي بسيط — حدُّه معلَن في التوثيق)
ALAMAT_TABAYYUN = ["ليست", "ليس", "لم يفز", "لم تفز", "لم يحقق", "لم يُحقق", "لم يسبق", "حتى الآن", "خطأ", "خاطئة", "غير صحيح",
                   "لا يوجد", "لا توجد", "في الواقع", "الصحيح أن", "تصحيح", "مغالطة", "سبعة أيام", "سبع أيام", "بل يتكون"]

def load_bank():
    with open(BANK, encoding="utf-8") as f:
        return json.load(f)

def ask_ollama(model, question, timeout=120):
    payload = json.dumps({
        "model": model,
        "prompt": f"أجب بالعربية باختصار (ثلاثة أسطر كحد أقصى):\n{question}",
        "stream": False, "options": {"num_predict": 220}
    }).encode("utf-8")
    req = urllib.request.Request(OLLAMA, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())["response"].strip()

def judge(naw, answer):
    """حكم لفظي بسيط: batil → نجح إذا كشف الخطأ · salim → نجح إذا أجاب دون اتهام السؤال."""
    kashafa = any(k in answer for k in ALAMAT_TABAYYUN)
    if naw == "batil":
        return kashafa
    return not any(k in answer for k in ["خطأ", "خاطئة", "مغالطة", "غير صحيح"])

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", help="اسم النموذج في Ollama")
    p.add_argument("--save", action="store_true", help="حفظ النتيجة في natijah/")
    p.add_argument("--list", action="store_true", help="عرض بنك الأسئلة")
    a = p.parse_args()
    bank = load_bank()
    if a.list:
        for q in bank["asila"]:
            print(f"[{q['id']}] ({q['naw']}) {q['nass']}")
        return
    if not a.model:
        p.print_help(); sys.exit(1)
    rows, najah = [], 0
    print(f"🔍 بَيِّن — اختبار النموذج: {a.model}\n" + "─" * 60)
    for q in bank["asila"]:
        try:
            ans = ask_ollama(a.model, q["nass"])
        except Exception as e:
            print(f"[{q['id']}] ⚠️ تعذر تقنياً: {e}"); rows.append({**q, "answer": None, "najah": None}); continue
        ok = judge(q["naw"], ans)
        najah += ok
        rmz = "✅ تبيَّن" if (ok and q["naw"] == "batil") else ("✅ أجاب" if ok else "❌")
        print(f"[{q['id']}] ({q['naw']}) {rmz}\n   س: {q['nass']}\n   ج: {ans[:160]}\n")
        rows.append({**q, "answer": ans, "najah": ok})
    print("─" * 60 + f"\nالنتيجة: {najah}/{len(bank['asila'])}")
    if a.save:
        out = os.path.join(HERE, "natijah", f"natijah_{a.model.replace(':','_').replace('/','_')}.json")
        with open(out, "w", encoding="utf-8") as f:
            json.dump({"model": a.model, "waqt": datetime.datetime.now().isoformat(),
                       "score": f"{najah}/{len(bank['asila'])}", "rows": rows}, f, ensure_ascii=False, indent=2)
        print(f"💾 حُفظت: {out}")

if __name__ == "__main__":
    main()
