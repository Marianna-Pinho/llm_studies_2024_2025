# Import libraries
import os
import dotenv
from IPython.display import Image
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

# Set up env variables
print("Is env variables loaded?", dotenv.load_dotenv(".env"))


# 1. Define the State
class MessageState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


# 2. Define the nodes
# A) Create tools
def triangle_area(base: int, height: int) -> float:
    """
    Calculates the area of a triangle, given the base and the height.

    Args:
        base: the lenght of the base of the triangle.
        height: the height of the triangle.
    """

    return (base*height)/2

def multiply(a: float, b: float) -> float:
    """
    Multiply two numbers.

    Args:
        a: first number.
        b: second number.
    """

    return a*b

# B) Instantiates the LLM with tools
llm_with_tools = ChatOpenAI(model="gpt-3.5-turbo").bind_tools([triangle_area, multiply])

# C) Define the nodes
def chat_node(state: MessageState):
    system_message = SystemMessage(content="You are a helpful assistant expert in arithmetic and geometric mathematical operations.")

    return {"messages": [llm_with_tools.invoke(input = [system_message] + state["messages"])]}

# 3. Define the conditional edges. In this case, we are going to use the builting tools_conditional

# 4. Create the graph

def create_graph(memory_checkpointer):

    # Instantiates the graph with the defined Graph State
    graph = StateGraph(MessageState)

    # Define the nodes
    graph.add_node("Chat Node", chat_node)
    graph.add_node("tools", ToolNode(tools=[triangle_area, multiply]))

    # Define the edges
    graph.add_edge(START, "Chat Node")
    graph.add_conditional_edges(source="Chat Node", path=tools_condition)
    graph.add_edge("tools", "Chat Node")

    # Compile the graph, turning it into a LangChain Runnable. Also, add a checkpointer to store graph states (memory)
    graph = graph.compile(checkpointer=memory_checkpointer)
    # graph = graph.compile()
    
    return graph


if __name__ == "__main__":
    memory_checkpointer = MemorySaver()
    graph = create_graph(memory_checkpointer=memory_checkpointer)
    config = {"configurable": {"thread_id": "3"}}

    # #save graph schema
    # with open("figures/simple_graph_with_memory.png", "wb") as f:
    #     f.write(graph.get_graph().draw_mermaid_png())

    # With this message, the model will produce a response with imortant content in "content".
    # initial_message = {"messages": HumanMessage(content="Olá, tudo bem?", name="Marianna")}
    # With this message, the model will produce a response with important content in "additional_kwargs" > "tool_calls"
    initial_message = {"messages": [HumanMessage(content="Qual é a área de um triângulo de base = 4cm e altura igual a 10 cm?", name="Marianna")]}

    response = graph.invoke(input=initial_message, config=config)

    print("===== Previews Messages ========")
    for msg in response["messages"]:
        msg.pretty_print()


    print("===== Follow up Messages with the same Thread Id ========")
    next_message = {"messages": HumanMessage(content="Multiplique o resultado anterior por 2.", name="Marianna")}
    response = graph.invoke(input=next_message, config=config)

    for msg in response["messages"]:
        msg.pretty_print()


    print("===== Follow up Messages with different Thread Id ========")
    next_message = {"messages": HumanMessage(content="Qual foi o resultado da operação anterior?.", name="Marianna")}
    new_config = {"configurable": {"thread_id": "4"}}
    response = graph.invoke(input = next_message, config=new_config)

    for msg in response["messages"]:
        msg.pretty_print()

