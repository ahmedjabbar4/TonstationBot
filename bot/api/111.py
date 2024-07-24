import requests
import json
from better_proxy import Proxy
import random
url = "https://tonstation.app/userprofile/api/v1/users/auth"

payload = json.dumps({
  "query_id": "AAFCf8UYAwAAAEJ_xRh-INjJ",
  "user": {
    "id": 6858047298,
    "first_name": "If Sub",
    "last_name": "333",
    "username": "wnddan",
    "language_code": "zh-hant",
    "allows_write_to_pm": True
  },
  "auth_date": "1721638103",
  "hash": "1172c5ab46a32af7d675802f58188608848eb3996cf98db7c3cf20d20024c8a5"
})
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
print(proxy.as_proxies_dict)
response = requests.request("POST", url, headers=headers, data=payload,proxies=proxy.as_proxies_dict)
print(response.text)
