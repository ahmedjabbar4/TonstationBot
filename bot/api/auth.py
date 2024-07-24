import aiohttp
from typing import Any
import json
import urllib.parse
from bot.api.http import handle_error, make_post_request
from bot.utils.logger import logger
from better_proxy import Proxy
import random
import requests
headers = {
  'accept': '*/*',
  'accept-encoding': 'gzip, deflate, br, zstd',
  'accept-language': 'zh,zh-CN;q=0.9,en-US;q=0.8,en;q=0.7',
  'connection': 'keep-alive',
  'content-type': 'application/json',
  'host': 'tonstation.app',
  'origin': 'https://tonstation.app',
  'referer': 'https://tonstation.app/app/',
  'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="122", "Android WebView";v="122"',
  'sec-ch-ua-mobile': '?1',
  'sec-ch-ua-platform': '"Android"',
  'sec-fetch-dest': 'empty',
  'sec-fetch-mode': 'cors',
  'sec-fetch-site': 'same-origin',
  'user-agent': 'Mozilla/5.0 (Linux; Android 14; 2304FPN6DC Build/UKQ1.230804.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/126.0.6478.134 Mobile Safari/537.36',
  'x-requested-with': 'app.nicegram'
}
proxies=Proxy.from_file("proxy.txt")
proxy=proxies[random.randrange(len(proxies))]

async def login(
    http_client: aiohttp.ClientSession, tg_web_data: str
) -> Any | None:
    response_text = ""
    try:
        params = dict(urllib.parse.parse_qsl(tg_web_data, keep_blank_values=True)) 
        params['user'] = json.loads(urllib.parse.unquote(params['user']))
        # 构建最终的 payload
        payload = json.dumps({
            "query_id": params['query_id'],
            "user": params['user'],
            "auth_date": params['auth_date'],
            "hash": params['hash'],
        })
        user_id=params['user']['id']
        # response = await http_client.post(url='https://tonstation.app/userprofile/api/v1/users/auth', data=payload)
        response = requests.request("POST", "https://tonstation.app/userprofile/api/v1/users/auth", headers=headers, data=payload,proxies=proxy.as_proxies_dict)
        response_text = response.text
        logger.info(response_text)
        response.raise_for_status()
        response_json = json.loads(response_text)
        return response_json,user_id
    except Exception as error:
        await handle_error(error, response_text, 'getting Access Token')
        return None
