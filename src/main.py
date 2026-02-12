import feedparser
import requests
import time
import os
import json
import sys
import html
import re
from datetime import datetime, date
from dotenv import load_dotenv 
import pytz
from collections import defaultdict

load_dotenv()

# --- 1. 配置读取 ---
def load_config():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    config_path = os.path.join(project_root, 'config.json')
    
    if not os.path.exists(config_path):
        print(f"错误: 找不到配置文件 {config_path}")
        sys.exit(1)
        
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

BOT_TOKEN = os.environ.get("TG_BOT_TOKEN") 
CHAT_ID = os.environ.get("TG_CHAT_ID")

def get_rss_url(all_categories):
    unique_cats = list(set(all_categories))
    category_str = "+".join(unique_cats)
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
        print(f"!! 发送失败: {e}")

def is_today(entry_date_struct):
    entry_date = date(entry_date_struct.tm_year, entry_date_struct.tm_mon, entry_date_struct.tm_mday)
    today = datetime.utcnow().date()
    return entry_date == today

def get_paper_tags(entry):
    try:
        return [t['term'] for t in entry.tags]
    except (AttributeError, KeyError):
        return []

# --- 关键词检查函数 ---
def check_keywords(entry, keywords):
    """
    检查标题和摘要是否包含关键词。
    返回匹配到的第一个关键词，如果没有匹配则返回 None。
    (不区分大小写)
    """
    if not keywords:
        return None
        
    # 组合标题和摘要进行搜索
    text_to_search = (entry.title + " " + entry.summary).lower()
    
    for kw in keywords:
        if kw.lower() in text_to_search:
            return kw # 返回匹配到的词
            
    return None

# --- 2. 详细版消息格式 (含摘要) ---
def format_entry_detailed(entry, max_length=800, matched_keyword=None):
    title = html.escape(entry.title.replace('\n', ' ').strip())
    authors = html.escape(entry.author)
    
    # 摘要清洗
    raw_summary = entry.summary.replace('\n', ' ')
    clean_text = re.sub(r'<[^>]+>', '', raw_summary).strip()
    
    pattern = r'arXiv:([^\s]+)\s+Announce Type:\s+(.*?)\s+Abstract:\s+(.*)'
    match = re.search(pattern, clean_text, re.IGNORECASE)
    
    paper_type = "Unknown"
    abstract_text = clean_text
    
    if match:
        paper_type = match.group(2).strip()
        abstract_text = match.group(3).strip()
    
    tags = get_paper_tags(entry)
    tags_str = ", ".join(tags)

    if len(abstract_text) > max_length:
        abstract_text = abstract_text[:max_length] + "..."
    
    summary = html.escape(abstract_text)
    
    abs_link = entry.link
    pdf_link = abs_link.replace("/abs/", "/pdf/") + ".pdf"
    
    type_emoji = "🆕" if "new" in paper_type.lower() else "🔄"
    type_label = f"<code>[{paper_type.upper()}]</code>"
    tags_label = f"🏷 <code>{tags_str}</code>"
    
    # [新增] 如果是因为关键词升级的，显示特殊标签
    keyword_label = ""
    if matched_keyword:
        keyword_label = f"\n🎯 <b>Keyword Match:</b> <code>{matched_keyword}</code>"
    
    msg = (
        f"<b>📄 {title}</b>\n"
        f"{type_emoji} {type_label} | {tags_label}{keyword_label}\n\n"
        f"<b>👥 Authors:</b> {authors}\n\n"
        f"<b>📝 Abstract:</b>\n{summary}\n\n"
        f"🔗 <a href='{pdf_link}'>PDF Download</a> | <a href='{abs_link}'>Abs Page</a>"
    )
    return msg

# --- 3. 批量发送 Digest ---
def send_digest_messages(simple_buffer):
    if not simple_buffer:
        return

    all_lines = []
    header = "<b>🗞️ Daily Digest (Other Categories)</b>\n"
    all_lines.append(header)

    for category, entries in simple_buffer.items():
        cat_header = f"\n<b>📂 {category}</b>\n"
        all_lines.append(cat_header)

        for entry in entries:
            title = html.escape(entry.title.replace('\n', ' ').strip())
            authors_full = html.escape(entry.author)
            pdf_link = entry.link.replace("/abs/", "/pdf/") + ".pdf"
            
            line = f"🔹 <a href='{pdf_link}'>{title}</a>\n    <i>{authors_full}</i>\n"
            all_lines.append(line)

    MAX_LENGTH = 4000
    current_message = ""
    
    for line in all_lines:
        if len(current_message) + len(line) > MAX_LENGTH:
            send_telegram_message(current_message)
            time.sleep(1)
            current_message = line
        else:
            current_message += line
            
    if current_message:
        send_telegram_message(current_message)

def main():
    config = load_config()
    
    detailed_categories = config.get("detailed_categories", [])
    digest_categories = config.get("digest_categories", [])
    keywords = config.get("keywords", [])
    summary_length = config.get("summary_length", 800)
    
    all_categories = detailed_categories + digest_categories
    
    if not all_categories:
        print("提示: detailed_categories 和 digest_categories 均为空，无任务。")
        sys.exit(0)

    utc_now = datetime.now(pytz.utc)

    rss_url = get_rss_url(all_categories)
    print(f"正在获取 RSS: {len(all_categories)} 个分类...")
    feed = feedparser.parse(rss_url)
    print(f"获取到 {len(feed.entries)} 篇文章")

    count = 0
    detailed_count = 0
    simple_buffer = defaultdict(list)

    for entry in feed.entries:
        if not is_today(entry.published_parsed):
            continue

        paper_tags = get_paper_tags(entry)
         
        # 1. 先检查是否属于核心精读分类 (Detailed)
        # 如果命中，直接发送，不做关键词检查 (节省时间)
        if any(tag in detailed_categories for tag in paper_tags):
            print(f"[{count+1}] 发送 (详细 - 核心): {entry.title[:30]}...")
            # 注意：这里 matched_keyword 传 None，因为我们为了省时间没去查
            msg = format_entry_detailed(entry, max_length=summary_length, matched_keyword=None)
            send_telegram_message(msg)
            detailed_count += 1
            time.sleep(1)
            
        # 2. 如果不属于精读，再检查是否属于泛读分类 (Digest)
        elif any(tag in digest_categories for tag in paper_tags):
            
            # 只有在它是 Digest 候选时，才去跑关键词检查 (Lazy Check)
            matched_keyword = check_keywords(entry, keywords)
            
            if matched_keyword:
                # 命中关键词 -> 升级为详细发送
                print(f"[{count+1}] 发送 (详细 - 关键词升级: {matched_keyword}): {entry.title[:30]}...")
                msg = format_entry_detailed(entry, max_length=summary_length, matched_keyword=matched_keyword)
                send_telegram_message(msg)
                detailed_count += 1
                time.sleep(1)
            else:
                # 没命中关键词 -> 也就是普通的 Digest
                target_cat = next((tag for tag in paper_tags if tag in digest_categories), "Others")
                print(f"[{count+1}] 缓存 (Digest -> {target_cat}): {entry.title[:30]}...")
                simple_buffer[target_cat].append(entry)
        
        # 3. 既不在 Detailed 也不在 Digest (可能是 RSS 带来的无关交叉引用) -> 跳过
        else:
            continue

        count += 1

    # 循环结束后发送 Digest
    if simple_buffer:
        print(f"正在构建并发送 Digest...")
        send_digest_messages(simple_buffer)

    print(f"任务完成。共处理 {count} 篇 (详细: {detailed_count}, 简报: {count - detailed_count})")


if __name__ == "__main__":
    main()