# Import libraries
import os
import dotenv
from IPython.display import Image
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage, SystemMessage
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
# Create the tools
def triangle_area(base: int, height: int) -> float:
    """
    Calculates the area of a triangle, given the base and the height.

    Args:
        base: the lenght of the base of the triangle.
        height: the height of the triangle.
    """

    return (base*height)/2

def circle_area(radius: float) -> float:
    """
    Calculates the area of a circle, given its radius.
    
    Args:
        radius: the radius of the circle.
    """
    pi = 3,14
    # TO DO: investigate why multiplying by PI causes TypeError during tool calling.
    return radius*radius*pi

def square_area(side: float) -> float:
    """
    Calcutes the area of a square.

    Args:
        side: the lenght of the side of the square.
    """

    return side*side


# Define the Agent node
class SimpleReActAgent:

    def __init__(self, llm):
        """Initialize the Agent with the LLM"""
        self.llm_with_tools = llm
        self.system_message = SystemMessage(content="You are a helpful assistent tasked with performing geometric area calculations on a set of inputs")
    
    def __call__(self, state: MessageState, config):
        """
        Call method to invoke.
        """

        result = self.llm_with_tools.invoke(input=[self.system_message]+state["messages"])
        return {"messages": result}
    

# 3. Define the Edges. We will use the tools_condition prebuilt conditional edge

# 4. Define the graph
def create_graph():
    # Instantiate the graph, initializing with the graph state
    graph = StateGraph(MessageState)
    # Add the nodes
    # Create the model and bind the tools
    llm_with_tools = ChatOpenAI(model="gpt-3.5-turbo").bind_tools([triangle_area, circle_area, square_area])
    graph.add_node("Chat Node", SimpleReActAgent(llm=llm_with_tools))
    graph.add_node("tools", ToolNode(tools=[triangle_area, circle_area, square_area]))
    # Add the edges
    graph.add_edge(START, "Chat Node")
    graph.add_conditional_edges(
        source="Chat Node",
        path = tools_condition
    )
    graph.add_edge("tools", "Chat Node")
    # Compile the graph, turning it into a LangChain Runnable
    graph = graph.compile()

    return graph

if __name__ == "__main__":
    
    graph = create_graph()

    # #save graph schema
    with open("figures/simple_react_agent.png", "wb") as f:
        f.write(graph.get_graph().draw_mermaid_png())

    # With this message, the model will produce a response with imortant content in "content".
    initial_message = {"messages": HumanMessage(content="Olá, tudo bem?", name="Marianna")}
    # With this message, the model will produce a response with important content in "additional_kwargs" > "tool_calls"
    initial_message = {"messages": HumanMessage(content="Qual é a área de um triângulo de base = 4cm e altura igual a 10 cm?", name="Marianna")}
    # With this message, the model will produce a response with important content in "additional_kwargs" > "tool_calls" and will loop over tools for some time.
    initial_message = {"messages": HumanMessage(content="Calcule a área de um triângulo de base 4 cm e altura 5 cm."
                                                " Use o resultado para calcular a área de um círculo com raio igual a 1/5 da área do triângulo."
                                                " Use o resultado da área do círculo para calcular a área de um quadrado cujo lado é igual à área do círculo.", name="Marianna")}

    # for chunk in graph.stream(initial_message):
    #     print(chunk)
    response = graph.invoke(initial_message)
    print(response)

    for msg in response["messages"]:
        msg.pretty_print()