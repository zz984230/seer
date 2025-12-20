from playwright.sync_api import sync_playwright
import time
import random
from typing import Dict, Any, Optional
from ..logger import logger
from ..config import settings

class XiaohongshuCrawler:
    def __init__(self):
        self.browser = None
        self.page = None
        self.config = settings.crawler
    
    def _setup_browser(self):
        """设置浏览器"""
        playwright = sync_playwright().start()
        self.browser = playwright.chromium.launch(headless=False)
        self.page = self.browser.new_page()
        
        # 设置随机User-Agent
        user_agent = random.choice(self.config.user_agents)
        self.page.set_extra_http_headers({
            "User-Agent": user_agent
        })
    
    def _close_browser(self):
        """关闭浏览器"""
        if self.browser:
            self.browser.close()
    
    def _random_delay(self):
        """随机延迟，避免被反爬"""
        delay = random.uniform(self.config.delay_range["min"], self.config.delay_range["max"])
        time.sleep(delay)
    
    def get_page_content(self, url: str) -> Optional[str]:
        """获取指定URL的页面内容"""
        try:
            self._setup_browser()
            logger.info(f"开始爬取URL: {url}")
            
            # 访问页面
            self.page.goto(url, timeout=self.config.timeout * 1000)
            self._random_delay()
            
            # 等待页面加载完成
            self.page.wait_for_load_state("networkidle")
            self._random_delay()
            
            # 滚动页面，加载动态内容
            for _ in range(3):
                self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                self._random_delay()
            
            # 获取页面内容
            content = self.page.content()
            logger.info(f"成功获取页面内容: {url}")
            return content
        
        except Exception as e:
            logger.error(f"爬取页面失败: {url}, 错误: {str(e)}")
            return None
        
        finally:
            self._close_browser()
    
    def download_media(self, url: str, save_path: str) -> bool:
        """下载媒体资源"""
        try:
            self._setup_browser()
            logger.info(f"开始下载媒体: {url} -> {save_path}")
            
            # 下载资源
            response = self.page.request.get(url)
            if response.status == 200:
                # 确保目录存在
                import os
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                
                with open(save_path, "wb") as f:
                    f.write(response.body())
                logger.info(f"媒体下载成功: {save_path}")
                return True
            else:
                logger.error(f"媒体下载失败: {url}, 状态码: {response.status}")
                return False
        
        except Exception as e:
            logger.error(f"媒体下载异常: {url}, 错误: {str(e)}")
            return False
        
        finally:
            self._close_browser()
