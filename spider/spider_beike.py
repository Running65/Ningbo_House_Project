"""
宁波二手房数据采集爬虫（贝壳版 + 登录支持）

- 目标：贝壳找房宁波站 https://nb.ke.com/ershoufang/
- 第 1 页公开可访问；第 2 页起需要登录
- 运行后浏览器窗口会弹出，遇到登录页时请手动登录一次，之后自动继续

用法：
    python spider_beike.py        # 采集 40 页（约 1200 条）
    python spider_beike.py 100    # 采集 100 页
"""
import csv
import os
import random
import re
import sys
import time
from datetime import datetime

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = r"D:\ms-playwright"

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# ==================== 配置 ====================
BASE_URL = "https://nb.ke.com/ershoufang/"
OUTPUT_FILENAME = "raw_data.csv"
DELAY_RANGE = (3, 5)
LOGIN_WAIT = 600            # 等登录的最长时间（秒）
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

FIELDS = ["标题", "小区名", "户型", "面积", "朝向", "楼层",
          "总价(万)", "单价(元/平)", "关注数", "发布时间", "房源链接"]


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def clean_price(text):
    return re.sub(r"[^\d.,]", "", text) if text else ""


def parse_house_info(text):
    """从 houseInfo 文本里提取户型/面积/楼层/朝向"""
    layout = re.search(r"\d+室\d+厅", text)
    area = re.search(r"[\d.]+\s*平米", text)
    floor = re.search(r"[高中低]楼层(?:\(共\d+层\))?", text)
    orient = re.search(r"(?<![高中低])[东南西北]{1,3}", text)
    return {
        "户型": layout.group(0) if layout else "",
        "面积": area.group(0).replace(" ", "") if area else "",
        "楼层": floor.group(0) if floor else "",
        "朝向": orient.group(0) if orient else "",
    }


def parse_page(html):
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
            link = "https://nb.ke.com" + link

        house = li.select_one(".houseInfo")
        house_text = house.get_text(" ", strip=True) if house else ""
        info = parse_house_info(house_text)

        tp = li.select_one(".totalPrice span")
        up = li.select_one(".unitPrice span")
        total_price = tp.get_text(strip=True) if tp else ""
        unit_price = up.get_text(strip=True) if up else ""

        pos = li.select_one(".positionInfo")
        community = pos.get_text(strip=True) if pos else ""

        follow = li.select_one(".followInfo")
        follow_text = follow.get_text(strip=True) if follow else ""
        fp = [p.strip() for p in follow_text.split("/")] if follow_text else []

        listings.append({
            "标题": title,
            "小区名": community,
            "户型": info["户型"],
            "面积": info["面积"],
            "朝向": info["朝向"],
            "楼层": info["楼层"],
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


def is_login(page):
    return "login" in page.url or "clogin" in page.url


def wait_login(page):
    log("⚠️  需要登录！请在浏览器窗口里登录贝壳账号（手机号+验证码），脚本会等你...")
    start = time.time()
    while time.time() - start < LOGIN_WAIT:
        time.sleep(3)
        if not is_login(page):
            log("✅ 登录成功，继续采集")
            return True
    log("❌ 等待登录超时（10分钟），结束")
    return False


def main():
    pages = int(sys.argv[1]) if len(sys.argv) > 1 else 40

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(project_root, "data", "raw")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, OUTPUT_FILENAME)
    if os.path.exists(output_path):
        os.remove(output_path)

    log(f"开始采集：共 {pages} 页，目标 {BASE_URL}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context(user_agent=UA, viewport={"width": 1366, "height": 768}, locale="zh-CN")
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

            # 被重定向到登录页 → 等用户登录
            if is_login(page):
                if not wait_login(page):
                    break
                page.wait_for_timeout(2000)

            html = page.content()
            listings = parse_page(html)
            if listings:
                save_csv(listings, output_path)
                total += len(listings)
                log(f"第{pg}页 采集 {len(listings)} 条（累计 {total} 条）")
            else:
                log(f"第{pg}页 未取到数据")

            if pg < pages:
                time.sleep(random.uniform(*DELAY_RANGE))

        browser.close()

    log(f"采集完成，共 {total} 条，已保存到 {output_path}")


if __name__ == "__main__":
    main()
