import pytest
import os
import json
from seer.storage import DataStorage


def test_storage_initialization():
    """测试存储模块初始化"""
    storage = DataStorage()
    assert storage is not None


def test_get_storage_path():
    """测试获取存储路径"""
    storage = DataStorage()
    user_id = "test_user"
    date = "2025-12-20"
    path = storage.get_storage_path(user_id, date)
    assert isinstance(path, str)
    assert user_id in path
    assert date in path


def test_save_metadata(tmp_path):
    """测试保存元数据"""
    storage = DataStorage()
    metadata = {
        "test_key": "test_value",
        "test_list": [1, 2, 3]
    }
    
    # 使用临时目录进行测试
    storage_path = str(tmp_path)
    result = storage.save_metadata(metadata, storage_path)
    
    assert result is True
    
    # 检查文件是否存在且内容正确
    metadata_path = os.path.join(storage_path, "metadata.json")
    assert os.path.exists(metadata_path)
    
    with open(metadata_path, "r", encoding="utf-8") as f:
        saved_metadata = json.load(f)
    
    assert saved_metadata == metadata


def test_save_crawled_data(tmp_path):
    """测试保存爬取数据"""
    storage = DataStorage()
    
    # 创建模拟爬取数据
    crawled_data = {
        "up_info": {
            "username": "test_user",
            "user_id": "user_123",
            "avatar": "https://example.com/avatar.jpg"
        },
        "content_info": {
            "content_id": "content_123",
            "title": "test_title",
            "text": "test_content",
            "publish_time": "2025-12-20",
            "content_type": "text",
            "images": [],
            "videos": []
        },
        "comments": []
    }
    
    # 使用临时目录进行测试
    original_base_dir = storage.base_dir
    storage.base_dir = str(tmp_path)
    
    date = "2025-12-20"
    result = storage.save_crawled_data(crawled_data, date)
    
    # 恢复原始base_dir
    storage.base_dir = original_base_dir
    
    assert result is True
    
    # 检查元数据文件是否存在
    expected_path = os.path.join(str(tmp_path), "user_123", date)
    metadata_path = os.path.join(expected_path, "metadata.json")
    assert os.path.exists(metadata_path)
