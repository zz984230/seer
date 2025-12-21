from typing import Dict, List, Any, Optional
import re
from datetime import datetime
from seer.logger import logger


class XiaohongshuCleaner:
    """
    Xiaohongshu data cleaner class
    Responsible for cleaning, validating and formatting raw data from crawler
    """
    
    def __init__(self):
        """
        Initialize the cleaner
        """
        self.logger = logger
        
    def clean_note_data(self, raw_note: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Clean a single note data
        
        :param raw_note: Raw note data from crawler
        :return: Cleaned note data or None if invalid
        """
        try:
            # Basic validation
            if not self._validate_note_structure(raw_note):
                self.logger.warning(f"Invalid note structure: {raw_note.get('id', 'unknown')}")
                return None
            
            cleaned = {
                "note_id": self._clean_id(raw_note.get("id", "") or raw_note.get("note_id", "")),
                "title": self._clean_text(raw_note.get("title", "") or raw_note.get("displayTitle", "")),
                "content": self._clean_text(raw_note.get("content", "")),
                "author_id": self._clean_id(raw_note.get("user", {}).get("id", "")),
                "author_name": self._clean_text(raw_note.get("user", {}).get("nickname", "")),
                "likes": self._clean_number(raw_note.get("likes", 0) or raw_note.get("like_count", 0)),
                "comments": self._clean_number(raw_note.get("comments", 0) or raw_note.get("comment_count", 0)),
                "collections": self._clean_number(raw_note.get("collections", 0) or raw_note.get("collect_count", 0)),
                "shares": self._clean_number(raw_note.get("shares", 0) or raw_note.get("share_count", 0)),
                "tags": self._clean_tags(raw_note.get("tags", [])),
                "create_time": self._clean_datetime(raw_note.get("time", 0) or raw_note.get("create_time", 0)),
                "update_time": self._clean_datetime(raw_note.get("update_time", 0)),
                "url": self._clean_url(raw_note.get("url", "")),
                "type": self._clean_note_type(raw_note.get("type", "normal")),
                "media": self._clean_media(raw_note.get("image_list", []) or raw_note.get("video", {})),
                "location": self._clean_location(raw_note.get("location", {})),
                "hashtags": self._extract_hashtags(raw_note.get("content", "")),
                "platform": "xiaohongshu"
            }
            
            # Validate cleaned data
            if not self._validate_cleaned_note(cleaned):
                self.logger.warning(f"Invalid cleaned note: {cleaned.get('note_id', 'unknown')}")
                return None
            
            return cleaned
            
        except Exception as e:
            self.logger.error(f"Error cleaning note data: {str(e)}")
            return None
    
    def clean_user_data(self, raw_user: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Clean a single user data
        
        :param raw_user: Raw user data from crawler
        :return: Cleaned user data or None if invalid
        """
        try:
            # Basic validation
            if not self._validate_user_structure(raw_user):
                self.logger.warning(f"Invalid user structure: {raw_user.get('id', 'unknown')}")
                return None
            
            cleaned = {
                "user_id": self._clean_id(raw_user.get("id", "")),
                "name": self._clean_text(raw_user.get("nickname", "")),
                "avatar": self._clean_url(raw_user.get("avatar", "")),
                "bio": self._clean_text(raw_user.get("bio", "") or raw_user.get("description", "")),
                "followers": self._clean_number(raw_user.get("followers", 0) or raw_user.get("follower_count", 0)),
                "following": self._clean_number(raw_user.get("following", 0) or raw_user.get("following_count", 0)),
                "notes": self._clean_number(raw_user.get("notes", 0) or raw_user.get("note_count", 0)),
                "likes": self._clean_number(raw_user.get("likes", 0) or raw_user.get("liked_count", 0)),
                "level": self._clean_number(raw_user.get("level", 0)),
                "gender": self._clean_gender(raw_user.get("gender", 0)),
                "create_time": self._clean_datetime(raw_user.get("create_time", 0)),
                "update_time": self._clean_datetime(raw_user.get("update_time", 0)),
                "platform": "xiaohongshu"
            }
            
            # Validate cleaned data
            if not self._validate_cleaned_user(cleaned):
                self.logger.warning(f"Invalid cleaned user: {cleaned.get('user_id', 'unknown')}")
                return None
            
            return cleaned
            
        except Exception as e:
            self.logger.error(f"Error cleaning user data: {str(e)}")
            return None
    
    def clean_comment_data(self, raw_comment: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Clean a single comment data
        
        :param raw_comment: Raw comment data from crawler
        :return: Cleaned comment data or None if invalid
        """
        try:
            # Basic validation
            if not self._validate_comment_structure(raw_comment):
                self.logger.warning(f"Invalid comment structure: {raw_comment.get('id', 'unknown')}")
                return None
            
            cleaned = {
                "comment_id": self._clean_id(raw_comment.get("id", "")),
                "note_id": self._clean_id(raw_comment.get("note_id", "")),
                "user_id": self._clean_id(raw_comment.get("user", {}).get("id", "")),
                "user_name": self._clean_text(raw_comment.get("user", {}).get("nickname", "")),
                "content": self._clean_text(raw_comment.get("content", "")),
                "likes": self._clean_number(raw_comment.get("likes", 0) or raw_comment.get("like_count", 0)),
                "create_time": self._clean_datetime(raw_comment.get("time", 0) or raw_comment.get("create_time", 0)),
                "parent_id": self._clean_id(raw_comment.get("parent_id", "")),
                "platform": "xiaohongshu"
            }
            
            # Validate cleaned data
            if not self._validate_cleaned_comment(cleaned):
                self.logger.warning(f"Invalid cleaned comment: {cleaned.get('comment_id', 'unknown')}")
                return None
            
            return cleaned
            
        except Exception as e:
            self.logger.error(f"Error cleaning comment data: {str(e)}")
            return None
    
    def clean_batch_data(self, raw_data: List[Dict[str, Any]], data_type: str) -> List[Dict[str, Any]]:
        """
        Clean a batch of data
        
        :param raw_data: List of raw data
        :param data_type: Type of data (note, user, comment)
        :return: List of cleaned data
        """
        cleaned_data = []
        
        for item in raw_data:
            if data_type == "note":
                cleaned = self.clean_note_data(item)
            elif data_type == "user":
                cleaned = self.clean_user_data(item)
            elif data_type == "comment":
                cleaned = self.clean_comment_data(item)
            else:
                self.logger.error(f"Unknown data type: {data_type}")
                continue
            
            if cleaned:
                cleaned_data.append(cleaned)
        
        return cleaned_data
    
    # Private cleaning methods
    def _clean_id(self, id_str: str) -> str:
        """Clean ID string"""
        return re.sub(r'[^a-zA-Z0-9]', '', str(id_str))
    
    def _clean_text(self, text: str) -> str:
        """Clean text content"""
        if not text:
            return ""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', str(text))
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters at the beginning and end
        text = text.strip()
        return text
    
    def _clean_number(self, num: Any) -> int:
        """Clean number value"""
        try:
            if isinstance(num, str):
                num = re.sub(r'[^0-9]', '', num)
            return max(0, int(num))
        except:
            return 0
    
    def _clean_datetime(self, timestamp: Any) -> str:
        """Clean datetime value"""
        try:
            if isinstance(timestamp, str):
                timestamp = int(timestamp)
            return datetime.fromtimestamp(timestamp).isoformat() if timestamp else ""
        except:
            return ""
    
    def _clean_url(self, url: str) -> str:
        """Clean URL"""
        if not url:
            return ""
        url = str(url).strip()
        if url.startswith("//"):
            url = "https:" + url
        elif not url.startswith("http"):
            url = "https://www.xiaohongshu.com" + url
        return url
    
    def _clean_note_type(self, note_type: str) -> str:
        """Clean note type"""
        valid_types = ["normal", "video", "image", "text"]
        note_type = str(note_type).lower().strip()
        return note_type if note_type in valid_types else "normal"
    
    def _clean_media(self, media: Any) -> Dict[str, List[str]]:
        """Clean media content"""
        result = {"images": [], "videos": []}
        
        if isinstance(media, dict):
            # Video case
            if "url" in media:
                result["videos"].append(self._clean_url(media["url"]))
            elif "play_url" in media:
                result["videos"].append(self._clean_url(media["play_url"]))
        elif isinstance(media, list):
            # Image list case
            for item in media:
                if isinstance(item, dict):
                    if "url" in item:
                        result["images"].append(self._clean_url(item["url"]))
                    elif "src" in item:
                        result["images"].append(self._clean_url(item["src"]))
                elif isinstance(item, str):
                    result["images"].append(self._clean_url(item))
        
        return result
    
    def _clean_location(self, location: Dict[str, Any]) -> Dict[str, Any]:
        """Clean location data"""
        if not isinstance(location, dict):
            return {"name": "", "latitude": 0.0, "longitude": 0.0}
        
        return {
            "name": self._clean_text(location.get("name", "")),
            "latitude": float(location.get("lat", 0.0)),
            "longitude": float(location.get("lng", 0.0))
        }
    
    def _clean_tags(self, tags: List[Any]) -> List[str]:
        """Clean tags"""
        result = []
        for tag in tags:
            if isinstance(tag, dict):
                tag_name = tag.get("name", "") or tag.get("title", "")
            else:
                tag_name = str(tag)
            
            tag_name = self._clean_text(tag_name)
            if tag_name:
                result.append(tag_name)
        
        # Remove duplicates
        return list(set(result))
    
    def _extract_hashtags(self, content: str) -> List[str]:
        """Extract hashtags from content"""
        if not content:
            return []
        
        hashtags = re.findall(r'#(\w+)', content)
        return [tag.strip() for tag in hashtags if tag.strip()]
    
    def _validate_note_structure(self, note: Dict[str, Any]) -> bool:
        """Validate raw note structure"""
        return isinstance(note, dict) and ("id" in note or "note_id" in note)
    
    def _validate_user_structure(self, user: Dict[str, Any]) -> bool:
        """Validate raw user structure"""
        return isinstance(user, dict) and "id" in user
    
    def _validate_comment_structure(self, comment: Dict[str, Any]) -> bool:
        """Validate raw comment structure"""
        return isinstance(comment, dict) and "id" in comment
    
    def _validate_cleaned_note(self, note: Dict[str, Any]) -> bool:
        """Validate cleaned note"""
        return isinstance(note, dict) and note.get("note_id") and len(note.get("note_id", "")) >= 10
    
    def _validate_cleaned_user(self, user: Dict[str, Any]) -> bool:
        """Validate cleaned user"""
        return isinstance(user, dict) and user.get("user_id") and len(user.get("user_id", "")) >= 10
    
    def _validate_cleaned_comment(self, comment: Dict[str, Any]) -> bool:
        """Validate cleaned comment"""
        return isinstance(comment, dict) and comment.get("comment_id") and len(comment.get("comment_id", "")) >= 10
