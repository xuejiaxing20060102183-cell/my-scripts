# -*- coding: utf-8 -*-
"""
mini_agent.py —— 一个 100 行的最小 Agent（用来理解"AI 为什么会干活"）

核心：Agent = 模型 + 工具 + 循环
  1. 把你的任务和"有哪些工具"一起发给模型
  2. 模型回话：要么直接给答案（结束），要么要求调用某个工具
  3. 你在本地真的执行那个工具，把结果塞回对话
  4. 回到第 1 步，直到模型给答案（或达到最大步数）
"""
import json, os, time, urllib.request

# ---------- 0. 读取网关配置（API 地址和密钥） ----------
CFG = json.load(open(r"C:\Users\jia\OneDrive\Desktop\workbuddy agent\wb2api\config.json", encoding="utf-8"))
API = "http://" + CFG["listen"] + "/v1/chat/completions"
KEY = CFG["api_key"]
MODEL = "cn:deepseek-v4.1-flash"

# ---------- 1. 工具：普通 Python 函数 ----------
def get_time():
    return time.strftime("%Y-%m-%d %H:%M:%S")

def read_file(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()[:2000]
    except Exception as e:
        return "读取失败: " + str(e)

def calc(expression):
    try:
        return str(eval(expression, {"__builtins__": {}}, {}))   # 演示用；生产环境别用 eval
    except Exception as e:
        return "算不出来: " + str(e)

def list_dir(path):
    try:
        return "\n".join(os.listdir(path)[:30])
    except Exception as e:
        return "列不出来: " + str(e)

# 工具名 → 真的函数
TOOLBOX = {"get_time": get_time, "read_file": read_file, "calc": calc, "list_dir": list_dir}

# 给模型看的"工具说明书"（JSON Schema）
TOOLS = [
 {"type": "function", "function": {"name": "get_time", "description": "获取当前日期和时间",
   "parameters": {"type": "object", "properties": {}}}},
 {"type": "function", "function": {"name": "read_file", "description": "读取一个文本文件的内容",
   "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "文件的完整路径"}},
                  "required": ["path"]}}},
 {"type": "function", "function": {"name": "calc", "description": "计算一个数学表达式，例如 12*(3+4)",
   "parameters": {"type": "object", "properties": {"expression": {"type": "string"}}, "required": ["expression"]}}},
 {"type": "function", "function": {"name": "list_dir", "description": "列出一个目录下的文件名",
   "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
]

# ---------- 2. 调用模型 ----------
def call_model(messages):
    body = json.dumps({"model": MODEL, "messages": messages, "tools": TOOLS, "temperature": 0}).encode()
    req = urllib.request.Request(API, data=body, headers={
        "Content-Type": "application/json", "Authorization": "Bearer " + KEY})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read().decode())

# ---------- 3. Agent 循环（整个 Agent 的灵魂就这 20 行） ----------
def run_agent(task, max_steps=8, verbose=True):
    messages = [
        {"role": "system", "content": "你是一个简洁的助手。需要实时信息（时间/文件/计算）时必须调用工具，不要凭空猜。"},
        {"role": "user", "content": task},
    ]
    for step in range(1, max_steps + 1):
        resp = call_model(messages)
        msg = resp["choices"][0]["message"]
        messages.append(msg)
        calls = msg.get("tool_calls") or []
        if verbose:
            if calls:
                print("  第%d步 → 模型要调用: %s" % (step, ", ".join(c["function"]["name"] for c in calls)))
            else:
                print("  第%d步 → 模型给出最终答案" % step)
        if not calls:                                  # 没有工具调用 = 任务完成
            return msg.get("content", ""), messages
        for c in calls:                                # 执行模型要求的每个工具
            name = c["function"]["name"]
            try:
                args = json.loads(c["function"]["arguments"] or "{}")
            except json.JSONDecodeError:
                args = {}
            result = TOOLBOX[name](**args) if name in TOOLBOX else "没有这个工具"
            if verbose:
                print("       ↳ 本地执行 %s(%s) = %s" % (name, args, str(result)[:80].replace("\n", " ")))
            messages.append({"role": "tool", "tool_call_id": c["id"], "content": str(result)})
    return "（达到最大步数，任务未完成）", messages

if __name__ == "__main__":
    task = "现在几点了？然后读一下 C:\\Users\\jia\\OneDrive\\Desktop\\workbuddy agent\\my-agent\\demo.txt，再帮我算一下 (123*456+789)/3 是多少"
    print("任务:", task, "\n")
    t0 = time.time()
    answer, history = run_agent(task)
    print("\n最终答案:", answer)
    print("\n本次对话消息数: %d 条，耗时 %.1f 秒" % (len(history), time.time() - t0))
