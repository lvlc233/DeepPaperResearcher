---
name: 数据库层说明文档
description: |
    该文档是该项目使用关系数据库层的说明文档。
    该项目的数据库层是基于SQLmodel构建的，使用pg作为数据库。
    当你需要开始使用数据库时，请务必确保你已掌握了该文档中的开发流程。
author: "lxz"
state: TODO
created: 2026-01-01
path: "/main/src/base/pg/"
---

# 介绍

使用SQLmodel进行ORM映射。

# 结构
pg/
├── entity.py # 定义数据库实体模型
|── service.py # 提供pg数据库语句。
