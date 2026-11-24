"""
宁波二手房数据采集爬虫
数据源：链家宁波站 https://nb.lianjia.com/ershoufang/
功能：采集二手房列表页房源信息，保存为 CSV

用法：
    python spider.py          # 抓取 1 页（约 30 条，用于测试）
    python spider.py 5        # 抓取 5 页
    python spider.py 100      # 抓取 100 页（全量，约 3000 条）
"""
import csv
import os
import random
import re
import sys
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

# ==================== 配置区 ====================
BASE_URL = "https://nb.lianjia.com/ershoufang/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}
OUTPUT_FILENAME = "raw_data.csv"
DELAY_RANGE = (0.5, 1.5)          # 每页请求之间的随机延时（秒），避免被封
RETRY_TIMES = 3                   # 单页失败重试次数
TIMEOUT = 15                      # 请求超时（秒）

# CSV 字段顺序（与成员 B 的分析需求对齐）
FIELDS = [
    "标题", "小区名", "商圈", "户型", "面积", "朝向", "装修", "楼层", "建筑类型",
    "总价(万)", "单价(元/平)", "关注数", "发布时间", "房源链接",
]


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def clean_price(text):
    """只保留数字、逗号、小数点，去掉「万」「元/平」等单位"""
    return re.sub(r"[^\d.,]", "", text) if text else ""


def fetch_page(page):
    """抓取第 page 页列表页，返回 HTML 文本；失败返回 None"""
    url = BASE_URL if page == 1 else f"https://nb.lianjia.com/ershoufang/pg{page}/"
    for attempt in range(1, RETRY_TIMES + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            if resp.status_code == 200:
                resp.encoding = "utf-8"
                return resp.text
            log(f"第{page}页 状态码异常: {resp.status_code}")
        except Exception as e:
            log(f"第{page}页 请求出错(第{attempt}次): {e}")
        time.sleep(2 * attempt)  # 失败后等一会儿再重试
    return None


def parse_page(html):
    """解析一页的房源列表，返回 list[dict]"""
    soup = BeautifulSoup(html, "html.parser")
    listings = []
    for li in soup.select("ul.sellListContent li"):
        item = parse_listing(li)
        if item:
            listings.append(item)
    return listings


def parse_listing(li):
    """解析单个房源 <li>，返回字段字典；无效返回 None"""
    title_el = li.select_one(".title a")
    if not title_el:
        return None

    title = title_el.get_text(strip=True)
    link = title_el.get("href", "")
    if link.startswith("//"):
        link = "https:" + link
    elif link.startswith("/"):
        link = "https://nb.lianjia.com" + link

    # 户型 | 面积 | 朝向 | 装修 | 楼层 | 建筑类型
    house_info = li.select_one(".houseInfo")
    info_text = house_info.get_text(strip=True) if house_info else ""
    info_parts = [p.strip() for p in info_text.split("|")] if info_text else []

    # 总价、单价
    total_price = li.select_one(".totalPrice span")
    unit_price = li.select_one(".unitPrice span")
    total_price = total_price.get_text(strip=True) if total_price else ""
    unit_price = unit_price.get_text(strip=True) if unit_price else ""

    # 小区名、商圈（格式：小区名-商圈）
    position = li.select_one(".positionInfo")
    pos_text = position.get_text(strip=True) if position else ""
    community, district = pos_text.rsplit("-", 1) if "-" in pos_text else (pos_text, "")

    # 关注数、发布时间（格式：0人关注 / 9个月以前发布）
    follow = li.select_one(".followInfo")
    follow_text = follow.get_text(strip=True) if follow else ""
    follow_parts = [p.strip() for p in follow_text.split("/")] if follow_text else []

    return {
        "标题": title,
        "小区名": community.strip(),
        "商圈": district.strip(),
        "户型": info_parts[0] if len(info_parts) > 0 else "",
        "面积": info_parts[1] if len(info_parts) > 1 else "",
        "朝向": info_parts[2] if len(info_parts) > 2 else "",
        "装修": info_parts[3] if len(info_parts) > 3 else "",
        "楼层": info_parts[4] if len(info_parts) > 4 else "",
        "建筑类型": info_parts[5] if len(info_parts) > 5 else "",
        "总价(万)": clean_price(total_price),
        "单价(元/平)": clean_price(unit_price),
        "关注数": follow_parts[0] if len(follow_parts) > 0 else "",
        "发布时间": follow_parts[1] if len(follow_parts) > 1 else "",
        "房源链接": link,
    }


def save_csv(data, output_path):
    """把数据追加写入 CSV；首次写入时写表头"""
    is_new = not os.path.exists(output_path)
    with open(output_path, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if is_new:
            writer.writeheader()
        writer.writerows(data)


def main():
    pages = int(sys.argv[1]) if len(sys.argv) > 1 else 1

    # 输出目录：项目根目录下的 data/raw/
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(project_root, "data", "raw")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, OUTPUT_FILENAME)

    log(f"开始采集：共 {pages} 页，输出到 {output_path}")
    total = 0
    for page in range(1, pages + 1):
        html = fetch_page(page)
        if html is None:
            log(f"第{page}页 采集失败，跳过")
            continue
        listings = parse_page(html)
        if listings:
            save_csv(listings, output_path)
            total += len(listings)
            log(f"第{page}页 采集到 {len(listings)} 条")
        else:
            log(f"第{page}页 未解析到房源（可能被反爬拦截，稍后重试）")
        # 页与页之间随机延时，降低被封风险
        if page < pages:
            time.sleep(random.uniform(*DELAY_RANGE))
    log(f"采集完成，共 {total} 条，已保存到 {output_path}")


if __name__ == "__main__":
    main()
