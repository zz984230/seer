import random
from typing import List, Dict, Optional
from ..logger import logger

class AntiCrawler:
    def __init__(self, user_agents: List[str], proxies: List[str]):
        self.user_agents = user_agents
        self.proxies = proxies
    
    def get_random_user_agent(self) -> str:
        """获取随机User-Agent"""
        return random.choice(self.user_agents)
    
    def get_random_proxy(self) -> Optional[str]:
        """获取随机代理"""
        if self.proxies:
            return random.choice(self.proxies)
        return None
    
    def random_delay(self, min_delay: float, max_delay: float) -> None:
        """随机延迟"""
        import time
        delay = random.uniform(min_delay, max_delay)
        logger.debug(f"随机延迟: {delay:.2f}秒")
        time.sleep(delay)
    
    def generate_random_cookies(self) -> Dict[str, str]:
        """生成随机Cookies（示例，实际使用中应根据网站特性调整）"""
        return {
            "user_id": f"user_{random.randint(10000, 99999)}",
            "session_id": f"session_{random.randint(10000000, 99999999)}",
            "timestamp": str(int(time.time()))
        }
    
    def rotate_ip(self) -> Optional[str]:
        """IP轮换（实际使用中应结合代理池实现）"""
        return self.get_random_proxy()
