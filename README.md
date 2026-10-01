# my-scripts

我的学习脚本仓库 —— 边学边写，持续更新。

## 目录

| 文件 | 作用 |
|---|---|
| `mini_agent.py` | 一个 100 行的最小 AI Agent：演示「模型 + 工具 + 循环」的工作原理 |
| `dsp_practice.py` | 双拼打字练习器：小鹤键位提示、速度/正确率统计、历史成绩 |
| `ram_price.py` | 内存价格记录器：记录价格、判断买点、生成走势图 |

## 环境

- Python 3.x（标准库为主，图表需要 Pillow）
- 运行示例：

```bash
python dsp_practice.py            # 双拼练习（默认 20 题）
python dsp_practice.py --keys     # 查看小鹤双拼键位表
python ram_price.py show          # 查看内存价格记录
python mini_agent.py              # 运行最小 Agent 示例
```

## 学习记录

- 2026-10-01 创建仓库，第一次 commit
