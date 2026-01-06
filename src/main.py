"""
小红书爬虫应用主入口

本模块是小红书爬虫应用的主入口，负责：
1. 爬取小红书用户主页的笔记数据
2. 数据清洗和格式化
3. 数据分析和统计
4. 生成分析报告

使用方法：
    python src/main.py --url <小红书用户主页URL> [--max-notes <最大笔记数>]

示例：
    python src/main.py --url https://www.xiaohongshu.com/user/profile/1234567890 --max-notes 10
"""

import argparse
import os
import json
from dotenv import load_dotenv
from seer.crawler import XiaohongshuCrawler, XHS_Apis
from seer.cleaner import XiaohongshuCleaner
from seer.analyzer import XiaohongshuAnalyzer
from seer.reporter import XiaohongshuReporter
from seer.storage import DataStorage
from seer.logger import logger
from config import settings
from datetime import datetime


def main():
    """应用主入口"""
    # 加载环境变量
    load_dotenv()
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="Xiaohongshu crawler application")
    parser.add_argument("--url", type=str, required=True, help="URL to crawl")
    parser.add_argument("--max-notes", type=int, default=settings.parser.max_notes, help="Maximum number of notes to crawl")
    args = parser.parse_args()
    
    # 获取当前日期，用于存储目录
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # 初始化各个模块
    crawler = XiaohongshuCrawler()  # 已更新为使用Spider_XHS
    cleaner = XiaohongshuCleaner()
    analyzer = XiaohongshuAnalyzer()
    reporter = XiaohongshuReporter()
    storage = DataStorage()
    
    logger.info(f"开始执行小红书爬虫任务: {args.url}")
    
    try:
        # 1. 获取用户信息
        user_id = args.url.split("/")[-1].split("?")[0]
        storage_path = os.path.join(storage.base_dir, user_id, current_date)
        os.makedirs(storage_path, exist_ok=True)
        
        # 使用新的爬虫方法获取用户的所有笔记
        cookies_str = os.getenv("XHS_COOKIES")  # 从环境变量获取cookies
        if not cookies_str:
            logger.error("未找到XHS_COOKIES环境变量，请检查.env文件")
            return
            
        # 获取配置参数
        max_pages = min(args.max_notes, settings.crawler.max_pages)
        request_interval = settings.crawler.request_interval
        logger.info(f"最大爬取页面数: {max_pages}, 请求间隔: {request_interval}秒")
        
        success, msg, notes = crawler.get_user_all_notes(args.url, cookies_str)
        if not success:
            logger.error(f"获取用户笔记失败: {msg}")
            return
        
        # 限制爬取的笔记数量
        if len(notes) > max_pages:
            notes = notes[:max_pages]
            logger.info(f"限制爬取笔记数量为: {max_pages}")
        
        logger.info(f"获取到 {len(notes)} 条笔记")
        
        # 2. 获取笔记详细内容
        logger.info("开始获取笔记详细内容...")
        detailed_notes = []
        import time
        
        for i, note in enumerate(notes):
            try:
                success, msg, note_info = crawler.get_note_info(note["url"], cookies_str)
                if success and note_info:
                    detailed_notes.append(note_info)
                    logger.info(f"✅ 成功获取笔记详细内容: {note['title']}")
                
                # 添加请求间隔（除了最后一个请求）
                if i < len(notes) - 1:
                    time.sleep(request_interval)
                    
            except Exception as e:
                logger.error(f"获取笔记详细内容失败: {note['title']}, 错误: {str(e)}")
                continue
            
            if detailed_notes:
                # 3. 保存笔记详细内容到文件
                # 保存为txt文件
                notes_txt_path = os.path.join(storage_path, "notes.txt")
                with open(notes_txt_path, "w", encoding="utf-8") as f:
                    f.write("小红书笔记列表\n")
                    f.write("=" * 50 + "\n")
                    for i, note in enumerate(detailed_notes, 1):
                        f.write(f"{i}. {note['title']}\n")
                        f.write(f"   链接: {note['url']}\n")
                        f.write(f"   类型: {note['note_type']}\n")
                        f.write(f"   内容: {note.get('desc', '无内容')[:100]}...\n")
                        f.write(f"   点赞: {note.get('liked_count', 0)}")
                        f.write(f"   收藏: {note.get('collected_count', 0)}")
                        f.write(f"   评论: {note.get('comment_count', 0)}\n")
                        f.write("-" * 50 + "\n")
                logger.info(f"笔记列表保存成功: {notes_txt_path}")
                
                # 保存为JSON文件
                notes_json_path = os.path.join(storage_path, "notes.json")
                with open(notes_json_path, "w", encoding="utf-8") as f:
                    json.dump(detailed_notes, f, ensure_ascii=False, indent=2)
                logger.info(f"笔记详细内容JSON保存成功: {notes_json_path}")
                
                # 打印笔记信息
                logger.info("\n获取的笔记信息：")
                for i, note in enumerate(detailed_notes, 1):
                    logger.info(f"{i}. 标题: {note['title']}")
                    logger.info(f"   链接: {note['url']}")
                    logger.info(f"   内容: {note.get('desc', '无内容')[:100]}...")
                    logger.info(f"   点赞: {note.get('liked_count', 0)}")
                    logger.info(f"   收藏: {note.get('collected_count', 0)}")
                    logger.info(f"   评论: {note.get('comment_count', 0)}")
                
                # 4. 数据清洗
                logger.info("开始数据清洗...")
                cleaned_notes = cleaner.clean_batch_data(detailed_notes, "note")
                logger.info(f"数据清洗完成，清洗后的笔记数量: {len(cleaned_notes)}")
                
                # 保存清洗后的数据
                cleaned_notes_path = os.path.join(storage_path, "cleaned_notes.json")
                with open(cleaned_notes_path, "w", encoding="utf-8") as f:
                    json.dump(cleaned_notes, f, ensure_ascii=False, indent=2)
                logger.info(f"清洗后的数据保存成功: {cleaned_notes_path}")
                
                # 5. 数据分析
                logger.info("开始数据分析...")
                analysis_results = analyzer.analyze_notes(cleaned_notes)
                logger.info("数据分析完成")
                
                # 保存分析结果
                analysis_results_path = os.path.join(storage_path, "analysis_results.json")
                with open(analysis_results_path, "w", encoding="utf-8") as f:
                    json.dump(analysis_results, f, ensure_ascii=False, indent=2)
                logger.info(f"分析结果保存成功: {analysis_results_path}")
                
                # 6. 生成分析报告
                logger.info("开始生成分析报告...")
                report_paths = reporter.generate_all_reports({
                    "notes_analysis": analysis_results,
                    "users_analysis": {},
                    "comments_analysis": {}
                })
                logger.info(f"分析报告生成完成，报告路径: {report_paths}")
        
        logger.info("爬虫任务执行成功")
    
    except Exception as e:
        logger.error(f"爬虫任务执行失败: {str(e)}")
    
    finally:
        logger.info("爬虫任务执行完毕")


if __name__ == "__main__":
    main()
