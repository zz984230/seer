import os
import json
from typing import Dict, Any, List
from ..logger import logger
from ..config import settings

class DataStorage:
    def __init__(self):
        self.base_dir = settings.storage.base_dir
    
    def get_storage_path(self, user_id: str, date: str) -> str:
        """获取存储路径：按UP主ID和日期组织"""
        return os.path.join(self.base_dir, user_id, date)
    
    def save_media(self, url: str, save_path: str) -> bool:
        """保存媒体文件（图片/视频）"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # 使用requests下载媒体（需要在项目中添加requests依赖）
            import requests
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                with open(save_path, "wb") as f:
                    f.write(response.content)
                logger.info(f"媒体保存成功: {save_path}")
                return True
            else:
                logger.error(f"媒体保存失败: {url}, 状态码: {response.status_code}")
                return False
        
        except Exception as e:
            logger.error(f"媒体保存异常: {url}, 错误: {str(e)}")
            return False
    
    def save_metadata(self, metadata: Dict[str, Any], storage_path: str) -> bool:
        """保存元数据为JSON格式"""
        try:
            metadata_path = os.path.join(storage_path, "metadata.json")
            
            # 确保目录存在
            os.makedirs(storage_path, exist_ok=True)
            
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            logger.info(f"元数据保存成功: {metadata_path}")
            return True
        
        except Exception as e:
            logger.error(f"元数据保存失败: {str(e)}")
            return False
    
    def save_crawled_data(self, crawled_data: Dict[str, Any], date: str) -> bool:
        """保存爬取的数据（主方法）"""
        try:
            # 获取UP主ID
            user_id = crawled_data["up_info"].get("user_id", "unknown")
            if not user_id:
                # 如果没有user_id，使用用户名作为替代
                username = crawled_data["up_info"].get("username", "unknown")
                user_id = f"user_{username}"
            
            # 获取存储路径
            storage_path = self.get_storage_path(user_id, date)
            
            # 下载并保存媒体资源
            media_paths = {
                "images": [],
                "videos": []
            }
            
            # 保存图片
            for i, img_url in enumerate(crawled_data["content_info"]["images"]):
                img_name = f"image_{i}.jpg"
                img_path = os.path.join(storage_path, "images", img_name)
                if self.save_media(img_url, img_path):
                    media_paths["images"].append(img_path)
            
            # 保存视频
            for i, video_url in enumerate(crawled_data["content_info"]["videos"]):
                video_name = f"video_{i}.mp4"
                video_path = os.path.join(storage_path, "videos", video_name)
                if self.save_media(video_url, video_path):
                    media_paths["videos"].append(video_path)
            
            # 更新metadata中的媒体路径，确保包含notes字段
            metadata = {
                **crawled_data,
                "media_paths": media_paths,
                "crawl_date": date
            }
            
            # 保存元数据
            return self.save_metadata(metadata, storage_path)
        
        except Exception as e:
            logger.error(f"保存爬取数据失败: {str(e)}")
            return False
