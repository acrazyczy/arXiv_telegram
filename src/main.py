import feedparser
import requests
import time
import os
import re
import json
import sys
import html
from datetime import datetime, date
from dotenv import load_dotenv 

# 加载 .env (本地调试用)
load_dotenv()

# --- 配置读取 ---
def load_config():
    # 获取当前脚本绝对路径，确保在任何目录下运行都能找到 config.json
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    config_path = os.path.join(project_root, 'config.json')
    
    if not os.path.exists(config_path):
        print(f"错误: 找不到配置文件 {config_path}")
        sys.exit(1)
        
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# 获取环境变量
BOT_TOKEN = os.environ.get("TG_BOT_TOKEN") 
CHAT_ID = os.environ.get("TG_CHAT_ID")

def get_rss_url(categories):
    category_str = "+".join(categories)
    return f"http://export.arxiv.org/rss/{category_str}"

def send_telegram_message(message):
    if not BOT_TOKEN or not CHAT_ID:
        print(">> [跳过发送] (未配置 Token 或 Chat ID)")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"\n!! 发送失败: {e}")
        # ---------------- 关键调试信息 ----------------
        print(f"❌ Telegram 返回的错误详情: {response.text}")
        print("-" * 30)
        print(f"📦 我尝试发送的内容:\n{payload['text']}")
        print("-" * 30)
        # --------------------------------------------

import html
import re

def format_entry(entry, max_length):
    # 1. 基础清洗：去除标题换行
    title = html.escape(entry.title.replace('\n', ' ').strip())
    authors = html.escape(entry.author)
    
    # 2. 深度清洗摘要
    raw_summary = entry.summary.replace('\n', ' ')
    clean_text = re.sub(r'<[^>]+>', '', raw_summary).strip()
    
    # 正则提取 ID, Type, Abstract
    pattern = r'arXiv:([^\s]+)\s+Announce Type:\s+(.*?)\s+Abstract:\s+(.*)'
    match = re.search(pattern, clean_text, re.IGNORECASE)
    
    paper_type = "Unknown"
    abstract_text = clean_text
    
    if match:
        paper_type = match.group(2).strip()
        abstract_text = match.group(3).strip()
    
    # 3. [新增] 提取分类标签 (cs.GT, cs.DS 等)
    # feedparser 解析的 tags 是一个 list of dict: [{'term': 'cs.GT', ...}, ...]
    try:
        # 获取所有标签的 term
        tags_list = [t['term'] for t in entry.tags]
        # 过滤掉可能的无关标签（ArXiv 比较干净，通常都是分类号）
        tags_str = ", ".join(tags_list)
    except (AttributeError, KeyError):
        tags_str = "Unknown"

    # 4. 截断摘要
    if len(abstract_text) > max_length:
        abstract_text = abstract_text[:max_length] + "..."
    
    # 5. 转义
    summary = html.escape(abstract_text)
    
    # 6. 链接处理
    abs_link = entry.link
    pdf_link = abs_link.replace("/abs/", "/pdf/") + ".pdf"
    
    # 7. 生成标签样式
    type_emoji = "🆕" if "new" in paper_type.lower() else "🔄"
    type_label = f"<code>[{paper_type.upper()}]</code>"
    tags_label = f"🏷 <code>{tags_str}</code>" # [新增] 分类标签样式
    
    # 8. 构建消息
    msg = (
        f"<b>📄 {title}</b>\n"
        f"{type_emoji} {type_label} | {tags_label}\n\n"  # [修改] 把分类加在这一行
        f"<b>👥 Authors:</b> {authors}\n\n"
        f"<b>📝 Abstract:</b>\n{summary}\n\n"
        f"🔗 <a href='{pdf_link}'>PDF Download</a> | <a href='{abs_link}'>Abs Page</a>"
    )
    return msg

def is_today(entry_date_struct):
    """判断文章日期是否是今天 (UTC)"""
    # feedparser 解析的时间是 time.struct_time
    # 我们将其转换为 date 对象
    entry_date = date(entry_date_struct.tm_year, entry_date_struct.tm_mon, entry_date_struct.tm_mday)
    today = datetime.utcnow().date()
    return entry_date == today

def main():
    # 1. 加载配置
    config = load_config()
    categories = config.get("categories", [])
    # 获取 max_items，如果没写则默认为 0
    max_items = config.get("max_items", 0)
    summary_length = config.get("summary_length", 800)
    
    if not categories:
        print("错误: 配置文件中没有 categories")
        sys.exit(1)

    # 2. 获取 RSS
    rss_url = get_rss_url(categories)
    print(f"正在获取 RSS: {rss_url}")
    
    feed = feedparser.parse(rss_url)
    total_entries = len(feed.entries)
    print(f"获取到 {total_entries} 篇文章")
    
    if total_entries == 0:
        print("没有新文章。")
        return

    # 3. 遍历并发送
    print(f"限制数量: {'无限制' if max_items == 0 else max_items}")

    print(f"当前 UTC 日期: {datetime.utcnow().date()}")

    count = 0
    for entry in feed.entries:
        # 1. 检查数量限制
        if max_items > 0 and count >= max_items:
            break
            
        # 2. [新增] 检查日期：如果不是今天发布的，就跳过
        # 注意：ArXiv 的 RSS 里 published_parsed 是 UTC 时间
        if not is_today(entry.published_parsed):
            print(f"跳过旧文章: {entry.title[:20]}... ({entry.published[:10]})")
            continue

        print(f"[{count+1}] 正在发送: {entry.title[:30]}...")
        msg = format_entry(entry, summary_length)
        send_telegram_message(msg)
        count += 1
        time.sleep(1) 

    if count == 0:
        print("今天没有新文章 (可能是周末或 ArXiv 尚未更新)。")
    else:
        print(f"任务完成，共推送 {count} 篇")

if __name__ == "__main__":
    main()