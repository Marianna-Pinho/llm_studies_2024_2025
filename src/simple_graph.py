# Import libraries
import os
import dotenv
import random
from IPython.display import Image
from typing import Literal, TypedDict
from langgraph.graph import StateGraph, START, END
import matplotlib.pyplot as plt

# Set up env variables
print("Is env variables loaded?", dotenv.load_dotenv(".env"))

# 1. Define the graph state (Class)
class State(TypedDict):
    name: str
    message: str

# 2. Define the nodes (Function)
def initial_node(state):
    print("---- Initial Node ----")
    return {"message": "Ola " + state["name"] + ", tudo bem?"}

def motivation_node(state):
    print("--- Motivational Node ---- ")
    return {"name": state["name"]+" Motivated", "message": "You can take it, you can make it"}

def name_change_node(state):
    print("--- Name Changing Node ----")
    return {"name": "mister bluesky"}

# 3. Define the edges (Function)
def route_edge(state) -> Literal["Motivational Node", "Name Changing Node"]:
    actual_state = state

    if random.random() < 0.7:
        return "Motivational Node"
    else:
        return "Name Changing Node"

# 4. Define the graph
def create_graph():
    # Initialize graph with the State
    graph = StateGraph(State)
    
    # Add nodes
    graph.add_node("Initial Node", initial_node)
    graph.add_node("Motivational Node", motivation_node)
    graph.add_node("Name Changing Node", name_change_node)

    # Add edges
    graph.add_edge(START, "Initial Node")
    graph.add_edge("Motivational Node", END)
    graph.add_edge("Name Changing Node", END)
    graph.add_conditional_edges("Initial Node", route_edge)

    #Compile the graph
    graph = graph.compile()

    return graph

if __name__ == "__main__":
    initial_state = {"name": "Marianna"}
    graph = create_graph()

    #save graph schema
    with open("figures/simple_graph.png", "wb") as f:
        f.write(graph.get_graph().draw_mermaid_png())

    # Experiment it
    print("======= Invoke ======== ")
    print(graph.invoke(initial_state))

    print("====== Stream ========")
    for chunk in graph.stream(initial_state):
        print("--->",chunk)