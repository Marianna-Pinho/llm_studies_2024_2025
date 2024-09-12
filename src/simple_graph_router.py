# Import libraries
import os
import dotenv
from IPython.display import Image
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode, tools_condition

# Set up env variables
print("Is env variables loaded?", dotenv.load_dotenv(".env"))

# 1. Define the State
class MessageState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

# An alternative way of defining the state is using a built-in langgraph messages state.
# It has the same behavior as the one we defined above, but it was created because it's a very commonly used state.
class BuiltinMessageState(MessagesState):
    pass

# 2. Define the Nodes.
# TO DO: learn how to pass other arguments to the nodes. For exemplo, the llm model defined in another function.
# Create the tool
def triangle_area(base: int, height: int) -> float:
    """
    Calculates the area of a triangle, given the base and the height.

    Args:
        base: the lenght of the base of the triangle.
        height: the height of the triangle.
    """

    return (base*height)/2

# Create the model and bind the tools
llm_with_tools = ChatOpenAI(model="gpt-3.5-turbo").bind_tools([triangle_area])

# Create the node
def node_llm_with_tools(state: MessagesState):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

# 3. Define the Edges. In this case, there is no conditional edge, so no function need to be implemented.

# 4. Define the graph
def create_graph():
    # Instantiate the graph, initializing with the graph state
    graph = StateGraph(MessagesState)
    # Add the nodes
    graph.add_node("Chat Node", node_llm_with_tools)
    graph.add_node("tools", ToolNode([triangle_area]))
    # Add the nodes
    graph.add_edge(START, "Chat Node")
    graph.add_conditional_edges(source="Chat Node", path=tools_condition)
    graph.add_edge("tools", END)
    # Compile the graph, turning it into a LangChain Runnable
    graph = graph.compile()

    return graph

if __name__ == "__main__":
    
    graph = create_graph()

    # #save graph schema
    with open("figures/simple_graph_router.png", "wb") as f:
        f.write(graph.get_graph().draw_mermaid_png())

    # With this message, the model will produce a response with imortant content in "content".
    initial_message = {"messages": HumanMessage(content="Olá, tudo bem?", name="Marianna")}
    # With this message, the model will produce a response with important content in "additional_kwargs" > "tool_calls"
    initial_message = {"messages": HumanMessage(content="Qual é a área de um triângulo de base = 4cm e altura igual a 10 cm?", name="Marianna")}

    response = graph.invoke(initial_message)
    print(response)

    for msg in response["messages"]:
        msg.pretty_print()