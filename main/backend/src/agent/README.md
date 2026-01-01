---
name: Agent层说明文档
description: |
    该文档是该项目构建Agent的说明文档。
    该项目的Agent层是基于langgraph构建的，每个Agent都是一个langgraph的图。
    当你需要开始构建一个Agent时，请务必确保你已掌握了该文档中的开发流程。
author: "lxz"
state: TEST
created: 2026-01-01
path: "/main/src/agent/"
---

# 结构
'''
├── agent/
│   ├── common/             # agent领域下可复用的代码 
│   │   └── tools.py
│   ├── example_agent/      # 一个示例Agent，用于演示如何构建一个Agent,命名规则{agent_name}
│   │   ├── __init__.py     # 按需暴露资源,一般只需要暴露agent即可
│   │   ├── agent.py        # 定义图的路由规则 和 节点编排关系
│   │   ├── node.py         # 定义节点的具体实现
│   │   ├── prompts.py      # 定义llm的prompts 和 工具描述
│   │   ├── schema.py       # 定义Agent状态,运行上下文和模型结构化输出内容
│   │   └── tools.py        # 定义节点的工具。
│   └── llm/                # TODO: 进行LLM的基础配置的工厂
'''