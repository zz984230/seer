from seer.crawler import XiaohongshuCrawler

# 初始化爬虫
crawler = XiaohongshuCrawler()

# 爬取用户页面
url = "https://www.xiaohongshu.com/user/profile/5b6150c56b58b741e26b8c7f?xsec_token=ABhU-3wtni9-4VBCkbuCZgesNnJlCAcu5IcuV3JQJzUSo%3D&xsec_source=pc_search"
html_content = crawler.get_page_content(url)

# 保存HTML内容到文件
with open("user_page.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("HTML内容已保存到user_page.html文件")
