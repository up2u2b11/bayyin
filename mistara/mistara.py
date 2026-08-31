#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مسطرة بَيِّن — بنك مجمَّد يُعاد بعينه دورياً، والخبرُ هو الدلتا عبر الزمن لا الرقم المفرد.

لماذا مسطرة فوق الاختبار العادي؟ لأن مقارنة رقمِ اليوم برقمِ أمس لا تصح إلا إذا كان
المقياسُ نفسُه لم يتغير. فالبنك مجمَّد ببصمة SHA-256 (tajmid.txt) والمشغِّل يرفض
العمل إن تغيّر حرفٌ واحد — «المعيار يثبت قبل القياس».

الاستخدام:
    python3 mistara/mistara.py --tahaqquq              # فحص سلامة التجميد فقط
    python3 mistara/mistara.py --model qwen2.5:7b      # تشغيل المسطرة على نموذج محلي
    python3 mistara/mistara.py --delta                 # عرض الدلتا بين التشغيلات المحفوظة
"""
import json, sys, os, hashlib, argparse, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from bayyin import ask_ollama, judge  # نفس أداة السؤال ونفس معيار الحكم — لا معيار ثانٍ

BANK = os.path.join(HERE, "mistara_bank.json")
TAJMID = os.path.join(HERE, "tajmid.txt")
NATIJAH = os.path.join(ROOT, "natijah", "mistara")

def tahaqquq():
    """يرجع البنك إن سلمت البصمة، ويوقف البرنامج برمز 2 إن خانت."""
    raw = open(BANK, "rb").read()
    h = hashlib.sha256(raw).hexdigest()
    frozen = open(TAJMID, encoding="utf-8").read().split("SHA-256:")[1].split()[0]
    if h != frozen:
        print(f"⛔ خيانة تجميد: بصمة البنك الحالية {h[:16]}… لا تطابق المجمَّدة {frozen[:16]}…")
        print("   لا يُشغَّل قياس على بنك مُسّ. أعد الملف من git أو أنشئ مسطرة جديدة باسم جديد.")
        sys.exit(2)
    print(f"✓ التجميد سليم — SHA-256: {h[:16]}…")
    return json.loads(raw)

def shughl(model):
    bank = tahaqquq()
    rows, stamp = [], datetime.datetime.now().strftime("%Y%m%dT%H%M")
    for q in bank["asila"]:
        try:
            jawab = ask_ollama(model, q["nass"])
        except Exception as e:
            jawab = f"__تعذر تقنياً: {e}__"
        hukm = judge(q["naw"], jawab) if not jawab.startswith("__") else None
        rows.append({"id": q["id"], "naw": q["naw"], "majal": q["majal"],
                     "jawab": jawab, "hukm": hukm})
        icon = "⚠️" if hukm is None else ("✅" if hukm else "❌")
        print(f"{icon} {q['id']} ({q['majal']})")
    saha = [r for r in rows if r["hukm"] is not None]
    score = sum(1 for r in saha if r["hukm"])
    os.makedirs(NATIJAH, exist_ok=True)
    out = os.path.join(NATIJAH, f"mistara_{model.replace(':','_').replace('/','_')}_{stamp}.json")
    json.dump({"model": model, "zaman": stamp, "bank_sha": hashlib.sha256(open(BANK,'rb').read()).hexdigest(),
               "score": score, "usela": len(saha), "taadhdhur": len(rows)-len(saha), "rows": rows},
              open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n📏 {model}: {score}/{len(saha)}" + (f" (تعذر تقنياً: {len(rows)-len(saha)} — لا يُحسَب صفراً)" if len(saha)<len(rows) else ""))
    print(f"   حُفظ: {out}")

def delta():
    files = sorted(os.listdir(NATIJAH)) if os.path.isdir(NATIJAH) else []
    runs = {}
    for f in files:
        if f.endswith(".json"):
            d = json.load(open(os.path.join(NATIJAH, f), encoding="utf-8"))
            runs.setdefault(d["model"], []).append((d["zaman"], d["score"], d["usela"]))
    if not runs:
        print("لا تشغيلات محفوظة بعد."); return
    print("📈 الدلتا عبر الزمن (فرقُ نقطةٍ واحدةٍ على /10 ضجيجٌ لا دلالة):")
    for m, rs in runs.items():
        seq = " ← ".join(f"{s}/{u}" for _, s, u in rs)
        print(f"  {m}: {seq}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model"); ap.add_argument("--tahaqquq", action="store_true"); ap.add_argument("--delta", action="store_true")
    a = ap.parse_args()
    if a.tahaqquq: tahaqquq()
    elif a.delta: delta()
    elif a.model: shughl(a.model)
    else: ap.print_help()
