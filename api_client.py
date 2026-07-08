import asyncio
import time
import logging
from typing import Dict, Any, Optional, List
import aiohttp
from config import config

logger = logging.getLogger(__name__)

class APIClient:
    def __init__(self):
        self.base_url = config.API_BASE_URL
        self.token = config.LOLZTEAM_TOKEN
        self.session: Optional[aiohttp.ClientSession] = None
        self.timeout = aiohttp.ClientTimeout(total=config.REQUEST_TIMEOUT)
        self._last_request_time: Dict[str, float] = {}
        self._request_count = 0

    _RATE_LIMITS = {
        method: 60 / per_min
        for method, per_min in config.RATE_LIMITS_PER_MIN.items()
    }

    async def _ensure_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    'Authorization': f'Bearer {self.token}',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                timeout=self.timeout
            )

    async def _wait_for_rate_limit(self, method: str):
        interval = self._RATE_LIMITS.get(method.upper(), 0.5)
        key = method.upper()
        now = time.time()
        last = self._last_request_time.get(key, 0)
        elapsed = now - last
        if elapsed < interval:
            await asyncio.sleep(interval - elapsed)
        self._last_request_time[key] = time.time()

    async def _request(self, method: str, endpoint: str,
                       data: Optional[Dict] = None,
                       params: Optional[Dict] = None,
                       retry_count: int = 0) -> Dict[str, Any]:
        await self._ensure_session()
        await self._wait_for_rate_limit(method)

        url = f"{self.base_url}{endpoint}"
        logger.info(f"{method} {url}")

        try:
            async with self.session.request(
                method=method, url=url,
                json=data if data else None,
                params=params
            ) as response:
                self._request_count += 1
                logger.info(f"Status: {response.status} for {endpoint}")

                if response.status == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limit. Waiting {retry_after}s")
                    await asyncio.sleep(retry_after)
                    if retry_count < 3:
                        return await self._request(method, endpoint, data, params, retry_count + 1)
                    raise Exception("Rate limit exceeded after 3 retries")

                if response.status == 401:
                    raise Exception("Ошибка авторизации. Проверьте LOLZTEAM_TOKEN")

                if response.status >= 400:
                    error_text = await response.text()
                    logger.error(f"API {response.status} {endpoint}: {error_text}")
                    import json as _json
                    try:
                        err_json = _json.loads(error_text)
                        errors = err_json.get('errors', [])
                        if errors == ['retry_request'] or errors == 'retry_request':
                            return err_json
                        if errors:
                            raise Exception('\n'.join(errors))
                    except (_json.JSONDecodeError, AttributeError):
                        pass
                    raise Exception(f"Ошибка {response.status}: {error_text[:300]}")

                return await response.json()

        except aiohttp.ClientError as e:
            logger.error(f"Network error: {e}")
            raise Exception(f"Ошибка сети: {e}")
        except Exception:
            raise


    async def get_categories(self) -> Dict:
        return await self._request('GET', '/category')


    async def get_user_info(self) -> Dict:
        return await self._request('GET', '/me')

    async def get_user_items(self, params: Optional[Dict] = None) -> Dict:
        return await self._request('GET', '/user/items', params=params)

    async def get_all_user_items(self, show: str = 'active',
                                 extra_params: Optional[Dict] = None,
                                 max_pages: int = 100) -> List[Dict]:
        all_items: List[Dict] = []
        seen_ids = set()
        page = 1
        while page <= max_pages:
            params = {'show': show, 'page': page}
            if extra_params:
                params.update(extra_params)
            response = await self.get_user_items(params)
            items = response.get('items', [])
            if not items:
                break

            new_on_page = 0
            for item in items:
                item_id = item.get('item_id')
                if item_id is not None and item_id in seen_ids:
                    continue
                if item_id is not None:
                    seen_ids.add(item_id)
                all_items.append(item)
                new_on_page += 1

            total = response.get('totalItems')
            if total is not None and len(all_items) >= int(total):
                break
            if new_on_page == 0:
                break
            page += 1

        return all_items


    async def add_item(self, data: Dict) -> Dict:
        return await self._request('POST', '/item/add', data=data)

    async def goods_check(self, item_id: int, data: Dict, max_retries: int = 100) -> Dict:
        await self._ensure_session()
        import json as _json

        safe = {k: v if k not in ('password', 'email_login_data') else '***' for k, v in data.items()}
        logger.info(f"goods/check REQUEST: {_json.dumps(safe, ensure_ascii=False)}")

        for attempt in range(1, max_retries + 1):
            await self._wait_for_rate_limit('POST')
            url = f"{self.base_url}/{item_id}/goods/check"
            try:
                async with self.session.request('POST', url, json=data) as response:
                    text = await response.text()
                    logger.info(f"goods/check attempt {attempt} status={response.status} body={text[:300]}")
                    try:
                        body = _json.loads(text)
                    except _json.JSONDecodeError:
                        raise Exception(f"Ошибка {response.status}: {text[:300]}")

                    errors = body.get('errors', [])
                    if isinstance(errors, str):
                        errors = [errors]

                    if 'retry_request' in errors:
                        logger.info(f"goods/check retry_request attempt {attempt}/{max_retries}")
                        await asyncio.sleep(1)
                        continue

                    if errors:
                        raise Exception('\n'.join(errors))

                    return body
            except aiohttp.ClientError as e:
                raise Exception(f"Ошибка сети: {e}")

        raise Exception("goods/check: превышено число попыток (retry_request x100)")


    async def get_item(self, item_id: int) -> Dict:
        return await self._request('GET', f'/{item_id}')

    async def edit_item(self, item_id: int, data: Dict) -> Dict:
        return await self._request('PUT', f'/{item_id}/edit', data=data)

    async def delete_item(self, item_id: int) -> Dict:
        return await self._request('DELETE', f'/{item_id}')

    async def open_item(self, item_id: int) -> Dict:
        return await self._request('POST', f'/{item_id}/open')

    async def close_item(self, item_id: int) -> Dict:
        return await self._request('POST', f'/{item_id}/close')


    async def fast_buy(self, item_id: int, price: float) -> Dict:
        return await self._request('POST', f'/{item_id}/fast-buy', data={'price': price})


    async def batch_request(self, requests: List[Dict]) -> Dict:
        return await self._request('POST', '/batch', data={'requests': requests})

    async def get_category_params(self, category_name: str) -> Dict:
        return await self._request('GET', f'/{category_name}/params')

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

api_client = APIClient()
