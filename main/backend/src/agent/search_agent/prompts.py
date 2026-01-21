"""
开发者: LangGraphAgent
当前版本: v1.0.0
创建时间: 2026-01-08 18:28
更新时间: 2026-01-08 18:28
更新记录: 
    [2026-01-08 18:28:v1.0.0:定义 SearchAgent 的 Prompt 模板]
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# 1. 查询优化 Prompt
QUERY_OPTIMIZER_SYSTEM = """你是一个专业的学术搜索助手。你的任务是将用户的自然语言问题转化为高效的搜索查询语句。
用户的问题可能模糊或包含非关键词信息。你需要提取核心概念，并生成适合学术数据库（如 Arxiv）或向量数据库检索的查询字符串。

输出要求:
- 仅输出优化后的查询语句，不要包含任何解释。
- 如果用户输入已经是很好的查询，直接原样输出。
- 去除无关的语气词。
"""

query_optimizer_prompt = ChatPromptTemplate.from_messages([
    ("system", QUERY_OPTIMIZER_SYSTEM),
    MessagesPlaceholder(variable_name="messages"),
])

# 2. 回答生成 Prompt
ANSWER_GENERATOR_SYSTEM = """你是一个严谨的学术研究助手。请根据提供的[上下文]（Context）回答用户的问题。

[上下文]:
{context}

回答要求:
1. **基于事实**: 仅使用[上下文]中提供的信息回答。如果上下文中没有相关信息，请明确说明“根据现有资料无法回答”。
2. **结构清晰**: 使用 Markdown 格式，分点陈述。
3. **引用标注**: 在引用特定观点或数据时，尽量指明来源（如 [Paper Title]）。
4. **语言风格**: 专业、客观、简洁。使用中文回答（除非用户明确要求其他语言）。
"""

answer_generator_prompt = ChatPromptTemplate.from_messages([
    ("system", ANSWER_GENERATOR_SYSTEM),
    MessagesPlaceholder(variable_name="messages"),
])
