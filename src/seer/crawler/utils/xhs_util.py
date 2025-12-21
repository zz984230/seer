import json
import math
import random
import execjs
import os
from loguru import logger
from seer.crawler.utils.cookie_util import trans_cookies

# 获取静态文件目录的绝对路径
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static')
static_dir = os.path.abspath(static_dir)

# 构建静态文件的绝对路径
xs_js_path = os.path.join(static_dir, 'xhs_xs_xsc_56.js')
xray_js_path = os.path.join(static_dir, 'xhs_xray.js')
xray_pack1_js_path = os.path.join(static_dir, 'xhs_xray_pack1.js')
xray_pack2_js_path = os.path.join(static_dir, 'xhs_xray_pack2.js')

# 读取并预处理xhs_xray.js文件，替换其中的相对路径
with open(xray_js_path, 'r', encoding='utf-8') as f:
    xray_js_content = f.read()
# 替换JavaScript文件中的相对路径为绝对路径
xray_js_content = xray_js_content.replace(
    "require('./xhs_xray_pack1.js');", 
    f"require('{xray_pack1_js_path.replace('\\', '/')}');"
)
xray_js_content = xray_js_content.replace(
    "require('../static/xhs_xray_pack1.js');", 
    f"require('{xray_pack1_js_path.replace('\\', '/')}');"
)
xray_js_content = xray_js_content.replace(
    "require('./static/xhs_xray_pack1.js');", 
    f"require('{xray_pack1_js_path.replace('\\', '/')}');"
)
xray_js_content = xray_js_content.replace(
    "require('./xhs_xray_pack2.js');", 
    f"require('{xray_pack2_js_path.replace('\\', '/')}');"
)
xray_js_content = xray_js_content.replace(
    "require('../static/xhs_xray_pack2.js');", 
    f"require('{xray_pack2_js_path.replace('\\', '/')}');"
)
xray_js_content = xray_js_content.replace(
    "require('./static/xhs_xray_pack2.js');", 
    f"require('{xray_pack2_js_path.replace('\\', '/')}');"
)

try:
    js = execjs.compile(open(xs_js_path, 'r', encoding='utf-8').read())
except Exception as e:
    js = execjs.compile(open(xs_js_path, 'r', encoding='utf-8').read())

try:
    xray_js = execjs.compile(xray_js_content)
except Exception as e:
    xray_js = execjs.compile(xray_js_content)

def generate_x_b3_traceid(len=16):
    x_b3_traceid = ""
    for t in range(len):
        x_b3_traceid += "abcdef0123456789"[math.floor(16 * random.random())]
    return x_b3_traceid

def generate_xs_xs_common(a1, api, data='', method='POST'):
    try:
        ret = js.call('get_request_headers_params', api, data, a1, method)
        if isinstance(ret, dict):
            xs, xt, xs_common = ret['xs'], ret['xt'], ret['xs_common']
        else:
            logger.error(f"JavaScript返回的不是字典类型: {type(ret)}")
            raise Exception(f"JavaScript返回的不是字典类型: {type(ret)}")
    except Exception as e:
        logger.error(f"调用JavaScript函数出错: {str(e)}")
        raise e
    return xs, xt, xs_common

def generate_xs(a1, api, data=''):
    ret = js.call('get_xs', api, data, a1)
    xs, xt = ret['X-s'], ret['X-t']
    return xs, xt

def generate_xray_traceid():
    return xray_js.call('traceId')
def get_common_headers():
    return {
        "authority": "www.xiaohongshu.com",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "zh-CN,zh;q=0.9",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "referer": "https://www.xiaohongshu.com/",
        "sec-ch-ua": "\"Chromium\";v=\"122\", \"Not(A:Brand\";v=\"24\", \"Google Chrome\";v=\"122\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
def get_request_headers_template():
    return {
        "authority": "edith.xiaohongshu.com",
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "cache-control": "no-cache",
        "content-type": "application/json;charset=UTF-8",
        "origin": "https://www.xiaohongshu.com",
        "pragma": "no-cache",
        "referer": "https://www.xiaohongshu.com/",
        "sec-ch-ua": "\"Not A(Brand\";v=\"99\", \"Microsoft Edge\";v=\"121\", \"Chromium\";v=\"121\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
        "x-b3-traceid": "",
        "x-mns": "unload",
        "x-s": "",
        "x-s-common": "",
        "x-t": "",
        "x-xray-traceid": generate_xray_traceid()
    }

def generate_headers(a1, api, data='', method='POST'):
    xs, xt, xs_common = generate_xs_xs_common(a1, api, data, method)
    x_b3_traceid = generate_x_b3_traceid()
    headers = get_request_headers_template()
    headers['x-s'] = xs
    headers['x-t'] = str(xt)
    headers['x-s-common'] = xs_common
    headers['x-b3-traceid'] = x_b3_traceid
    if data:
        data = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
    return headers, data

def generate_request_params(cookies_str, api, data='', method='POST'):
    cookies = trans_cookies(cookies_str)
    if 'a1' not in cookies:
        logger.error("cookies中没有找到a1键")
        raise Exception("cookies中没有找到a1键")
    a1 = cookies['a1']
    try:
        headers_result, data_result = generate_headers(a1, api, data, method)
        headers = headers_result
        data = data_result
    except Exception as e:
        logger.error(f"调用generate_headers出错: {str(e)}")
        raise e
    return headers, cookies, data

def splice_str(api, params):
    url = api + '?'
    for key, value in params.items():
        if value is None:
            value = ''
        url += key + '=' + value + '&'
    return url[:-1]

