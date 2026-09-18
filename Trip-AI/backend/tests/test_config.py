"""app.config 的单元测试"""
from app.config import Settings


def test_get_cors_origins_list_splits_and_trims():
    """CORS 列表应按逗号拆分并去除两端空白"""
    s = Settings(cors_origins=" a , b ,c ")
    assert s.get_cors_origins_list() == ["a", "b", "c"]


def test_get_cors_origins_list_empty():
    """空字符串应返回空列表"""
    s = Settings(cors_origins="")
    assert s.get_cors_origins_list() == []
