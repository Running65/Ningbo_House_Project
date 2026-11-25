"""
宁波二手房数据采集爬虫（Playwright 版，可绕过链家验证码）

原理：
- 用真实浏览器（有头模式）模拟真人翻页，绕过链家对无头浏览器的拦截
- 翻页过程中如果弹出验证码，脚本会暂停，等你手动在浏览器窗口里完成验证，
  验证通过后自动继续采集

用法：
    python spider_playwright.py        # 采集 40 页（约 1200 条，满足 1000 要求）
    python spider_playwright.py 100    # 采集 100 页（约 3000 条）

注意事项：
- 运行时浏览器窗口会弹出，请**不要关掉它**
- 弹出验证码时，在浏览器窗口里手动滑一下/点一下，脚本检测到通过后自动继续
"""
import csv
import os
import random
import re
import sys
import time
from datetime import datetime

# 浏览器装在 D 盘（不是 C 盘）
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = r"D:\ms-playwright"

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# ==================== 配置区 ====================
BASE_URL = "https://nb.lianjia.com/ershoufang/"
OUTPUT_FILENAME = "raw_data.csv"
DELAY_RANGE = (3, 5)          # 翻页间隔（秒）
CAPTCHA_WAIT = 300            # 等你解验证码的最长时间（秒）
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

FIELDS = [
    "标题", "小区名", "商圈", "户型", "面积", "朝向", "装修", "楼层", "建筑类型",
    "总价(万)", "单价(元/平)", "关注数", "发布时间", "房源链接",
]


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def clean_price(text):
    """只保留数字、逗号、小数点，去掉「万」「元/平」等单位"""
    return re.sub(r"[^\d.,]", "", text) if text else ""


def parse_page(html):
    """解析一页 HTML，返回 list[dict]（复用 requests 版的解析逻辑）"""
    soup = BeautifulSoup(html, "html.parser")
    listings = []
    for li in soup.select("ul.sellListContent li"):
        title_el = li.select_one(".title a")
        if not title_el:
            continue
        title = title_el.get_text(strip=True)
        link = title_el.get("href", "")
        if link.startswith("//"):
            link = "https:" + link
        elif link.startswith("/"):
            link = "https://nb.lianjia.com" + link

        house_info = li.select_one(".houseInfo")
        info_text = house_info.get_text(strip=True) if house_info else ""
        parts = [p.strip() for p in info_text.split("|")] if info_text else []

        tp = li.select_one(".totalPrice span")
        up = li.select_one(".unitPrice span")
        total_price = tp.get_text(strip=True) if tp else ""
        unit_price = up.get_text(strip=True) if up else ""

        pos = li.select_one(".positionInfo")
        pos_text = pos.get_text(strip=True) if pos else ""
        community, district = pos_text.rsplit("-", 1) if "-" in pos_text else (pos_text, "")

        follow = li.select_one(".followInfo")
        follow_text = follow.get_text(strip=True) if follow else ""
        fp = [p.strip() for p in follow_text.split("/")] if follow_text else []

        listings.append({
            "标题": title,
            "小区名": community.strip(),
            "商圈": district.strip(),
            "户型": parts[0] if len(parts) > 0 else "",
            "面积": parts[1] if len(parts) > 1 else "",
            "朝向": parts[2] if len(parts) > 2 else "",
            "装修": parts[3] if len(parts) > 3 else "",
            "楼层": parts[4] if len(parts) > 4 else "",
            "建筑类型": parts[5] if len(parts) > 5 else "",
            "总价(万)": clean_price(total_price),
            "单价(元/平)": clean_price(unit_price),
            "关注数": fp[0] if len(fp) > 0 else "",
            "发布时间": fp[1] if len(fp) > 1 else "",
            "房源链接": link,
        })
    return listings


def save_csv(data, output_path):
    is_new = not os.path.exists(output_path)
    with open(output_path, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if is_new:
            writer.writeheader()
        writer.writerows(data)


def is_captcha(page):
    return page.title() == "CAPTCHA"


def wait_captcha(page):
    """遇到验证码时暂停，等用户在浏览器里手动解决"""
    log("⚠️  检测到验证码！请在浏览器窗口里手动完成验证，脚本会等你...")
    start = time.time()
    while time.time() - start < CAPTCHA_WAIT:
        time.sleep(3)
        if not is_captcha(page):
            log("✅ 验证码已通过，继续采集")
            return True
    log("❌ 等待超时（5分钟），跳过本页")
    return False


def main():
    pages = int(sys.argv[1]) if len(sys.argv) > 1 else 40

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(project_root, "data", "raw")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, OUTPUT_FILENAME)
    # 重新采集，删除旧文件避免重复
    if os.path.exists(output_path):
        os.remove(output_path)

    log(f"开始采集：共 {pages} 页，输出到 {output_path}")
    log("提示：浏览器窗口会弹出，请不要关闭；弹验证码时手动解一下即可")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context(
            user_agent=UA,
            viewport={"width": 1366, "height": 768},
            locale="zh-CN",
        )
        page = ctx.new_page()

        total = 0
        for pg in range(1, pages + 1):
            url = BASE_URL if pg == 1 else f"{BASE_URL}pg{pg}/"
            try:
                page.goto(url, timeout=60000, wait_until="domcontentloaded")
                page.wait_for_timeout(2500)
            except Exception as e:
                log(f"第{pg}页 访问失败: {e}")
                continue

            # 有验证码（或没有房源）就等用户解
            if is_captcha(page) or page.locator("ul.sellListContent li").count() == 0:
                if not wait_captcha(page):
                    continue
                page.wait_for_timeout(2000)

            html = page.content()
            listings = parse_page(html)
            if listings:
                save_csv(listings, output_path)
                total += len(listings)
                log(f"第{pg}页 采集 {len(listings)} 条（累计 {total} 条）")
            else:
                log(f"第{pg}页 仍未取到数据，跳过")

            if pg < pages:
                time.sleep(random.uniform(*DELAY_RANGE))

        browser.close()

    log(f"采集完成，共 {total} 条，已保存到 {output_path}")


if __name__ == "__main__":
    main()
