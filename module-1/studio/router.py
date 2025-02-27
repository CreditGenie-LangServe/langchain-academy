import os

from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition


# Tool
def multiply(a: int, b: int) -> int:
    """Multiplies a and b.

    Args:
        a: first int
        b: second int
    """
    return a * b


# LLM with bound tool
llm = (
    ChatOllama(
        model="llama3.1:8b",
        base_url=os.environ["SPARE_PARTS_OLLAMA_API_URL"],
        client_kwargs={
            "headers": {
                "Authorization": f"Bearer {os.environ['SPARE_PARTS_OLLAMA_API_KEY']}"
            }
        },
    )
    if os.environ["USE_SPARE_PARTS"]
    else ChatOpenAI(model="gpt-4o")
)
llm
llm_with_tools = llm.bind_tools([multiply])


# Node
def tool_calling_llm(state: MessagesState):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}


# Build graph
builder = StateGraph(MessagesState)
builder.add_node("tool_calling_llm", tool_calling_llm)
builder.add_node("tools", ToolNode([multiply]))
builder.add_edge(START, "tool_calling_llm")
builder.add_conditional_edges(
    "tool_calling_llm",
    # If the latest message (result) from assistant is a tool call -> tools_condition routes to tools
    # If the latest message (result) from assistant is a not a tool call -> tools_condition routes to END
    tools_condition,
)
builder.add_edge("tools", END)

# Compile graph
graph = builder.compile()
