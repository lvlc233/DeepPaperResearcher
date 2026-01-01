"""
创建时间: 2026-1-1
创建者: lxz
描述: agent编排的案例。
"""
# 引入该agent包下的资源
# 创建编排

from langgraph.graph.state import END, StateGraph
from schema import AgentState
from node import Node,chat

# 建立路由
async def router(state:AgentState):
    "路由"
    if ...:
        return "chat"
    return END


# 初始化Node 
node = Node("chat_node")

# 添加节点
graph = StateGraph()
graph.add_node(node.node_name, node.run)
graph.add_node("chat",chat)
# 创建关系

graph.set_entry_point(node.node_name)
graph.add_conditional_edges(
    node.node_name,
    router,
    {
        "chat": "chat",
        END: END,
    },
)

# 编译agent
agent=graph.compile(AgentState)




