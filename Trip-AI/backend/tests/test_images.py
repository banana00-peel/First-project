"""app.services.images 的单元测试"""
from app.services.images import ImageService


def test_search_images_returns_empty_without_key(monkeypatch):
    """未配置 Unsplash key 时，应直接返回空列表，不发起网络请求"""

    class FakeSettings:
        unsplash_access_key = ""

    monkeypatch.setattr("app.services.images.get_settings", lambda: FakeSettings())

    service = ImageService()
    try:
        assert service.search_images("beach") == []
    finally:
        service.close()
