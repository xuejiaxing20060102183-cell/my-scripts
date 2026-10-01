# -*- coding: utf-8 -*-
"""
dsp_practice.py —— 双拼打字练习器 v2（小鹤键位提示 + 限时挑战 + 错题本 + 成绩曲线）

基础用法：
    python dsp_practice.py                     # 混合模式 20 题（带键位提示）
    python dsp_practice.py --mode 词 --n 15
    python dsp_practice.py --no-hint           # 关提示（实战）
    python dsp_practice.py --mode 段           # 长段落跟打
    python dsp_practice.py --keys              # 小鹤键位表
    python dsp_practice.py --stats             # 历史成绩

新增：
    python dsp_practice.py --timed 60          # 限时挑战：60 秒内打尽可能多
    python dsp_practice.py --review 20         # 错题重练（专练你打错的字）
    python dsp_practice.py --chart             # 生成成绩趋势图 PNG
    python dsp_practice.py --mistakes          # 看错题本
"""
import argparse, csv, json, os, random, sys, time

BASE = os.path.dirname(os.path.abspath(__file__))
HIST = os.path.join(BASE, "typing_history.csv")
MIST = os.path.join(BASE, "typing_mistakes.json")

# ============ 小鹤双拼键位表（来源：Rime 官方 double_pinyin_flypy 方案）============
INITIALS = ["zh", "ch", "sh", "b", "p", "m", "f", "d", "t", "n", "l", "g", "k",
            "h", "j", "q", "x", "r", "z", "c", "s", "y", "w"]
FINALS = {
    "a": "a", "o": "o", "e": "e", "i": "i", "u": "u", "v": "v", "ü": "v",
    "ai": "d", "ei": "w", "ui": "v", "ao": "c", "ou": "z", "iu": "q", "ie": "p",
    "ue": "t", "ve": "t", "üe": "t", "er": "r",
    "an": "j", "en": "f", "in": "b", "un": "y", "ün": "y", "vn": "y",
    "ang": "h", "eng": "g", "ing": "k", "ong": "s", "iong": "s",
    "ian": "m", "iang": "l", "uang": "l", "uan": "r", "ua": "x", "ia": "x",
    "iao": "n", "uo": "o", "uai": "k", "üan": "r", "van": "r",
}

def encode(syllable):
    s = syllable.lower().replace("ü", "v").strip()
    if s[0] in "aoe":
        if s == "er":
            return ("e", "r")
        return (s[0], FINALS.get(s, "?"))
    ini = next((i for i in INITIALS if s.startswith(i)), None)
    if ini is None:
        return ("?", "?")
    fin = s[len(ini):]
    if ini in ("j", "q", "x", "y") and fin == "u":
        fin = "v"
    key1 = {"zh": "v", "ch": "i", "sh": "u"}.get(ini, ini[0])
    return (key1, FINALS.get(fin, "?"))

def hint_of(pinyin):
    return " ".join("".join(encode(s)) for s in pinyin.split())

# ============ 语料库 ============
CHARS = [("我","wo"),("你","ni"),("他","ta"),("的","de"),("是","shi"),("不","bu"),("了","le"),
         ("在","zai"),("有","you"),("人","ren"),("这","zhe"),("那","na"),("大","da"),("小","xiao"),
         ("中","zhong"),("国","guo"),("天","tian"),("地","di"),("水","shui"),("火","huo"),("山","shan"),
         ("月","yue"),("日","ri"),("年","nian"),("时","shi"),("分","fen"),("秒","miao"),("好","hao"),
         ("学","xue"),("习","xi"),("电","dian"),("脑","nao"),("键","jian"),("盘","pan"),("打","da"),
         ("字","zi"),("快","kuai"),("慢","man"),("对","dui"),("错","cuo")]
WORDS = [("学习","xue xi"),("电脑","dian nao"),("打字","da zi"),("键盘","jian pan"),("双拼","shuang pin"),
         ("输入法","shu ru fa"),("练习","lian xi"),("速度","su du"),("准确","zhun que"),("记忆","ji yi"),
         ("时间","shi jian"),("今天","jin tian"),("明天","ming tian"),("现在","xian zai"),("我们","wo men"),
         ("朋友","peng you"),("学校","xue xiao"),("专业","zhuan ye"),("计算机","ji suan ji"),("科学","ke xue"),
         ("技术","ji shu"),("网络","wang luo"),("程序","cheng xu"),("代码","dai ma"),("文件","wen jian"),
         ("系统","xi tong"),("硬盘","ying pan"),("屏幕","ping mu"),("中文","zhong wen"),("努力","nu li"),
         ("生活","sheng huo"),("工作","gong zuo"),("问题","wen ti"),("方法","fang fa"),("结果","jie guo"),
         ("经验","jing yan"),("效率","xiao lv"),("训练","xun lian"),("进步","jin bu"),("习惯","xi guan"),
         ("坚持","jian chi"),("目标","mu biao"),("计划","ji hua"),("思考","si kao"),("理解","li jie"),
         ("知识","zhi shi"),("能力","neng li"),("发展","fa zhan"),("未来","wei lai"),("改变","gai bian")]
SENTENCES = ["今天天气很好，我们一起去跑步吧。","我正在练习双拼打字，速度越来越快了。",
    "计算机科学与技术是我最喜欢的专业。","人工智能正在改变我们的生活方式。",
    "这个程序的功能是把积分转换成接口。","深夜的街道上，一个人安静地走着。",
    "学习新的技能需要耐心和坚持。","他每天早上都会读半个小时的英语。",
    "我打算把这台电脑升级一下内存。","国庆假期我准备整理一下电脑里的文件。",
    "你最想去哪个城市旅行呢？","请把这段代码复制到新的文件里。",
    "天气转凉了，记得多穿一件外套。","我们约在图书馆门口见面吧。",
    "这道题的解法比我想象的简单。","每次跑步之后我都觉得特别轻松。",
    "双拼的键位需要反复练习才能记住。","月亮很亮，星星也很清楚。",
    "加油，你一定可以做到的！","坚持练习，总有一天会变成打字高手。",
    "把复杂的问题拆成小块，就会容易很多。","每天进步一点点，一年后就是巨大的变化。",
    "不要害怕犯错，错误是最好的老师。","代码写得越清楚，维护起来就越省力。",
    "窗外的雨下了一整夜，早上空气很清新。","他喜欢在安静的午后读一本好书。",
    "这个城市的夜景比白天更漂亮。","时间过得真快，转眼就到秋天了。",
    "只要能坚持下去，结果一定不会太差。","先想清楚再动手，能省下很多返工的时间。"]
PARAS = ["学习一门新技术，最重要的不是天赋，而是方法。先把目标拆成小步骤，每天完成一点点，积累起来就是巨大的进步。遇到问题不要慌，先自己查资料，再向别人请教，这样印象最深刻。",
         "打字速度的提升有三个阶段：第一是记住键位，第二是不用看键盘，第三是形成肌肉记忆。前两个阶段最痛苦，但只要坚持两周，就会明显感觉到轻松。到第三阶段，手指会自己找到位置，你只需要思考要打什么内容。",
         "计算机的世界里，很多东西都是分层的。硬件在最下面，操作系统在上面，再往上是各种程序和应用。理解了这个结构，学习任何新技术的时候，你都能快速找到它所在的层，知道它依赖谁、又被谁依赖。",
         "写作和编程有一个共同点：先完成，再完美。很多人卡在第一句话或者第一行代码上，其实最好的做法是先写出一个能跑的粗糙版本，然后再一点点修改。改的过程比空想快得多。",
         "保持专注比延长工作时间更有效。与其连续坐四个小时，不如分成四个一小时，中间休息十分钟。人的注意力本来就是波动的，顺着它的节奏安排任务，效率会高很多。"]
CORPUS = {"字": CHARS, "词": WORDS, "句": [(s, "") for s in SENTENCES], "段": [(p, "") for p in PARAS]}

# ============ 界面 ============
def enable_ansi():
    if os.name == "nt":
        try:
            import ctypes; k = ctypes.windll.kernel32
            k.SetConsoleMode(k.GetStdHandle(-11), 7)
        except Exception:
            pass
G, R, Y, C, DIM, RST = "\033[32m", "\033[31m", "\033[33m", "\033[36m", "\033[2m", "\033[0m"

def load_mist():
    if os.path.exists(MIST):
        try:
            with open(MIST, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_mist(m):
    with open(MIST, "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=1)

def diff(target, typed):
    out, ok, wrong = [], 0, []
    for i, ch in enumerate(target):
        if i < len(typed) and typed[i] == ch:
            out.append(G + ch + RST); ok += 1
        else:
            got = typed[i] if i < len(typed) else "∅"
            out.append(R + "[" + ch + "←" + got + "]" + RST)
            wrong.append(ch)
    if len(typed) > len(target):
        out.append(R + "[多" + typed[len(target):] + "]" + RST)
    return ok, "".join(out), wrong

def show_keys():
    print("\n小鹤双拼键位表（Rime 官方方案）\n")
    rows = [("Q","iu"),("W","ei"),("E","e"),("R","uan"),("T","üe"),("Y","un"),("U","u/sh"),("I","i/ch"),("O","o/uo"),("P","ie"),
            ("A","a"),("S","ong/iong"),("D","ai"),("F","en"),("G","eng"),("H","ang"),("J","an"),("K","ing/uai"),("L","uang/iang"),
            ("Z","ou"),("X","ua/ia"),("C","ao"),("V","ui/ü/zh"),("B","in"),("N","iao"),("M","ian")]
    for i in range(0, len(rows), 10):
        print("  " + "   ".join("%s=%-10s" % (k, v) for k, v in rows[i:i + 10]))
    print("\n  零声母：首字母 + 韵母键    安 a+j   昂 a+h   欧 o+z   恩 e+f   爱 a+d")
    print("  zh/ch/sh 占一键：V=zh  I=ch  U=sh\n")

def save_hist(mode, cnt, chars, cpm, acc, best):
    with open(HIST, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        if not os.path.exists(HIST) or os.path.getsize(HIST) == 0:
            w.writerow(["时间", "模式", "题数", "字数", "字每分", "正确率", "最快单题"])
        w.writerow([time.strftime("%Y-%m-%d %H:%M"), mode, cnt, chars, "%.1f" % cpm, "%.1f" % acc, "%.1f" % best])

# ============ 模式 1：常规练习 ============
def run(mode, n, hint):
    if mode == "混合":
        k = max(1, n // 3 + 1)
        parts = [("字", random.sample(CHARS, min(len(CHARS), k))),
                 ("词", random.sample(WORDS, min(len(WORDS), k))),
                 ("句", random.sample(CORPUS["句"], min(len(SENTENCES), max(0, n - 2 * k))))]
        pool = []
        for lvl, items in parts:
            pool += [(lvl, t, p) for (t, p) in items]
        random.shuffle(pool)
    else:
        pool = [(mode, t, p) for (t, p) in random.sample(CORPUS[mode], min(len(CORPUS[mode]), n))]
    pool = pool[:n]

    print(C + "\n=== 开始！共 %d 题（输入 q 跳过，:quit 结束）===\n" % len(pool) + RST)
    mist = load_mist()
    tc = tt = tok = 0
    results = []
    for idx, (lvl, target, pinyin) in enumerate(pool, 1):
        print("%s[%d/%d] (%s)%s  %s%s%s" % (Y, idx, len(pool), lvl, RST, C, target, RST))
        if hint and pinyin:
            marks = ["%s%s%s %s·%s" % (DIM, ch, RST, encode(py)[0], encode(py)[1]) for ch, py in zip(target, pinyin.split())]
            print("      " + "   ".join(marks))
        t0 = time.perf_counter()
        try:
            typed = input("  > ").rstrip("\n")
        except (EOFError, KeyboardInterrupt):
            print(); break
        dt = time.perf_counter() - t0
        if typed.strip() == ":quit":
            break
        if typed.strip().lower() == "q":
            print(DIM + "      跳过" + RST); continue
        ok, marked, wrong = diff(target, typed)
        cpm = len(target) / dt * 60 if dt > 0 else 0
        print("      " + marked)
        print("      %s%d/%d 字正确 · %.1f 字/分 · 用时 %.1f 秒%s\n" %
              (G if ok == len(target) else Y, ok, len(target), cpm, dt, RST))
        for w in wrong:
            mist[w] = mist.get(w, 0) + 1
        results.append((len(target), dt, ok, cpm))
        tc += len(target); tt += dt; tok += ok
    save_mist(mist)
    if not results:
        print("没有有效记录。"); return
    cpm = tc / tt * 60
    acc = tok / tc * 100
    best = max(r[3] for r in results)
    print(C + "=" * 46 + RST)
    print("  本轮：%d 题 · %d 字 · 平均 %.1f 字/分 · 正确率 %.1f%% · 最快单题 %.1f" %
          (len(results), tc, cpm, acc, best))
    print(C + "=" * 46 + RST)
    save_hist(mode, len(results), tc, cpm, acc, best)
    print(DIM + "  已记录。打错的字已存入错题本（--mistakes 查看，--review 重练）" + RST)

# ============ 模式 2：限时挑战 ============
def timed(seconds):
    print(C + "\n=== 限时挑战：%d 秒 ===" % seconds + RST)
    print(DIM + "  规则：连续出题，打对/打错都自动进入下一题，时间到就结算。" + RST)
    input(DIM + "  准备好按回车开始..." + RST)
    pool_all = [(t, p) for (t, p) in CHARS] + [(t, p) for (t, p) in WORDS] + [(t, "") for (t, _) in CORPUS["句"]]
    mist = load_mist()
    deadline = time.time() + seconds
    tc = tok = 0; cnt = 0; wrong_all = []
    print()
    while time.time() < deadline:
        target, pinyin = random.choice(pool_all)
        left = int(deadline - time.time())
        print("%s[%2d 秒]%s %s%s%s" % (Y, left, RST, C, target, RST))
        if pinyin:
            marks = ["%s%s%s %s·%s" % (DIM, ch, RST, encode(py)[0], encode(py)[1]) for ch, py in zip(target, pinyin.split())]
            print("      " + "   ".join(marks))
        try:
            typed = input("  > ").rstrip("\n")
        except (EOFError, KeyboardInterrupt):
            break
        if typed.strip() == ":quit":
            break
        if time.time() > deadline:
            print(DIM + "  （时间到）" + RST); break
        ok, marked, wrong = diff(target, typed)
        tc += len(target); tok += ok; cnt += 1
        wrong_all += wrong
        for w in wrong:
            mist[w] = mist.get(w, 0) + 1
        print("      " + marked + "   %s%d/%d%s" % (G if ok == len(target) else Y, ok, len(target), RST))
    save_mist(mist)
    if cnt == 0:
        print("没有有效记录。"); return
    cpm = tc / seconds * 60
    acc = tok / tc * 100
    print(C + "\n" + "=" * 46 + RST)
    print("  ⏱ %d 秒挑战结果：%d 题 · %d 字 · **%.1f 字/分** · 正确率 %.1f%%" % (seconds, cnt, tc, cpm, acc))
    print(C + "=" * 46 + RST)
    save_hist("限时%d秒" % seconds, cnt, tc, cpm, acc, cpm)
    if wrong_all:
        top = sorted(set(wrong_all), key=lambda x: -wrong_all.count(x))[:8]
        print(DIM + "  本次打错的字：" + " ".join(top) + RST)

# ============ 模式 3：错题重练 ============
def review(n):
    mist = load_mist()
    if not mist:
        print("错题本是空的——先练几轮吧！"); return
    top = sorted(mist.items(), key=lambda x: -x[1])[:n]
    print(C + "\n=== 错题重练（共 %d 个）===" % len(top) + RST)
    print(DIM + "  这些都是你历史上打错最多的字。" + RST)
    pairs = {t: p for t, p in CHARS}
    pool = [(t, pairs.get(t, "")) for t, _ in top if t in pairs]
    if not pool:
        print("错题本里的字不在当前语料中。"); return
    random.shuffle(pool)
    tc = tt = tok = 0; results = []
    for idx, (t, py) in enumerate(pool, 1):
        print("%s[%d/%d]%s  %s%s%s    %s(错 %d 次)%s" % (Y, idx, len(pool), RST, C, t, RST, DIM, mist[t], RST))
        if py:
            a, b = encode(py)
            print("      " + DIM + t + " " + a + "·" + b + RST)
        t0 = time.perf_counter()
        try:
            typed = input("  > ").rstrip("\n")
        except (EOFError, KeyboardInterrupt):
            break
        dt = time.perf_counter() - t0
        if typed.strip() == ":quit":
            break
        ok, marked, wrong = diff(t, typed)
        tc += len(t); tt += dt; tok += ok
        results.append(dt)
        if ok == len(t):
            mist[t] = max(0, mist[t] - 1)          # 打对就减一次错
            print("      " + G + "✅ 对了（错题本 -1）" + RST)
        else:
            mist[t] = mist.get(t, 0) + 1
            print("      " + marked + RST)
    save_mist(mist)
    if tt > 0:
        print(C + "\n  重练完成：%.1f 字/分 · 正确率 %.1f%%" % (tc / tt * 60, tok / tc * 100) + RST)

def show_mistakes():
    mist = load_mist()
    if not mist:
        print("错题本是空的。"); return
    print("\n=== 错题本（按出错次数）===\n")
    for t, c in sorted(mist.items(), key=lambda x: -x[1])[:30]:
        print("  %s  错 %d 次" % (t, c))
    print("\n  共 %d 个不同的字。用 --review 20 专门重练。" % len(mist))

# ============ 统计与图表 ============
def stats():
    if not os.path.exists(HIST):
        print("还没有记录，先练一轮吧。"); return
    with open(HIST, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    print("\n最近 10 次练习：\n")
    print("  %-17s %-8s %-6s %-9s %-7s" % ("时间", "模式", "字数", "字/分", "正确率"))
    for r in rows[-10:]:
        print("  %-17s %-8s %-6s %-9s %-7s" % (r["时间"], r["模式"], r["字数"], r["字每分"], r["正确率"]))
    best = max(rows, key=lambda r: float(r["字每分"]))
    print("\n  历史最佳：%s 字/分（%s，正确率 %s）" % (best["字每分"], best["时间"], best["正确率"]))
    first, last = rows[0], rows[-1]
    print("  进步：%s → %s 字/分（%s → %s）" % (first["字每分"], last["字每分"], first["时间"], last["时间"]))
    if len(rows) >= 3:
        a = sum(float(r["字每分"]) for r in rows[-3:]) / 3
        print("  最近 3 次平均：%.1f 字/分\n" % a)

def chart():
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("需要 Pillow 库"); return
    if not os.path.exists(HIST):
        print("还没有记录。"); return
    with open(HIST, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if len(rows) < 2:
        print("至少练 2 轮才能画曲线。"); return
    W, H, PAD = 1000, 560, 70
    img = Image.new("RGB", (W, H), (18, 20, 30))
    dr = ImageDraw.Draw(img)
    try:
        F = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 19)
        F2 = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 26)
    except Exception:
        F = F2 = ImageFont.load_default()
    cpm = [float(r["字每分"]) for r in rows]
    acc = [float(r["正确率"]) for r in rows]
    n = len(rows)
    xs = [PAD + i * (W - 2 * PAD) / max(1, n - 1) for i in range(n)]
    lo, hi = min(cpm) * 0.8, max(cpm) * 1.15
    ys = [H - PAD - (v - lo) / max(1e-6, hi - lo) * (H - 2 * PAD) for v in cpm]
    ya = [H - PAD - (a - 50) / 50 * (H - 2 * PAD) for a in acc]
    dr.line([PAD - 10, H - PAD, W - PAD + 10, H - PAD], fill=(90, 96, 120), width=2)
    dr.line([PAD - 10, PAD - 20, PAD - 10, H - PAD], fill=(90, 96, 120), width=2)
    dr.line(list(zip(xs, ys)), fill=(120, 170, 255), width=4, joint="curve")
    dr.line(list(zip(xs, ya)), fill=(120, 220, 150), width=2, joint="curve")
    for x, y, v in zip(xs, ys, cpm):
        dr.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(255, 200, 120))
    dr.text((PAD, 16), "双拼打字成绩趋势", font=F2, fill=(235, 240, 255))
    dr.text((PAD + 300, 24), "— 字/分", font=F, fill=(120, 170, 255))
    dr.text((PAD + 420, 24), "— 正确率(%)", font=F, fill=(120, 220, 150))
    dr.text((PAD, H - PAD + 14), rows[0]["时间"][:10], font=F, fill=(160, 170, 200))
    dr.text((W - PAD - 110, H - PAD + 14), rows[-1]["时间"][:10], font=F, fill=(160, 170, 200))
    out = os.path.join(BASE, "typing_chart.png")
    img.save(out)
    print("趋势图已保存：" + out)

def selftest():
    bad = []
    for lvl, items in CORPUS.items():
        for t, p in items:
            if not p: continue
            for py in p.split():
                a, b = encode(py)
                if "?" in (a + b): bad.append((t, py))
    print("自检：语料音节全部可编码 ✅" if not bad else "失败: %s" % bad)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="双拼打字练习器 v2")
    ap.add_argument("--mode", default="混合", choices=["字", "词", "句", "段", "混合"])
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--no-hint", action="store_true")
    ap.add_argument("--timed", type=int, metavar="秒", help="限时挑战")
    ap.add_argument("--review", type=int, metavar="个数", help="错题重练")
    ap.add_argument("--mistakes", action="store_true", help="查看错题本")
    ap.add_argument("--keys", action="store_true")
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--chart", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if sys.platform == "win32":
        try: sys.stdout.reconfigure(encoding="utf-8")
        except Exception: pass
    enable_ansi()
    if a.keys: show_keys()
    elif a.stats: stats()
    elif a.chart: chart()
    elif a.mistakes: show_mistakes()
    elif a.selftest: selftest()
    elif a.timed: timed(a.timed)
    elif a.review: review(a.review)
    else: run(a.mode, a.n, not a.no_hint)
