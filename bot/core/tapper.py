import asyncio
import heapq
import math
from random import randint
from time import time
from datetime import datetime, timedelta, timezone
from bot.api.http import handle_error, make_post_request
from aiocfscrape import CloudflareScraper
import aiohttp
from aiohttp_proxy import ProxyConnector
from bot.api.auth import login
from bot.api.farm import claim_farm, start_farm
from bot.api.info import get_info
from pyrogram import Client
import json
from bot.config import settings
from bot.utils.logger import logger
from bot.exceptions import InvalidSession

from bot.utils.scripts import get_headers, is_jwt_valid
from bot.utils.tg_web_data import get_tg_web_data
from bot.utils.proxy import check_proxy


class Tapper:
    def __init__(self, tg_client: Client):
        self.session_name = tg_client.name
        self.tg_client = tg_client
        self.user_id = ''

    async def get_task_list(self,http_client: aiohttp.ClientSession) :
        res=await http_client.get(url="https://tonstation.app/farming/api/v1/farming/{}/running".format(self.user_id))
        response_text = await res.text()
        response_json = json.loads(response_text)
        return response_json,res.status
    async def claim_task(self,http_client: aiohttp.ClientSession,task_id:str) :
        data={"userId":self.user_id,
              "taskId": "1"}
        res=await http_client.post(url="https://tonstation.app/farming/api/v1/farming/start",data=data)
        response_text = await res.text()
        response_json = json.loads(response_text)
        return response_json
    #     return task_list
    # async def submit_claim(self,http_client: aiohttp.ClientSession,task_list :list ) -> None:
    #     if '668fbec8647177930d0ac0bc' in task_list:
    #         bind_wallet_url=f'https://tg-bot-tap.laborx.io/api/v1/me/ton/info'
    #         wallet_json= {"address":"UQAatGc8y2TtYjnSxb1jaCstvo4HdDAyIGv6G05Bncfl5lPH"}
    #         res =  await make_post_request(http_client,bind_wallet_url,wallet_json,"钱包信息更新")
    #     for i in task_list:
    #         sub_url = f'https://tg-bot-tap.laborx.io/api/v1/tasks/{i}/submissions'
    #         claim_url2 = f'https://tg-bot-tap.laborx.io/api/v1/tasks/{i}/claims'
    #         res = await http_client.post(url=sub_url,json={})
    #         text=res.text()

    #         # if "OK" in text or res.status ==400:
    #         response2_json =  await http_client.post(
    #             url=claim_url2,
    #             json={})
    #     return None   
    
    async def run(self, proxy: str | None) -> None:
        token = ""
        sleep_time=0
        headers = get_headers(name=self.tg_client.name)
        logger.info(headers)
        proxy_conn = ProxyConnector().from_url(proxy) if proxy else None
        http_client = aiohttp.ClientSession(headers=headers, connector=proxy_conn)
        if proxy:
            await check_proxy(
                http_client=http_client,
                proxy=proxy,
                session_name=self.session_name,
            )

        while True:
            try:
                if http_client.closed:
                    if proxy_conn:
                        if not proxy_conn.closed:
                            proxy_conn.close()

                    proxy_conn = (
                        ProxyConnector().from_url(proxy) if proxy else None
                    )
                http_client = aiohttp.ClientSession(headers=headers, connector=proxy_conn)
                tg_web_data = await get_tg_web_data(
                tg_client=self.tg_client,
                proxy=proxy,
                session_name=self.session_name,
                )
                http_client = aiohttp.ClientSession(
                        headers=headers, connector=proxy_conn
                    )
                if not is_jwt_valid(http_client.headers.get("Authorization", "")):
                    # Remove the Authorization header if it exists
                    if "Authorization" in http_client.headers:
                        del http_client.headers["Authorization"]

                    # Attempt to log in and get new authentication data
                    login_data,self.user_id = await login(http_client=http_client, tg_web_data=tg_web_data)
                    accessToken = login_data.get('accessToken')
                    http_client.headers[
                        'Authorization'
                    ] = f'Bearer {accessToken}'

                    # Check if the new Authorization token is present in the headers
                    if not http_client.headers.get("Authorization"):
                        logger.error(
                            f"{self.session_name} | Failed to fetch token | Sleeping for 60s")
                        await asyncio.sleep(delay=60)
                        continue
                task_info,task_status= await self.get_task_list(http_client=http_client)
                logger.info(task_info)
                try:
                    if task_info.get("data"):
                        if task_info.get("data")[0]["isClaimed"]:
                            claim = await claim_farm(http_client=http_client)
                            sleep_between_clicks = randint(
                                a=settings.SLEEP_BETWEEN_TAP[0],
                                b=settings.SLEEP_BETWEEN_TAP[1],
                                )
                            logger.info(f'Sleep {sleep_between_clicks}s')
                            f_info = await start_farm(http_client=http_client,_id=task_info.get("data")[0]["_id"])
                            sleep_time = math.ceil(sleep_between_clicks)
                        
                        else:
                            end_time=task_info.get("data")[0]["timeEnd"]
                            farm_end_time = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
                            remaining_time = farm_end_time - datetime.now(timezone.utc)
                            sleep_time=math.ceil(remaining_time.total_seconds())
                    elif task_status==304:
                        claim = await claim_farm(http_client=http_client)
                        end_time=task_info.get("data")["timeEnd"]
                        farm_end_time = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
                        remaining_time = farm_end_time - datetime.now(timezone.utc)
                        sleep_time=math.ceil(remaining_time.total_seconds())
                    await http_client.close()
                    if proxy_conn:
                        if not proxy_conn.closed:
                            proxy_conn.close()

                    logger.info(
                        f'{self.session_name} | Sleep {sleep_time:,}s'
                    )
                    await asyncio.sleep(delay=sleep_time)  
                except Exception as e:
                    
                    logger.error(e)                
                
                # task_list=await self.get_task_list(http_client=http_client)
                # if len(task_list)>1:
                #     await self.submit_claim(task_list=task_list,http_client=http_client)
                # if task_status==304 or (task_status==200&task_info):
                #     claim = await claim_farm(http_client=http_client)
                #     end_time=task_info.get("data")["timeEnd"]
                #     farm_end_time = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
                #     remaining_time = farm_end_time - datetime.now(timezone.utc)
                #     sleep_time=math.ceil(remaining_time.total_seconds())
                # else:
                #     if task_info.get("data")[0]["isClaimed"]:
                #         claim = await claim_farm(http_client=http_client)
                #         sleep_between_clicks = randint(
                #             a=settings.SLEEP_BETWEEN_TAP[0],
                #             b=settings.SLEEP_BETWEEN_TAP[1],
                #             )
                #         logger.info(f'Sleep {sleep_between_clicks}s')
                #         f_info = await start_farm(http_client=http_client,_id=task_info.get("data")[0]["_id"])
                #         sleep_time = math.ceil(sleep_between_clicks)
                        
                #     else:
                #         end_time=task_info.get("data")[0]["timeEnd"]
                #         farm_end_time = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
                #         remaining_time = farm_end_time - datetime.now(timezone.utc)
                #         sleep_time=math.ceil(remaining_time.total_seconds())


            except InvalidSession as error:
                raise error

            except Exception as error:
                logger.error(f'{self.session_name} | Unknown error: {error}')
                await asyncio.sleep(delay=3)

            else:
                sleep_between_clicks = randint(
                    a=settings.SLEEP_BETWEEN_TAP[0],
                    b=settings.SLEEP_BETWEEN_TAP[1],
                )
                logger.info(f'Sleep {sleep_between_clicks}s')
                await asyncio.sleep(delay=sleep_between_clicks)


async def run_tapper(tg_client: Client, proxy: str | None):
    try:
        await Tapper(tg_client=tg_client).run(proxy=proxy)
    except InvalidSession:
        logger.error(f'{tg_client.name} | Invalid Session')
