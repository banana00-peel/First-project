"""图片服务（Unsplash，可选）"""
from typing import List, Optional

import httpx
from loguru import logger

from app.config import get_settings

UNSPLASH_BASE = "https://api.unsplash.com"


class ImageService:
    """Unsplash 图片服务封装；未配置 key 时返回空列表"""

    def __init__(self, access_key: Optional[str] = None):
        self.access_key = access_key or get_settings().unsplash_access_key
        self._client = httpx.Client(timeout=15.0)

    def search_images(self, query: str, per_page: int = 3) -> List[str]:
        """搜索图片，返回 URL 列表"""
        if not self.access_key:
            return []

        try:
            resp = self._client.get(
                f"{UNSPLASH_BASE}/search/photos",
                params={"query": query, "per_page": per_page, "client_id": self.access_key},
            )
            resp.raise_for_status()
            results = resp.json().get("results", [])
            return [r.get("urls", {}).get("regular", "") for r in results if r.get("urls")]
        except Exception as e:
            logger.warning("Unsplash 请求失败: {}", e)
            return []

    def close(self):
        self._client.close()


_client: Optional[ImageService] = None


def get_image_service() -> ImageService:
    global _client
    if _client is None:
        _client = ImageService()
    return _client
