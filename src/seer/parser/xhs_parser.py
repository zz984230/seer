from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
from ..logger import logger
from ..config import settings

class XiaohongshuParser:
    def __init__(self):
        self.config = settings.parser
    
    def parse_page(self, html_content: str) -> Optional[Dict[str, Any]]:
        """解析小红书页面内容"""
        if not html_content:
            logger.info("空内容解析，返回None")
            return None
        
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            
            # 解析UP主信息
            up_info = self._parse_up_info(soup)
            
            # 解析内容信息
            content_info = self._parse_content_info(soup)
            
            # 解析评论信息
            comments = self._parse_comments(soup)
            
            # 组合结果
            result = {
                "up_info": up_info,
                "content_info": content_info,
                "comments": comments
            }
            
            logger.info("页面解析成功")
            return result
        
        except Exception as e:
            logger.error(f"页面解析失败: {str(e)}")
            return None
    
    def _parse_up_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """解析UP主信息"""
        try:
            # 示例：根据实际HTML结构调整选择器
            up_info = {
                "username": "",
                "user_id": "",
                "avatar": ""
            }
            
            # 查找用户名
            username_elem = soup.find("div", class_="user-name") or soup.find("span", class_="username")
            if username_elem:
                up_info["username"] = username_elem.text.strip()
            
            # 查找头像
            avatar_elem = soup.find("img", class_="avatar")
            if avatar_elem and avatar_elem.get("src"):
                up_info["avatar"] = avatar_elem["src"]
            
            logger.debug(f"UP主信息解析: {up_info}")
            return up_info
        
        except Exception as e:
            logger.error(f"UP主信息解析失败: {str(e)}")
            return {"username": "", "user_id": "", "avatar": ""}
    
    def _parse_content_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """解析内容信息"""
        try:
            content_info = {
                "content_id": "",
                "title": "",
                "text": "",
                "publish_time": "",
                "content_type": "",
                "images": [],
                "videos": []
            }
            
            # 查找标题
            title_elem = soup.find("h1", class_="title") or soup.find("div", class_="note-title")
            if title_elem:
                content_info["title"] = title_elem.text.strip()
            
            # 查找正文
            text_elem = soup.find("div", class_="content") or soup.find("div", class_="note-content")
            if text_elem:
                content_info["text"] = text_elem.text.strip()
            
            # 查找图片
            img_elems = soup.find_all("img", class_="image") or soup.find_all("img", class_="note-image")
            for img_elem in img_elems:
                if img_elem.get("src"):
                    content_info["images"].append(img_elem["src"])
            
            # 查找视频
            video_elems = soup.find_all("video")
            for video_elem in video_elems:
                if video_elem.get("src"):
                    content_info["videos"].append(video_elem["src"])
                else:
                    # 检查是否有source标签
                    source_elem = video_elem.find("source")
                    if source_elem and source_elem.get("src"):
                        content_info["videos"].append(source_elem["src"])
            
            # 确定内容类型
            if content_info["videos"]:
                content_info["content_type"] = "video"
            elif content_info["images"]:
                content_info["content_type"] = "image"
            else:
                content_info["content_type"] = "text"
            
            logger.debug(f"内容信息解析: {content_info}")
            return content_info
        
        except Exception as e:
            logger.error(f"内容信息解析失败: {str(e)}")
            return {
                "content_id": "",
                "title": "",
                "text": "",
                "publish_time": "",
                "content_type": "",
                "images": [],
                "videos": []
            }
    
    def _parse_comments(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """解析评论信息"""
        try:
            comments = []
            
            # 查找评论容器
            comment_container = soup.find("div", class_="comments") or soup.find("div", class_="note-comments")
            if not comment_container:
                return comments
            
            # 查找评论列表
            comment_elems = comment_container.find_all("div", class_="comment-item") or comment_container.find_all("div", class_="comment")
            
            # 限制最大评论数
            for i, comment_elem in enumerate(comment_elems[:self.config.max_comments]):
                comment = {
                    "comment_id": f"comment_{i}",
                    "commenter": "",
                    "content": "",
                    "comment_time": ""
                }
                
                # 查找评论者
                commenter_elem = comment_elem.find("span", class_="commenter") or comment_elem.find("div", class_="username") or comment_elem.find("span", class_="username")
                if commenter_elem:
                    comment["commenter"] = commenter_elem.text.strip()
                
                # 查找评论内容
                content_elem = comment_elem.find("div", class_="comment-content") or comment_elem.find("span", class_="content")
                if content_elem:
                    comment["content"] = content_elem.text.strip()
                
                # 查找评论时间
                time_elem = comment_elem.find("span", class_="comment-time") or comment_elem.find("div", class_="time")
                if time_elem:
                    comment["comment_time"] = time_elem.text.strip()
                
                comments.append(comment)
            
            logger.debug(f"解析到 {len(comments)} 条评论")
            return comments
        
        except Exception as e:
            logger.error(f"评论解析失败: {str(e)}")
            return []
