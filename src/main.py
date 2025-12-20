import argparse
import os
import json
from seer.crawler import XiaohongshuCrawler
from seer.parser import XiaohongshuParser
from seer.storage import DataStorage
from seer.logger import logger
from seer.config import settings
from datetime import datetime


def main():
    """应用主入口"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="Xiaohongshu crawler application")
    parser.add_argument("--url", type=str, required=True, help="URL to crawl")
    args = parser.parse_args()
    
    # 获取当前日期，用于存储目录
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # 初始化各个模块
    crawler = XiaohongshuCrawler()
    parser = XiaohongshuParser()
    storage = DataStorage()
    
    logger.info(f"开始执行小红书爬虫任务: {args.url}")
    
    try:
        # 1. 获取页面内容
        html_content = crawler.get_page_content(args.url)
        if not html_content:
            logger.error("无法获取页面内容，任务终止")
            return
        
        # 保存原始HTML内容到文件，用于分析真实笔记ID格式
        with open("test_html.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        logger.info("原始HTML内容已保存到test_html.html文件")
        
        # 2. 解析页面内容
        parsed_data = parser.parse_page(html_content)
        if not parsed_data:
            logger.error("页面解析失败，任务终止")
            return
        
        # 3. 保存爬取数据
        success = storage.save_crawled_data(parsed_data, current_date)
        
        # 4. 保存笔记列表到文件
        if "notes" in parsed_data and parsed_data["notes"]:
            # 获取存储路径
            user_id = parsed_data["up_info"].get("user_id", "unknown")
            storage_path = os.path.join(storage.base_dir, user_id, current_date)
            os.makedirs(storage_path, exist_ok=True)
            
            # 保存为txt文件
            notes_txt_path = os.path.join(storage_path, "notes.txt")
            with open(notes_txt_path, "w", encoding="utf-8") as f:
                f.write("小红书笔记列表\n")
                f.write("=" * 50 + "\n")
                for i, note in enumerate(parsed_data["notes"], 1):
                    f.write(f"{i}. {note['title']}\n")
                    f.write(f"   链接: {note['url']}\n")
                    f.write(f"   类型: {note['type']}\n")
                    f.write("-" * 50 + "\n")
            logger.info(f"笔记列表保存成功: {notes_txt_path}")
            
            # 保存为JSON文件（可选，方便后续处理）
            notes_json_path = os.path.join(storage_path, "notes.json")
            with open(notes_json_path, "w", encoding="utf-8") as f:
                json.dump(parsed_data["notes"], f, ensure_ascii=False, indent=2)
            logger.info(f"笔记列表JSON保存成功: {notes_json_path}")
        
        if success:
            logger.info("爬虫任务执行成功")
        else:
            logger.error("数据保存失败，任务终止")
    
    except Exception as e:
        logger.error(f"爬虫任务执行失败: {str(e)}")
    
    finally:
        logger.info("爬虫任务执行完毕")


if __name__ == "__main__":
    main()
