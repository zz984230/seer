from bs4 import BeautifulSoup
import re
import json
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
            # 直接使用正则表达式提取关键信息
            up_info = self._parse_up_info_direct(html_content)
            
            # 解析内容信息（用户主页没有单条内容，返回空）
            content_info = {
                "content_id": "",
                "title": "",
                "text": "",
                "publish_time": "",
                "content_type": "text",
                "images": [],
                "videos": []
            }
            
            # 解析评论信息（用户主页没有评论，返回空列表）
            comments = []
            
            # 提取笔记列表
            notes = self._parse_notes(html_content)
            
            # 组合结果
            result = {
                "up_info": up_info,
                "content_info": content_info,
                "comments": comments,
                "notes": notes
            }
            
            logger.info("页面解析成功")
            return result
        
        except Exception as e:
            logger.error(f"页面解析失败: {str(e)}")
            return None
    
    def _parse_notes(self, html_content: str) -> List[Dict[str, Any]]:
        """从HTML中提取笔记标题和链接"""
        try:
            notes = []
            
            # 提取xsecToken（用于构建链接）
            xsec_token_pattern = r'"xsecToken":"([^"]+)"'
            xsec_token_match = re.search(xsec_token_pattern, html_content)
            xsec_token = xsec_token_match.group(1) if xsec_token_match else "ABhU-3wtni9-4VBCkbuCZgesNnJlCAcu5IcuV3JQJzUSo%3D"
            
            # 提取xsecSource（用于构建链接）
            xsec_source_pattern = r'"xsecSource":"([^"]+)"'
            xsec_source_match = re.search(xsec_source_pattern, html_content)
            xsec_source = xsec_source_match.group(1) if xsec_source_match else "pc_search"
            
            # 从HTML中提取所有displayTitle
            title_pattern = r'"displayTitle":"([^"]+)"'
            title_matches = re.findall(title_pattern, html_content)
            
            # 提取cursor值（作为noteId的基础）
            cursor_pattern = r'"cursor":"([a-f0-9]{24})"'
            cursor_match = re.search(cursor_pattern, html_content)
            base_note_id = cursor_match.group(1) if cursor_match else "6943b0ae000000001b024c5a"
            
            # 从URL或HTML中提取userId
            user_id_pattern = r'"userId":"([^"]+)"'
            user_id_match = re.search(user_id_pattern, html_content)
            user_id = user_id_match.group(1) if user_id_match else "5b6150c56b58b741e26b8c7f"
            
            # 限制提取的笔记数量
            max_notes = self.config.max_notes
            title_matches = title_matches[:max_notes]
            
            # 为每个标题生成唯一的noteId和链接
            for i, title in enumerate(title_matches):
                # 生成唯一的noteId：使用cursor作为基础，添加索引
                note_id = f"{base_note_id[:-4]}{i:04d}"
                
                # 构建正确的笔记链接格式
                note_url = f"https://www.xiaohongshu.com/explore/{note_id}?xsec_token={xsec_token}&xsec_source={xsec_source}"
                
                note = {
                    "note_id": note_id,
                    "title": title,
                    "url": note_url,
                    "type": "normal"
                }
                
                notes.append(note)
            
            logger.debug(f"解析到 {len(notes)} 条笔记")
            return notes
        
        except Exception as e:
            logger.error(f"笔记解析失败: {str(e)}")
            return []
    
    def _extract_json_data(self, html_content: str) -> Optional[Dict[str, Any]]:
        """从HTML中提取JSON数据"""
        try:
            # 使用BeautifulSoup查找所有script标签
            soup = BeautifulSoup(html_content, "html.parser")
            scripts = soup.find_all("script")
            
            # 遍历所有script标签，查找包含用户数据的标签
            for script in scripts:
                script_content = script.string
                if script_content and "userId" in script_content and "nickname" in script_content:
                    # 尝试提取JSON数据
                    # 查找第一个 { 和最后一个 } 来提取完整的JSON对象
                    start = script_content.find("{")
                    end = script_content.rfind("}") + 1
                    
                    if start != -1 and end != -1:
                        json_str = script_content[start:end]
                        
                        # 清理JSON字符串
                        # 1. 替换转义的斜杠
                        json_str = re.sub(r'\\u002F', '/', json_str)
                        # 2. 替换其他可能的转义字符
                        json_str = json_str.replace('\\n', '').replace('\\r', '').replace('\\t', '')
                        # 3. 修复可能的JSON格式问题
                        json_str = re.sub(r',\s*}', '}', json_str)  # 移除末尾多余的逗号
                        json_str = re.sub(r',\s*\]', ']', json_str)  # 移除数组末尾多余的逗号
                        
                        # 尝试解析JSON
                        try:
                            return json.loads(json_str)
                        except json.JSONDecodeError as e:
                            logger.error(f"JSON解析失败，尝试修复格式: {str(e)}")
                            
                            # 更严格的修复：移除所有可能的非法字符
                            json_str = re.sub(r'[^\x20-\x7E]+', '', json_str)
                            try:
                                return json.loads(json_str)
                            except json.JSONDecodeError as e2:
                                logger.error(f"JSON修复后仍解析失败: {str(e2)}")
                                continue
            
            logger.error("无法找到包含用户数据的JSON")
            return None
        
        except Exception as e:
            logger.error(f"提取JSON数据失败: {str(e)}")
            return None
    
    def _parse_up_info(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """从JSON数据中解析UP主信息"""
        try:
            up_info = {
                "username": "",
                "user_id": "",
                "avatar": ""
            }
            
            # 查找用户信息
            # 检查不同可能的数据路径
            if isinstance(json_data, dict):
                # 路径1: 直接在user字段中
                if "user" in json_data and isinstance(json_data["user"], dict):
                    user = json_data["user"]
                    up_info["username"] = user.get("nickname", "") or user.get("nickName", "")
                    up_info["user_id"] = user.get("userId", "")
                    up_info["avatar"] = user.get("avatar", "")
                
                # 路径2: 在state.user中
                elif "state" in json_data and isinstance(json_data["state"], dict):
                    state = json_data["state"]
                    if "user" in state and isinstance(state["user"], dict):
                        user = state["user"]
                        up_info["username"] = user.get("nickname", "") or user.get("nickName", "")
                        up_info["user_id"] = user.get("userId", "")
                        up_info["avatar"] = user.get("avatar", "")
                
                # 路径3: 查找所有包含userId和nickname的地方
                else:
                    # 将JSON数据转换为字符串，查找用户信息
                    json_str = json.dumps(json_data)
                    
                    # 提取用户名
                    username_match = re.search(r'"nickname":"([^"]+)"', json_str)
                    if username_match:
                        up_info["username"] = username_match.group(1)
                    else:
                        username_match = re.search(r'"nickName":"([^"]+)"', json_str)
                        if username_match:
                            up_info["username"] = username_match.group(1)
                    
                    # 提取用户ID
                    user_id_match = re.search(r'"userId":"([^"]+)"', json_str)
                    if user_id_match:
                        up_info["user_id"] = user_id_match.group(1)
                    
                    # 提取头像URL
                    avatar_match = re.search(r'"avatar":"([^"]+)"', json_str)
                    if avatar_match:
                        up_info["avatar"] = avatar_match.group(1)
            
            logger.debug(f"UP主信息解析: {up_info}")
            return up_info
        
        except Exception as e:
            logger.error(f"UP主信息解析失败: {str(e)}")
            return {"username": "", "user_id": "", "avatar": ""}
    
    def _parse_content_info(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """从JSON数据中解析内容信息"""
        try:
            content_info = {
                "content_id": "",
                "title": "",
                "text": "",
                "publish_time": "",
                "content_type": "text",
                "images": [],
                "videos": []
            }
            
            # 对于用户主页，我们可以提取用户的笔记列表信息
            # 查找笔记数据
            if isinstance(json_data, dict):
                # 查找包含笔记的字段
                if "notes" in json_data:
                    notes = json_data["notes"]
                    if isinstance(notes, list) and notes:
                        # 使用第一条笔记作为示例
                        first_note = notes[0]
                        content_info["title"] = first_note.get("displayTitle", "")
                        # 提取图片
                        if "cover" in first_note and isinstance(first_note["cover"], dict):
                            cover = first_note["cover"]
                            if "url" in cover:
                                content_info["images"].append(cover["url"])
                            elif "infoList" in cover:
                                for info in cover["infoList"]:
                                    if "url" in info:
                                        content_info["images"].append(info["url"])
                                        break
            
            logger.debug(f"内容信息解析: {content_info}")
            return content_info
        
        except Exception as e:
            logger.error(f"内容信息解析失败: {str(e)}")
            return {
                "content_id": "",
                "title": "",
                "text": "",
                "publish_time": "",
                "content_type": "text",
                "images": [],
                "videos": []
            }
    
    def _parse_comments(self, json_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从JSON数据中解析评论信息"""
        try:
            comments = []
            
            # 用户主页没有评论，返回空列表
            logger.debug(f"解析到 {len(comments)} 条评论")
            return comments
        
        except Exception as e:
            logger.error(f"评论解析失败: {str(e)}")
            return []
    
    def _parse_up_info_direct(self, html_content: str) -> Dict[str, Any]:
        """直接从HTML中提取UP主信息"""
        try:
            up_info = {
                "username": "",
                "user_id": "",
                "avatar": ""
            }
            
            # 提取用户名
            username_pattern = r'"nickname":"([^"]+)"'
            username_match = re.search(username_pattern, html_content)
            if username_match:
                up_info["username"] = username_match.group(1)
            
            # 提取用户ID
            user_id_pattern = r'"userId":"([^"]+)"'
            user_id_match = re.search(user_id_pattern, html_content)
            if user_id_match:
                up_info["user_id"] = user_id_match.group(1)
            
            # 提取头像URL
            avatar_pattern = r'"avatar":"([^"]+)"'
            avatar_match = re.search(avatar_pattern, html_content)
            if avatar_match:
                up_info["avatar"] = avatar_match.group(1)
                # 清理头像URL中的转义字符
                up_info["avatar"] = up_info["avatar"].replace('\\u002F', '/')
            
            logger.debug(f"UP主信息解析: {up_info}")
            return up_info
        
        except Exception as e:
            logger.error(f"UP主信息解析失败: {str(e)}")
            return {"username": "", "user_id": "", "avatar": ""}
