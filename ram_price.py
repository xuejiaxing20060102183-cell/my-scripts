# -*- coding: utf-8 -*-
"""
ram_price.py —— 内存价格记录 & 买点判断小工具（纯本地，不联网）

用法：
    python ram_price.py add 1581 三星16G5600     # 记录一次价格
    python ram_price.py show                     # 看走势 + 该不该买
    python ram_price.py target 1000              # 设心理价位
    python ram_price.py chart                    # 生成走势图 PNG
"""
import json, os, sys, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "ram_price.json")
CHART = os.path.join(BASE, "ram_price_chart.png")
DEFAULT = {"target": 1000, "spec": "DDR5 SODIMM 16GB 5600", "records": []}

def load():
    if not os.path.exists(DATA):
        return dict(DEFAULT)
    try:
        with open(DATA, encoding="utf-8") as f:
            d = json.load(f)
        d.setdefault("target", DEFAULT["target"]); d.setdefault("records", [])
        return d
    except Exception:
        return dict(DEFAULT)

def save(d):
    with open(DATA, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def cmd_add(price, note=""):
    d = load()
    try:
        p = float(price)
    except ValueError:
        print("价格必须是数字，例如：add 1581 三星16G5600"); return
    d["records"].append({"date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                         "price": p, "note": note or d.get("spec", "")})
    save(d)
    print("已记录：%.0f 元  %s" % (p, note))
    verdict(d)

def cmd_target(price):
    d = load()
    try:
        d["target"] = float(price)
    except ValueError:
        print("目标价必须是数字"); return
    save(d)
    print("心理价位已设为 %.0f 元" % d["target"])

def verdict(d):
    r = d["records"]
    if not r:
        print("还没有记录，先用 add <价格> 记一条。"); return
    cur = r[-1]["price"]
    prices = [x["price"] for x in r]
    lo, hi = min(prices), max(prices)
    tgt = d.get("target", 1000)
    print("-" * 52)
    print("  当前记录价 : %.0f 元" % cur)
    print("  历史最低   : %.0f 元" % lo)
    print("  历史最高   : %.0f 元" % hi)
    print("  心理价位   : %.0f 元" % tgt)
    print("-" * 52)
    if cur <= tgt:
        print("  🎉 已到你的心理价位（低 %.0f 元），可以考虑下手了！" % (tgt - cur))
    elif len(r) < 3:
        print("  📝 记录还太少（%d 条），先多记几次才能判断走势。" % len(r))
        print("     参考：当前价距你的心理价位还差 %.0f 元（需降价 %.0f%%）。" % (cur - tgt, (cur - tgt) / cur * 100))
    elif lo > 0 and cur <= lo * 1.03:
        print("  👀 已经接近历史最低（高 %.1f%%），值得重点关注。" % ((cur / lo - 1) * 100))
    elif lo > 0:
        print("  ⏳ 建议继续等：比历史最低高 %.1f%%，距心理价位还差 %.0f 元。" % ((cur / lo - 1) * 100, cur - tgt))
    if len(r) >= 2:
        diff = cur - r[-2]["price"]
        arrow = "📈 涨了" if diff > 0 else ("📉 降了" if diff < 0 else "→ 没变")
        print("  与上次相比：%s %.0f 元" % (arrow, abs(diff)))

def cmd_show():
    d = load()
    r = d["records"]
    print("\n内存价格记录 · %s\n" % d.get("spec", ""))
    if not r:
        print("  （还没有记录）")
    else:
        print("  %-18s %10s   %s" % ("时间", "价格", "备注"))
        for x in r[-15:]:
            print("  %-18s %8.0f 元   %s" % (x["date"], x["price"], x.get("note", "")))
    verdict(d)
    print()

def cmd_chart():
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("需要 Pillow 库"); return
    d = load(); r = d["records"]
    if len(r) < 2:
        print("至少记录 2 次才能画走势图。"); return
    W, H, PAD = 1000, 560, 70
    img = Image.new("RGB", (W, H), (18, 20, 30))
    dr = ImageDraw.Draw(img)
    fp = "C:/Windows/Fonts/msyh.ttc"
    try:
        F = ImageFont.truetype(fp, 20); F2 = ImageFont.truetype(fp, 26)
    except Exception:
        F = F2 = ImageFont.load_default()
    prices = [x["price"] for x in r]
    lo, hi = min(prices + [d.get("target", 1000)]), max(prices)
    span = max(1.0, hi - lo)
    lo -= span * 0.12; hi += span * 0.12
    n = len(r)
    xs = [PAD + i * (W - 2 * PAD) / max(1, n - 1) for i in range(n)]
    ys = [H - PAD - (p - lo) / (hi - lo) * (H - 2 * PAD) for p in prices]
    # 坐标轴
    dr.line([PAD - 10, H - PAD, W - PAD + 10, H - PAD], fill=(90, 96, 120), width=2)
    dr.line([PAD - 10, PAD - 20, PAD - 10, H - PAD], fill=(90, 96, 120), width=2)
    # 目标价虚线
    ty = H - PAD - (d.get("target", 1000) - lo) / (hi - lo) * (H - 2 * PAD)
    for x in range(PAD - 10, W - PAD + 10, 16):
        dr.line([x, ty, x + 8, ty], fill=(120, 220, 140), width=2)
    dr.text((W - PAD - 190, ty - 28), "心理价位 %.0f 元" % d.get("target", 1000), font=F, fill=(120, 220, 140))
    # 折线
    dr.line(list(zip(xs, ys)), fill=(120, 170, 255), width=4, joint="curve")
    for x, y, it in zip(xs, ys, r):
        dr.ellipse([x - 6, y - 6, x + 6, y + 6], fill=(255, 200, 120))
        dr.text((x - 26, y - 34), "%.0f" % it["price"], font=F, fill=(255, 220, 160))
    dr.text((PAD, 18), "内存价格走势（元）", font=F2, fill=(235, 240, 255))
    dr.text((PAD, H - PAD + 16), r[0]["date"][:10], font=F, fill=(160, 170, 200))
    dr.text((W - PAD - 120, H - PAD + 16), r[-1]["date"][:10], font=F, fill=(160, 170, 200))
    img.save(CHART)
    print("走势图已保存：" + CHART)
    verdict(d)

def main():
    if sys.platform == "win32":
        try: sys.stdout.reconfigure(encoding="utf-8")
        except Exception: pass
    a = sys.argv[1:]
    if not a or a[0] in ("help", "-h", "--help"):
        print(__doc__); return
    c = a[0].lower()
    if c == "add" and len(a) >= 2: cmd_add(a[1], " ".join(a[2:]))
    elif c == "show" or c == "list": cmd_show()
    elif c == "target" and len(a) >= 2: cmd_target(a[1])
    elif c == "chart": cmd_chart()
    else: print(__doc__)

main()
