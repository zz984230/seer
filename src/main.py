import argparse
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
        
        # 2. 解析页面内容
        parsed_data = parser.parse_page(html_content)
        if not parsed_data:
            logger.error("页面解析失败，任务终止")
            return
        
        # 3. 保存爬取数据
        success = storage.save_crawled_data(parsed_data, current_date)
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
