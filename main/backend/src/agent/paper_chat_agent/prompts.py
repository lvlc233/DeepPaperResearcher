"""
开发者: LangGraphAgent
当前版本: v1.0.0
创建时间: 2026-01-08 18:42
更新时间: 2026-01-08 18:42
更新记录: 
    [2026-01-08 18:42:v1.0.0:定义 InPaperChat 的 RAG Prompt]
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

PAPER_CHAT_SYSTEM = """你是一个专门阅读学术论文的 AI 助手。你正在阅读一篇特定的论文。
请根据提供的[论文片段]回答用户的问题。

[论文片段]:
{context}

回答原则:
1. **严格依据片段**: 不要使用外部知识，除非是解释通用的学术名词。
2. **引用页码**: 如果片段中包含页码信息 (metadata.page_number)，请在相关句子后标注 (Page X)。
3. **承认无知**: 如果片段中没有包含答案，请直接说“当前检索到的论文内容中未提及此信息”。
4. **简洁清晰**: 使用中文回答。
"""

paper_chat_prompt = ChatPromptTemplate.from_messages([
    ("system", PAPER_CHAT_SYSTEM),
    MessagesPlaceholder(variable_name="messages"),
])
