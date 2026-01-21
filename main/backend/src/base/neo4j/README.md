---
name: Neo4j数据库说明文档
description: |
    该文档是该项目使用Neo4j数据库的说明文档。
    已初始化基本的连接服务。
author: "BackendAgent"
state: DONE
created: 2026-01-14
path: "/main/src/base/neo4j/"
---

## 使用方法

### 依赖注入

在 FastAPI 路由中:

```python
from fastapi import Depends
from neo4j import AsyncSession
from base.neo4j.service import get_neo4j_session

@router.get("/graph")
async def get_graph(session: AsyncSession = Depends(get_neo4j_session)):
    result = await session.run("MATCH (n) RETURN n LIMIT 5")
    return [record["n"] async for record in result]
```

### 上下文管理器

```python
from base.neo4j.service import Neo4jService

async with Neo4jService.get_session() as session:
    await session.run("CREATE (n:Person {name: 'Andy'})")
```
