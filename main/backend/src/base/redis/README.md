---
name: Redis缓存层说明文档
description: |
    该文档是该项目使用Redis缓存层的说明文档。
    已初始化基本的连接服务。
author: "BackendAgent"
state: DONE
created: 2026-01-14
path: "/main/src/base/redis/"
---

## 使用方法

### 依赖注入

在 FastAPI 路由中:

```python
from fastapi import Depends
from redis.asyncio import Redis
from base.redis.service import get_redis

@router.get("/cache")
async def get_cache(redis: Redis = Depends(get_redis)):
    await redis.set("key", "value")
    return await redis.get("key")
```

### 直接调用

```python
from base.redis.service import redis_client

await redis_client.set("key", "value")
```
