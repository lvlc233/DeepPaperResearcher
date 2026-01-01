"""
创建时间: 2026-1-1
创建者: lxz
描述: Agent相关的提示词定义:案例
"""
# 使用简单的提示词时: 后缀,PROMPT
XX_PROMPT = """
你是一个专业的研究助手，你的任务是根据用户的问题，进行专业的研究和回答。
"""

# 带有模板时: 后缀,TEMPLATE
XX_TEMPLATE = """
{question}
"""


# 当模板复杂时: 后缀,TEMPLATE
from jinja2 import Template

# 定义模板
XX_TEMPLATE :Template= Template("""
{{question}}
""")


# 如果是工具的描述时: 后缀:DESCRIPTION
XX_DESCRIPTION = """
一个简单的工具，用于返回查询的结果
"""