"""限流器（slowapi）

独立模块持有单例 Limiter，供 main.py 挂到 app.state 与各路由用装饰器引用，
避免 main ↔ 路由之间的循环导入。
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
