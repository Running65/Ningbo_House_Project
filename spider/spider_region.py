"""
宁波二手房采集（按行政区，CDP 接管真实 Chrome）

原理：贝壳列表页按行政区筛选（如 /ershoufang/yinzhouqu2/ = 鄞州区），
     每个区域页的房源自动带上该行政区，无需访问详情页。

用法：
    python spider_region.py        # 每个行政区采 4 页
    python spider_region.py 6      # 每个行政区采 6 页
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

# 宁波 11 个行政区（贝壳的区域筛选 URL 后缀）
REGIONS = {
    "yinzhouqu2": "鄞州区",
    "haishuqu1": "海曙区",
    "jiangbeiqu1": "江北区",
    "zhenhaiqu1": "镇海区",
    "beilunqu1": "北仑区",
    "fenghuaqu": "奉化区",
    "cixishi": "慈溪市",
    "yuyaoshi": "余姚市",
    "xiangshanxian": "象山县",
    "ninghaixian": "宁海县",
    "qianwanxinqu": "前湾新区",
}

OUTPUT_FILENAME = "raw_data.csv"
DELAY_RANGE = (3, 5)

FIELDS = ["标题", "小区名", "行政区", "户型", "面积", "朝向", "楼层",
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


def parse_page(html, region_name):
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
            "行政区": region_name,
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


def is_blocked(page):
    return page.title() == "CAPTCHA" or "captcha" in page.url or "login" in page.url


def wait_unblock(page):
    log("⚠️  遇到验证码/登录，请在浏览器窗口完成验证，脚本会等你...")
    start = time.time()
    while time.time() - start < 300:
        time.sleep(3)
        if not is_blocked(page):
            log("✅ 已通过，继续")
            return True
    return False


def main():
    pages_per_region = int(sys.argv[1]) if len(sys.argv) > 1 else 4

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(project_root, "data", "raw")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, OUTPUT_FILENAME)
    if os.path.exists(output_path):
        os.remove(output_path)

    log(f"开始按行政区采集：11 个区域 × {pages_per_region} 页")

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        ctx = browser.contexts[0]
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        total = 0
        for region_code, region_name in REGIONS.items():
            for pg in range(1, pages_per_region + 1):
                url = f"https://nb.ke.com/ershoufang/{region_code}/" if pg == 1 \
                    else f"https://nb.ke.com/ershoufang/{region_code}/pg{pg}/"
                try:
                    page.goto(url, timeout=60000, wait_until="domcontentloaded")
                    page.wait_for_timeout(2000)
                except Exception as e:
                    log(f"{region_name} 第{pg}页 访问失败: {e}")
                    continue

                if is_blocked(page):
                    if not wait_unblock(page):
                        break
                    page.wait_for_timeout(2000)

                listings = parse_page(page.content(), region_name)
                if listings:
                    save_csv(listings, output_path)
                    total += len(listings)
                    log(f"{region_name} 第{pg}页 采 {len(listings)} 条（累计 {total}）")
                else:
                    log(f"{region_name} 第{pg}页 无数据")
                    break  # 该区域没有更多页了

                time.sleep(random.uniform(*DELAY_RANGE))

    log(f"采集完成，共 {total} 条，已保存到 {output_path}")


if __name__ == "__main__":
    main()
