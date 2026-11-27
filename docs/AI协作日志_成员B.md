# AI 协作日志 — 成员 B

> 项目：宁波市二手房市场价格分析与可视化研究
> 记录人：成员 B（数据清洗与分析工程师）
> 要求：记录关键 Prompt、AI 生成代码/方案出现的问题、人工排查与修复思路。课程要求不少于 3 个真实排错案例。

---

## 案例一：pandas 读 CSV 后表头出现乱码前缀（BOM 问题）

- **日期**：2026-11-25
- **场景**：第一周数据质量检查，用 pandas 读取成员 A 采集的 `data/raw/raw_data.csv`，第一个字段名显示为 `标题`，导致按「标题」取列会找不到列。
- **关键 Prompt**：
  > "pandas 读 csv 后第一列名字是 '标题'，前面多了个看不懂的字符，取列报 KeyError，怎么解决？"
- **排查过程**：
  1. AI 先让确认文件编码：用十六进制查看文件开头，发现是 `EF BB BF` 三个字节；
  2. 定位结论：这是 **UTF-8 BOM**（字节顺序标记），成员 A 的采集脚本在 Windows 上以 `utf-8-sig` 写出，而读取时用了 `encoding="utf-8"`，BOM 被当成了表头第一个字符的一部分。
- **修复方案**：读取时改成 `pd.read_csv(RAW_DATA_PATH, encoding="utf-8-sig")`，BOM 自动被剥掉，表头恢复正常。
- **收获/复盘**：
  - Windows 上中文 CSV 常见「带 BOM 的 UTF-8」，读写两端编码要一致，最好统一用 `utf-8-sig`；
  - 列名取不到时先 `print(df.columns.tolist())` 看真实列名，再对比有没有不可见字符；
  - 已把这一条写进《数据字段设计表》的清洗约定，提醒组内其他成员。

---

## 案例二：电脑里有三个 Python，pip 装的 pandas 和运行用的不是同一个

- **日期**：2026-11-25
- **场景**：第一周环境准备，运行 `python analysis/beginner_test.py` 报 `ModuleNotFoundError: No module named 'pandas'`；但明明刚用 `pip install pandas` 安装成功，还打印过安装过程。
- **关键 Prompt**：
  > "pip install pandas 显示安装成功，运行 python 却说没有 pandas，为什么？"
- **排查过程**：
  1. AI 让先查「运行的 python 是哪一个」和「pip 属于哪个 python」是不是同一个：`where python` 一查，机器上同时有 **MSYS2 的 python（C:\msys64\ucrt64\bin\python.exe）、Anaconda 的 python（D:\Anaconda3\python.exe）、Windows 商店的 python** 三个；
  2. 进一步检查发现 bash 终端默认用的是 MSYS2 的 python，它**连 pip 都没有**，之前 `pip install` 实际走的是另一个环境的 pip；
  3. 定位结论：不是 pandas 装失败，而是**安装的 python 和运行的 python 不是同一个**（AI 第一版给的 `pip install` 重试方案因此无效）。
- **修复方案**：
  1. 确认 `D:\Anaconda3\python.exe` 自带 pandas（`python -c "import pandas; print(pandas.__version__)"` 输出 3.0.3）；
  2. 之后所有脚本统一用 `D:\Anaconda3\python.exe` 运行，不再依赖裸命令 `python` / `pip`。
- **收获/复盘**：
  - 「装了却 import 不到」十有八九是**多个 Python 环境错位**，先 `where python` 再谈安装；
  - 最稳的写法是用 `python -m pip install`，保证 pip 和 python 是同一个环境；
  - 建议三人按教程统一用虚拟环境（.venv），避免我这种多 Python 共存的坑。

---

## 案例三：git push 报 "could not read Username"，终端无法弹出登录

- **日期**：2026-11-25
- **场景**：第一周把交付物推送到 `member-b-week1` 分支时，push 报错 `fatal: could not read Username for 'https://github.com': terminal prompts disabled`，分支始终推不上去。
- **关键 Prompt**：
  > "git push 提示 could not read Username for 'https://github.com'，terminal prompts disabled，怎么办？"（附完整报错）
- **排查过程**：
  1. AI 分析：这是**没有任何已保存的 GitHub 凭据**，Git 想在终端里提示输入用户名/密码，但当前终端不支持交互输入，所以直接失败；
  2. 检查发现本机装了 Git Credential Manager（credential.helper=manager），但凭据库里还没有 github.com 的记录；纯命令行方式（`git credential fill`）也取不到；
  3. 定位结论：需要**完成一次浏览器登录授权**，让凭据管理器把令牌存下来，之后才能非交互推送。
- **修复方案**：
  1. 在能弹出图形界面的方式下重新执行 push，凭据管理器弹出 GitHub 登录授权窗口；
  2. 在浏览器完成登录授权后，push 成功（`27419e7..ec836e6 member-b-week1 -> member-b-week1`）；
  3. 之后再次 push 不再需要登录。
- **收获/复盘**：
  - 认证报错先看原文，`terminal prompts disabled` 说明问题在「无法交互输入」而不是账号密码错误；
  - 第一次 push 前先单独执行一次 `git fetch` 或 `git ls-remote` 验证凭据是否可用，不要等到交付时才发现推不上去；
  - 这个坑和成员 C 遇到的「密码认证不被支持」是同一个主题：GitHub 推送认证只认令牌，第一次配置好凭据管理器后全组都省事。

---

## 附：其他值得记的小经验（非独立案例）

- **AI 生成的脚本要本地先跑一遍再交付**：`beginner_test.py` 里 `df.describe()` 默认只统计数值列，能看到「总价」字段的最大值 1799 万（明显的长尾），这一条被直接写进了《数据质量报告》的异常值观察。
- **调 AI 时把报错原文、操作系统、命令完整贴出来**，一轮就能定位；只描述「跑不了」要多来回好几轮。

## 案例四：字段统计脚本按文本列直接 describe，数值校验全是空

- **日期**：2026-11-27
- **场景**：第二周做原始数据字段级统计，第一版脚本想对「面积」「单价(元/平)」做合法性校验（是否有 ≤0 的值），直接 `df["面积"].astype(float)` 时报 `ValueError: could not convert string to float: '136.15平米'`——原始数据里这两个字段都带单位/千位逗号，是文本列。
- **关键 Prompt**：
  > "面积列是 '136.15平米' 这种文本，怎么批量转成数值做校验？"
- **排查过程**：
  1. AI 第一版直接 `astype(float)`，报错信息里明确给出了无法转换的样例值，一眼定位到是单位后缀问题；
  2. 同理「单价(元/平)」含千位逗号、「关注数」含「人关注」后缀，都是同类问题；
  3. 人工确认清洗顺序：先 `.str.replace()` 去掉单位/逗号再 `astype(float)`，并抽了 3 行人工核对转换结果。
- **修复方案**：`df["面积"].str.replace("平米", "", regex=False).str.strip().astype(float)`，单价、关注数同法处理后再统计。最终验证出 1195 条全部合法（≤0 为 0 条），且「总价×10000÷面积」与采集单价偏差全为 0。
- **收获/复盘**：
  - 原始数据没有纯数值列时，`describe()` 看不到任何统计——先做「临时转换」再统计，但这层转换属于检查用途，真正的统一清洗留到第3周 `clean.py`；
  - `astype` 报错会打印第一个无法转换的值，是定位脏格式最快的线索；
  - 交叉校验（总价、面积、单价三者自洽）比单字段检查更能发现采集问题，本次结果证明成员A的数据质量很好。

<!-- 后续案例按同样格式往下追加 -->
