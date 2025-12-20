import pytest
from seer.crawler import XiaohongshuCrawler


def test_crawler_initialization():
    """测试爬虫初始化"""
    crawler = XiaohongshuCrawler()
    assert crawler is not None


def test_get_page_content():
    """测试获取页面内容"""
    # 注意：实际运行时需要替换为真实的小红书URL
    test_url = "https://www.xiaohongshu.com/explore"
    crawler = XiaohongshuCrawler()
    content = crawler.get_page_content(test_url)
    assert content is not None
    assert isinstance(content, str)
    assert len(content) > 0
