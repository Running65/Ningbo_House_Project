# AI 协作日志

> 项目：宁波市二手房市场价格分析与可视化研究
> 记录人：成员 C（可视化与前端）
> 要求：记录关键 Prompt、AI 生成代码/方案出现的问题、人工排查与修复思路。课程要求不少于 3 个真实排错案例。

---

## 案例一：Pyecharts 生成的 demo.html 打开全白

- **日期**：2026-11-23
- **场景**：第一周 Pyecharts 最小演示，按教程示例代码运行 `pyecharts_demo.py` 生成 demo.html，浏览器打开后页面全白，只有背景没有图表。
- **关键 Prompt**：
  > "file:///D:/Ningbo_House_Project_C/demo/demo.html，全是空白？"
- **AI 给出的排查过程**：
  1. 让 AI 分析可能原因，AI 建议先看 HTML 源码引用了哪些外部资源；
  2. 用 `grep 'src='` 检查发现页面只引用了一个外部脚本：`https://assets.pyecharts.org/assets/v6/echarts.min.js`；
  3. 定位结论：**pyecharts 默认从 CDN 在线加载 ECharts 引擎**，本机访问该 CDN 失败时页面就是全白——不是代码写错，是资源加载失败。
- **修复方案**（AI 建议 + 人工验证）：
  1. 从 npmmirror 镜像下载 `echarts.min.js`（1MB）放到 demo 目录（试了官方 CDN、jsdelivr 均失败，npmmirror 成功）；
  2. 在代码里加两行，让 HTML 引用本地资源：
     ```python
     from pyecharts.globals import CurrentConfig
     CurrentConfig.ONLINE_HOST = "./"
     ```
  3. 重新生成 demo.html，引用变为 `src="./echarts.min.js"`，浏览器打开正常显示。
- **收获/复盘**：
  - 页面空白不一定报错，要从"页面引用了哪些外部资源"入手排查；
  - 第 4 周做正式大屏必须沿用本地化资源方案，否则答辩现场网络不稳会翻车；
  - 下载大文件时国内镜像（npmmirror/清华源）比官方源可靠。

---

## 案例二：git push 报 "Password authentication is not supported"

- **日期**：2026-11-23
- **场景**：第一次推送 member-c 分支，Git 提示输密码后报错：
  `remote: Invalid username or token. Password authentication is not supported for Git operations.`
- **关键 Prompt**：
  > "Invalid username or token 什么意思？"（附完整报错）
- **AI 的解释**：GitHub 从 2021 年起禁止用账号密码做 Git 推送认证，密码栏必须填 **Personal Access Token（PAT）**。
- **修复方案**（人工操作）：
  1. GitHub → Settings → Developer settings → Personal access tokens (classic) → Generate new token；
  2. 勾选 `repo` 权限，生成 `ghp_` 开头的令牌并立即复制（刷新即消失）；
  3. 再次 push 时：Username 填账号，Password 粘贴 token，成功后 Windows 凭据管理器记住，之后免输。
- **收获/复盘**：
  - 遇到认证问题先看报错原文，里面通常写明了原因；
  - token 只在生成时可见，要马上存好；
  - 团队里谁第一次推送都会踩这个坑，可写进《协作规范》。

---

## 案例三：git pull 时被卡进黑屏编辑器（vim）

- **日期**：2026-11-23
- **场景**：执行 `git pull origin main` 合并远程更新时，终端突然变成黑底编辑器，显示 "Please enter a commit message..."和一堆 `~`，无法正常操作，以为卡死了。
- **关键 Prompt**：
  > "这是什么？"（附编辑器截图内容）
- **AI 的解释**：这是 Git 默认编辑器 **vim**，拉取产生 merge 提交时要求填写合并说明。`~` 只是空行显示，不是异常。
- **修复方案**：
  1. 在 vim 里：直接敲入合并说明 → 按 `Esc` → 输入 `:wq` → 回车，保存退出完成合并；
  2. 若想放弃合并：`Esc` → `:q!` 回车；
  3. 以后避免弹出：`git pull --no-edit origin main`。
- **收获/复盘**：
  - 终端里的编辑器有"模式"概念，Esc 是回到普通模式再输命令；
  - 常用 Git 命令可以加参数避免交互界面，写脚本/协作时更顺畅。

---

## 附：其他值得记的小经验（非独立案例）

- **GitHub 直连不稳定**：本机直连 github.com 经常 Connection reset / 443 超时。clone、pull 等不需要认证的操作走 `gh-proxy.com` 加速前缀可用；push 需要认证走不了代理，只能等网络恢复或用代理软件。
- **AI 生成代码不是拿来就用的**：以上案例中 AI 的方案都需要人工验证（如镜像地址要挨个试），最终成功的一步都是人工确认过的。

<!-- 后续案例按同样格式往下追加 -->
