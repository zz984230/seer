import pytest
from seer.parser import XiaohongshuParser


def test_parser_initialization():
    """测试解析器初始化"""
    parser = XiaohongshuParser()
    assert parser is not None


def test_parse_empty_content():
    """测试解析空内容"""
    parser = XiaohongshuParser()
    result = parser.parse_page("")
    assert result is None


def test_parse_sample_content():
    """测试解析示例HTML内容"""
    sample_html = """
    <html>
    <head><title>Test Page</title></head>
    <body>
        <div class="user-name">Test User</div>
        <img class="avatar" src="https://example.com/avatar.jpg">
        <h1 class="title">Test Title</h1>
        <div class="content">Test content here.</div>
        <img class="image" src="https://example.com/image1.jpg">
        <img class="image" src="https://example.com/image2.jpg">
        <video src="https://example.com/video1.mp4"></video>
        <div class="comments">
            <div class="comment-item">
                <span class="username">Commenter1</span>
                <div class="comment-content">Great post!</div>
                <span class="comment-time">1 hour ago</span>
            </div>
            <div class="comment-item">
                <span class="username">Commenter2</span>
                <div class="comment-content">Thanks!</div>
                <span class="comment-time">30 minutes ago</span>
            </div>
        </div>
    </body>
    </html>
    """
    
    parser = XiaohongshuParser()
    result = parser.parse_page(sample_html)
    
    assert result is not None
    assert isinstance(result, dict)
    
    # 测试UP主信息解析
    assert "up_info" in result
    assert result["up_info"]["username"] == "Test User"
    assert result["up_info"]["avatar"] == "https://example.com/avatar.jpg"
    
    # 测试内容信息解析
    assert "content_info" in result
    assert result["content_info"]["title"] == "Test Title"
    assert result["content_info"]["text"] == "Test content here."
    assert len(result["content_info"]["images"]) == 2
    assert len(result["content_info"]["videos"]) == 1
    assert result["content_info"]["content_type"] == "video"
    
    # 测试评论解析
    assert "comments" in result
    assert len(result["comments"]) == 2
    assert result["comments"][0]["commenter"] == "Commenter1"
    assert result["comments"][0]["content"] == "Great post!"
