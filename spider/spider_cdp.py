"""
宁波二手房采集（CDP 版：接管你已登录的真实 Chrome）

原理：
- 用真实 Chrome（带 --remote-debugging-port=9222 启动）来采集
- 浏览器指纹是真实的，不会被贝壳的「小怪兽」识别
- 你在 Chrome 里已经登录贝壳，爬虫直接复用你的登录会话

用法（前提：Chrome 已登录贝壳，且调试端口 9222 开着）：
    python spider_cdp.py        # 采集 40 页
    python spider_cdp.py 100    # 采集 100 页
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

BASE_URL = "https://nb.ke.com/ershoufang/"
OUTPUT_FILENAME = "raw_data.csv"
DELAY_RANGE = (8, 12)

FIELDS = ["标题", "小区名", "户型", "面积", "朝向", "楼层",
          "总价(万)", "单价(元/平)", "关注数", "发布时间", "房源链接"]


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def clean_price(text):
    return re.sub(r"[^\d.,]", "", text) if text else ""


def parse_house_info(text):
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
        pos = li.select_one(".positionInfo")
        follow = li.select_one(".followInfo")

        follow_text = follow.get_text(strip=True) if follow else ""
        fp = [p.strip() for p in follow_text.split("/")] if follow_text else []

        listings.append({
            "标题": title,
            "小区名": pos.get_text(strip=True) if pos else "",
            "户型": info["户型"],
            "面积": info["面积"],
            "朝向": info["朝向"],
            "楼层": info["楼层"],
            "总价(万)": clean_price(tp.get_text(strip=True) if tp else ""),
            "单价(元/平)": clean_price(up.get_text(strip=True) if up else ""),
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


def main():
    pages = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    start = int(sys.argv[2]) if len(sys.argv) > 2 else 1

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(project_root, "data", "raw")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, OUTPUT_FILENAME)
    if start == 1 and os.path.exists(output_path):
        os.remove(output_path)

    log(f"开始采集：第 {start}-{pages} 页，通过 CDP 接管真实 Chrome")

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()

        total = 0
        for pg in range(start, pages + 1):
            url = BASE_URL if pg == 1 else f"{BASE_URL}pg{pg}/"
            try:
                page.goto(url, timeout=60000, wait_until="domcontentloaded")
                page.wait_for_timeout(2000)
            except Exception as e:
                log(f"第{pg}页 访问失败: {e}")
                continue

            html = page.content()
            listings = parse_page(html)
            if listings:
                save_csv(listings, output_path)
                total += len(listings)
                log(f"第{pg}页 采集 {len(listings)} 条（累计 {total} 条）")
            else:
                log(f"第{pg}页 未取到数据（可能又被拦）")

            if pg < pages:
                time.sleep(random.uniform(*DELAY_RANGE))

        # 注意：CDP 连接不要 close（会关掉你的真实浏览器）

    log(f"采集完成，共 {total} 条，已保存到 {output_path}")


if __name__ == "__main__":
    main()
