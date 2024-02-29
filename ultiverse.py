import base64
import json
import sys
from curl_cffi.requests import AsyncSession
import asyncio
from loguru import logger
from eth_account.messages import encode_defunct
from web3 import AsyncWeb3

logger.remove()
logger.add(sys.stdout, colorize=True, format="<g>{time:HH:mm:ss:SSS}</g> | <c>{level}</c> | <level>{message}</level>")


class Solver:
    def __init__(self, userToken, siteKey):
        self.http = AsyncSession(timeout=120)
        self.siteKey = siteKey
        self.userToken = userToken

    async def nocaptcha(self, captcha_rqdata):
        try:
            headers = {
                'User-Token': self.userToken,
                'Developer-Id': 'dwBf1P'
            }
            json_data = {
                'sitekey': self.siteKey,
                'referer': 'https://discord.com',
                'rqdata': captcha_rqdata,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            }
            resp = await self.http.post('http://api.nocaptcha.io/api/wanda/hcaptcha/universal', headers=headers, json=json_data)
            if resp.status_code == 200 and resp.json()['status'] == 1:
                return resp.json()['data']['generated_pass_UUID']
            else:
                return None
        except Exception as e:
            logger.error(e)
            return None


class Discord:
    def __init__(self, address, token, userToken):
        prop = {
            "os": "Mac OS X",
            "browser": "Chrome",
            "device": "",
            "system_locale": "zh-CN",
            "browser_user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "browser_version": "120.0.0.0",
            "os_version": "10.15.7",
            "referrer": "https://mission.ultiverse.io/",
            "referring_domain": "mission.ultiverse.io",
            "referrer_current": "",
            "referring_domain_current": "",
            "release_channel": "stable",
            "client_build_number": 269166,
            "client_event_source": None
        }
        _super = base64.b64encode(json.dumps(prop, separators=(',', ':')).encode()).decode()
        headers = {
            'Accept-Language': 'zh-CN,zh;q=0.7',
            'Authority': 'discord.com',
            'Content-Type': 'application/json',
            'Origin': 'https://discord.com',
            'Referer': 'https://discord.com/register',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Brave";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': "macOS",
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Gpc': '1',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'X-Debug-Options': 'bugReporterEnabled',
            'X-Discord-Locale': 'en-US',
            'X-Discord-Timezone': 'Asia/Shanghai',
            'X-Super-Properties': _super,
            'Authorization': token,
            'Accept-Encoding': 'gzip, deflate'
        }
        jsonContext = {
            "location": "Join Guild",
            "location_guild_id": "947538592018878484",
            "location_channel_id": "947551612694564914",
            "location_channel_type": 0
        }
        self.xContext = base64.b64encode(json.dumps(jsonContext, separators=(',', ':')).encode()).decode()
        self.Discord = AsyncSession(headers=headers, timeout=120, impersonate="chrome120")
        self.captchaKey, self.address, self.userToken = None, address, userToken

    async def get_cookie(self):
        try:
            res = await self.Discord.get('https://discord.com')
            if res.status_code == 200:
                return True
            return False
        except Exception as e:
            logger.error(f'获取Discord Cookie异常：{e}')
            return False

    async def joiner(self):
        payload = {'session_id': None}
        try:
            if self.captchaKey is not None:
                self.Discord.headers.update({'X-Captcha-Key': self.captchaKey})
            response = await self.Discord.post(f'https://discord.com/api/v9/invites/ultiverse', json=payload)
            if response.status_code == 200:
                logger.success(f'[{self.address}] 加入服务器成功 ')
                return True
            elif response.status_code == 401:
                logger.error(f'[{self.address}] Token错误')
            elif response.status_code == 403:
                logger.error(f'[{self.address}] Token被锁定')
            elif response.status_code == 400:
                logger.error(f'[{self.address}] 需要Hcapt')
                captcha_rqdata = response.json()['captcha_rqdata']
                captcha_rqtoken = response.json()['captcha_rqtoken']
                self.Discord.headers.update({'X-Captcha-Rqtoken': captcha_rqtoken})
                solver = Solver(userToken=self.userToken, siteKey='a9b5fb07-92ff-493f-86fe-352a2803b3df')
                self.captchaKey = await solver.nocaptcha(captcha_rqdata)
                if self.captchaKey is not None:
                    return await self.joiner()
            else:
                logger.error(f'[{self.address}] 加入服务器失败 {response.text}')
            return False
        except Exception as error:
            logger.error(f'[{self.address}] 加入服务器异常：{error}')
            return False

    async def authorize(self):
        try:
            params = {
                'client_id': '1038062301871358022',
                'response_type': 'code',
                'redirect_uri': 'https://mission.ultiverse.io',
                'scope': 'identify email guilds guilds.members.read',
                'state': 'eyJ0eXBlIjoiZGlzY29yZCIsInRhc2tJZCI6NTI1LCJoYXNoIjoiTVVJdFZUSkVUWHd4TnpBMk1UWTRNRFE0TlRNMiJ9'
            }
            json_data = {
                "permissions": "0",
                "authorize": True,
                "integration_type": 0
            }
            res = await self.Discord.post('https://discord.com/api/v9/oauth2/authorize', params=params, json=json_data)
            if res.status_code == 200 and 'location' in res.text:
                location = res.json()['location']
                code = location.split('code=')[1].split('&')[0]
                return code
            logger.error(f'[{self.address}] 获取Discord授权失败：{res.text}')
            return None
        except Exception as e:
            logger.error(f'[{self.address}] 绑定discord异常：{e}')
            return None


class Twitter:
    def __init__(self, auth_token, code_challenge):
        self.code_challenge, self.auth_token = code_challenge, auth_token
        bearer_token = "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"
        defaulf_headers = {
            "authority": "twitter.com",
            "origin": "https://twitter.com",
            "x-twitter-active-user": "yes",
            "x-twitter-client-language": "en",
            "authorization": bearer_token,
        }
        defaulf_cookies = {"auth_token": auth_token}
        self.Twitter = AsyncSession(headers=defaulf_headers, cookies=defaulf_cookies, timeout=120)
        self.auth_code = None

    async def get_auth_code(self):
        try:
            params = {
                'code_challenge': self.code_challenge,
                'code_challenge_method': 'plain',
                'client_id': 'Vm1EeUVfU1BIejQ5MWQ5emRnOTk6MTpjaQ',
                'redirect_uri': 'https://mission.ultiverse.io',
                'response_type': 'code',
                'scope': 'tweet.read tweet.write users.read follows.read follows.write offline.access like.read like.write',
                'state': 'eyJ0eXBlIjoidHdpdHRlciIsInRhc2tJZCI6NTI1LCJoYXNoIjoiTVVJdFZUSkVUWHd4TnpBMk1UWTRNRFE0TlRNMiJ9'
            }
            response = await self.Twitter.get('https://twitter.com/i/api/2/oauth2/authorize', params=params)
            if "code" in response.json() and response.json()["code"] == 353:
                self.Twitter.headers.update({"x-csrf-token": response.cookies["ct0"]})
                return await self.get_auth_code()
            elif 'auth_code' in response.json():
                self.auth_code = response.json()['auth_code']
                return True
            logger.error(f'{self.auth_token} 获取auth_code失败')
            return False
        except Exception as e:
            logger.error(e)
            return False

    async def twitter_authorize(self):
        try:
            if not await self.get_auth_code():
                return False
            data = {
                'approval': 'true',
                'code': self.auth_code,
            }
            response = await self.Twitter.post('https://twitter.com/i/api/2/oauth2/authorize', data=data)
            if 'redirect_uri' in response.text:
                return True
            logger.error(f'{self.auth_token}  推特授权失败')
            return False
        except Exception as e:
            logger.error(f'{self.auth_token}  推特授权异常：{e}')
            return False


class Ultiverse:
    def __init__(self, private_key, Nickname):
        self.Nickname = Nickname
        headers = {
            "Referer": "https://pilot.ultiverse.io/",
            "Origin": "https://pilot.ultiverse.io",
            "Ul-Auth-Api-Key": "YWktYWdlbnRAZFd4MGFYWmxjbk5s",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        self.http = AsyncSession(timeout=120, headers=headers, impersonate="chrome120")
        self.web3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider('https://opbnb-rpc.publicnode.com'))
        self.account = self.web3.eth.account.from_key(private_key)
        self.http.headers.update({"Ul-Auth-Address": self.account.address})
        abi = [
            {
                "inputs": [
                    {"internalType": "uint256", "name": "deadline", "type": "uint256"},
                    {"internalType": "bytes32", "name": "attributeHash", "type": "bytes32"},
                    {"internalType": "bytes", "name": "signature", "type": "bytes"}
                ],
                "name": "mintSBT",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]
        self.contract_address = self.web3.to_checksum_address('0x06F9914838903162515aFa67D5b99Ada0F9791cc')
        self.contract = self.web3.eth.contract(address=self.contract_address, abi=abi)

    async def get_nonce(self):
        try:
            json_data = {
                "address": self.account.address,
                "feature": "assets-wallet-login",
                "chainId": 204
            }
            res = await self.http.post('https://toolkit.ultiverse.io/api/user/signature', json=json_data)
            if 'success' in res.text and res.json()['success']:
                message = res.json()['data']['message']
                signature = self.account.sign_message(encode_defunct(text=message))
                return signature.signature.hex()
            logger.error(f'[{self.account.address}] 获取nonce失败：{res.text}')
            return None
        except Exception as e:
            logger.error(f'[{self.account.address}] 获取nonce异常：{e}')
            return None

    async def signin(self):
        try:
            signature = await self.get_nonce()
            if signature is None:
                return False
            json_data = {
                "address": self.account.address,
                "signature": signature,
                "chainId": 204
            }
            res = await self.http.post('https://toolkit.ultiverse.io/api/wallets/signin', json=json_data)
            if 'success' in res.text and res.json()['success']:
                access_token = res.json()['data']['access_token']
                self.http.headers.update({"Ul-Auth-Token": access_token})
                return True
            logger.error(f'[{self.account.address}] 登录失败：{res.text}')
            return False
        except Exception as e:
            logger.error(f'[{self.account.address}] 登录异常：{e}')
            return False

    async def get_info(self):
        try:
            if 'Ul-Auth-Token' not in self.http.headers:
                await self.signin()
            res = await self.http.get('https://pilot.ultiverse.io/api/register/agent-info')
            if 'success' in res.text and res.json()['success']:
                if 'nickname' in res.json()['data'] and res.json()['data']['nickname'] is None or 'nickname' not in res.json()['data']:
                    logger.info(f"[{self.account.address}] 未注册，开始注册")
                    await self.polit()
                elif 'tokenId' in res.json()['data'] and res.json()['data']['tokenId'] is None or 'tokenId' not in res.json()['data']:
                    logger.info(f"[{self.account.address}] 未Mint，开始Mint")
                    return await self.mint()
                else:
                    logger.success(f"[{self.account.address}] 注册Mint成功")
                    return True
            return False
        except Exception as e:
            logger.error(f'[{self.account.address}] 获取信息异常：{e}')
            return False

    async def register(self):
        try:
            json_data = {"referralCode": "1IjSF"}
            res = await self.http.post('https://pilot.ultiverse.io/api/register/sign', json=json_data)
            if 'success' in res.text and res.json()['success']:
                return True
            logger.error(f'[{self.account.address}] 注册失败：{res.text}')
            return False
        except Exception as e:
            logger.error(f'[{self.account.address}] 注册异常：{e}')
            return False

    async def polit(self):
        try:
            if not await self.register():
                return None
            json_data = {"nickname": self.Nickname}
            res = await self.http.post('https://pilot.ultiverse.io/api/register/polit', json=json_data)
            if 'success' in res.text and res.json()['success']:
                return await self.get_info()
            logger.error(f'[{self.account.address}] 设置用户名失败：{res.text}')
            return None
        except Exception as e:
            logger.error(f'[{self.account.address}] 设置用户名异常：{e}')
            return None

    async def get_mint(self):
        try:
            json_data = {"meta": ["Introverted", "Confident", "Social Butterfly", "Open-minded", "Skeptical"]}
            res = await self.http.post('https://pilot.ultiverse.io/api/register/mint', json=json_data)
            if 'success' in res.text and res.json()['success']:
                deadline = res.json()['data']['deadline']
                attributeHash = res.json()['data']['attributeHash']
                signature = res.json()['data']['signature']
                return self.contract.functions.mintSBT(int(deadline), attributeHash, signature)
            logger.error(f'[{self.account.address}] 获取Mint信息失败：{res.text}')
            return None
        except Exception as e:
            logger.error(f'[{self.account.address}] 获取Mint信息异常：{e}')
            return None

    async def mint(self):
        try:
            mintSBT = await self.get_mint()
            if mintSBT is None:
                return False
            nonce = await self.web3.eth.get_transaction_count(self.account.address)
            tx = await mintSBT.build_transaction({
                'from': self.account.address,
                'chainId': 204,
                'gas': 2000000,
                'nonce': nonce,
                'maxFeePerGas': 18,
                'maxPriorityFeePerGas': 2,
            })
            signed = self.account.sign_transaction(tx)
            tx_hash = await self.web3.eth.send_raw_transaction(signed.rawTransaction)
            receipt = await self.web3.eth.wait_for_transaction_receipt(tx_hash)
            if receipt.status == 1:
                logger.success(f"[{self.account.address}] Mint交易 {tx_hash.hex()} 成功")
                await asyncio.sleep(10)
                return True
            else:
                logger.error(f"[{self.account.address}] Mint交易 {tx_hash.hex()} 失败")
            return False
        except Exception as e:
            logger.error(f"[{self.account.address}] Mint交易异常：{e}")
            return False


class mission:
    def __init__(self, address, ck, tw_token, dc_token, nocaptcha_token):
        self.address, self.tw_token, self.dc_token = address, tw_token, dc_token
        self.nocaptcha_token = nocaptcha_token
        headers = {
            "Ul-Auth-Api-Key": "bWlzc2lvbl9ydW5uZXJAZFd4MGFYWmxjbk5s",
            "Referer": "https://mission.ultiverse.io/",
            "Origin": "https://mission.ultiverse.io",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        self.http = AsyncSession(timeout=120, headers=headers, impersonate="chrome120")
        self.http.cookies.set('Ultiverse_Authorization', ck)
        self.DC = Discord(self.address, self.dc_token, self.nocaptcha_token)
        self.code_challenge = None

    async def get_info(self):
        try:
            res = await self.http.get('https://toolkit.ultiverse.io/api/user/info')
            if 'success' in res.text and res.json()['success']:
                if res.json()['data']['twitterId'] is None:
                    if not await self.bind_twitter():
                        return False
                if res.json()['data']['discordId'] is None:
                    if not await self.bind_discord():
                        return False
                return True
            logger.error(f'[{self.address}] 获取信息失败：{res.text}')
            return False
        except Exception as e:
            logger.error(f'[{self.address}] 获取信息异常：{e}')
            return False

    async def get_authUrl(self):
        try:
            res = await self.http.get('https://mission.ultiverse.io/api/twitter/login?redirect_uri=https://mission.ultiverse.io&state=eyJ0eXBlIjoidHdpdHRlciIsInRhc2tJZCI6NTI1LCJoYXNoIjoiTVVJdFZUSkVUWHd4TnpBMk1UWTRNRFE0TlRNMiJ9')
            if 'authUrl' in res.text:
                authUrl = res.json()['authUrl']
                self.code_challenge = authUrl.split('code_challenge=')[1].split('&')[0]
                return True
            logger.error(f'[{self.address}] 获取authUrl失败：{res.text}')
            return False
        except Exception as e:
            logger.error(f'[{self.address}] 获取authUrl异常：{e}')
            return False

    async def connect_twitter(self, code):
        try:
            params = {
                'code': code,
                'redirect_uri': 'https://mission.ultiverse.io',
                'codeChallenge': self.code_challenge
            }
            res = await self.http.get('https://mission.ultiverse.io/api/twitter/connect', params=params)
            if 'profile_image_url' in res.text:
                return True
            logger.error(f'[{self.address}] 连接twitter失败：{res.text}')
            return False
        except Exception as e:
            logger.error(f'[{self.address}] 连接twitter异常：{e}')
            return False

    async def bind_twitter(self):
        try:
            if not await self.get_authUrl():
                return False
            twitter = Twitter(self.tw_token, self.code_challenge)
            if not await twitter.twitter_authorize():
                return False
            if not await self.connect_twitter(twitter.auth_code):
                return False
            logger.success(f'[{self.address}] 绑定twitter成功')
            return True
        except Exception as e:
            logger.error(f'[{self.address}] 绑定twitter异常：{e}')
            return False

    async def get_task(self, task_hash):
        try:
            res = await self.http.get(f'https://mission.ultiverse.io/api/task/task?hash={task_hash}')
            if 'success' in res.text and res.json()['success']:
                if res.json()['data']['completed']:
                    logger.success(f'[{self.address}] 任务已完成')
                    return None
                for task in res.json()['data']['actions']:
                    if task['tag'][0]['type'] == 'twitter':
                        if task['isFinished']:
                            logger.success(f'[{self.address}] {task["name"]} 已完成')
                            continue
                        await self.twitter_check(task['name'], task['taskId'], task['id'], task['type'], task['data'])
                    if task['tag'][0]['type'] == 'discord':
                        if task['isFinished']:
                            logger.success(f'[{self.address}] {task["name"]} 已完成')
                            continue
                        if not await self.discord_check():
                            return False
                return await self.claim(task_hash)
            logger.error(f'[{self.address}] 获取任务失败：{res.text}')
            return False
        except Exception as e:
            logger.error(f'[{self.address}] 获取任务异常：{e}')
            return False

    async def claim(self, task_hash):
        try:
            json_data = {"taskId": 525, "hash": task_hash}
            res = await self.http.post('https://mission.ultiverse.io/api/task/claim', json=json_data)
            if 'success' in res.text and res.json()['success']:
                logger.success(f'[{self.address}] 任务claim成功')
                return True
            logger.error(f'[{self.address}] 任务claim失败：{res.text}')
            return False
        except Exception as e:
            logger.error(f'[{self.address}] 任务claim异常：{e}')
            return False

    async def twitter_check(self, task_name, task_taskId, task_id, task_type, task_data):
        try:
            json_data = {"type": task_type, "taskId": task_taskId, "actionId": task_id}
            json_data.update(json.loads(task_data))
            res = await self.http.post('https://mission.ultiverse.io/api/twitter/check', json=json_data)
            if 'success' in res.text and res.json()['success']:
                sleep = 70
                if task_id == 1208 or task_id == 1207:
                    sleep = 10
                logger.success(f'[{self.address}] {task_name} 成功，等待{sleep}s后继续下一个任务')
                await asyncio.sleep(sleep)
                return True
            logger.error(f'[{self.address}] {task_name} 失败：{res.text}')
            return False
        except Exception as e:
            logger.error(f'[{self.address}] {task_name} 异常：{e}')
            return False

    async def discord_check(self):
        await asyncio.sleep(10)
        try:
            json_data = {"type": 20, "taskId": 525, "actionId": 1205, "redirect_uri": "https://mission.ultiverse.io", "channel": "947538592018878484"}
            res = await self.http.post('https://mission.ultiverse.io/api/dc/check', json=json_data)
            if 'success' in res.text and res.json()['success']:
                logger.success(f'[{self.address}] DC进群 成功, 等待10s后继续下一个任务')
                await asyncio.sleep(10)
                return True
            logger.error(f'[{self.address}] DC进群 失败：{res.text}')
            return False
        except Exception as e:
            logger.error(f'[{self.address}] DC进群 异常：{e}')
            return False

    async def connect_discord(self, code):
        try:
            params = {
                'code': code,
                'redirect_uri': 'https://mission.ultiverse.io',
                'channel': 947538592018878484
            }
            res = await self.http.get('https://mission.ultiverse.io/api/dc/connect', params=params)
            if 'global_name' in res.text:
                return True
            logger.error(f'[{self.address}] 连接discord失败：{res.text}')
            return False
        except Exception as e:
            logger.error(f'[{self.address}] 连接discord异常：{e}')
            return False

    async def bind_discord(self):
        try:
            if not await self.DC.joiner():
                return False
            code = await self.DC.authorize()
            if code is None:
                return False
            if not await self.connect_discord(code):
                return False
            if not await self.discord_check():
                return False
            logger.success(f'[{self.address}] 绑定discord成功')
            return True
        except Exception as e:
            logger.error(f'[{self.address}] 绑定discord异常：{e}')
            return False


async def main():
    twitter_account = "Aeroscythe85094----huq8dbBdfcwjAxFPiahA----agyigltx@fmailler.com----auilhruhY4844!----e91dafd9ae3ba909cd52392557c5aad5e5641096----1762336337917538304-v6PFKjaFfJe5YKV0choMCS6O5KTYTt----E3q81qfSwPvomT1zHdMB73HhLco2VHRh5ep7UlSCFfSuV"
    # hdd.cm购买的twitter账号

    twitter_account_list = twitter_account.split("----")
    auth_token = next((tw for tw in twitter_account_list if len(tw) == 40 and set(tw).issubset('0123456789abcdef')), "")
    Nickname = twitter_account_list[0]
    DY = Ultiverse('私钥', Nickname)
    # 私钥
    for _ in range(5):
        if await DY.get_info():
            MS = mission(DY.account.address, DY.http.headers.get('Ul-Auth-Token'), auth_token, "Discord_token", "nocaptcha_token")
            # Discord_token 为Discord的token
            # nocaptcha_token 为nocaptcha的token，注册地址：https://www.nocaptcha.io/register?c=dwBf1P
            if await MS.get_info() and await MS.get_task('MUItVTJETXwxNzA2MTY4MDQ4NTM2') and await MS.get_task('MUItVTJETXwxNzA2MTY4NjY5NDYx'):
                logger.success(f'[{DY.account.address}] 任务完成')
                return True


asyncio.run(main())
