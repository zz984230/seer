import json
import execjs
import os

# 获取当前文件所在目录的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))

# 构建静态文件的绝对路径
creator_js_path = os.path.join(current_dir, '../static/xhs_creator_xs.js')
creator_js_path = os.path.abspath(creator_js_path)

# 加载JavaScript文件
try:
    js = execjs.compile(open(creator_js_path, 'r', encoding='utf-8').read())
except Exception as e:
    js = execjs.compile(open(creator_js_path, 'r', encoding='utf-8').read())


def generate_xs(a1, api, data=''):
    ret = js.call('get_request_headers_params', api, data, a1)
    xs, xt = ret['xs'], ret['xt']
    if data:
        data = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
    return xs, xt, data


def get_common_headers():
    return {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0",
        "accept": "application/json, text/plain, */*",
        "Host": "edith.xiaohongshu.com",
        "pragma": "no-cache",
        "cache-control": "no-cache",
        "sec-ch-ua-platform": "\"Windows\"",
        "authorization": "",
        "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Microsoft Edge\";v=\"138\"",
        "sec-ch-ua-mobile": "?0",
        "x-t": "",
        "x-s": "",
        "origin": "https://creator.xiaohongshu.com",
        "sec-fetch-site": "same-site",
        "sec-fetch-mode": "cors",
        "sec-fetch-dest": "empty",
        "referer": "https://creator.xiaohongshu.com/",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "priority": "u=1, i"
    }


def splice_str(api, params):
    url = api + '?'
    for key, value in params.items():
        if value is None:
            value = ''
        url += key + '=' + value + '&'
    return url[:-1]