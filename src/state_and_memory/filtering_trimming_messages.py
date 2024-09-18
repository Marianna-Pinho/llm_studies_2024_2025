import dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langgraph.graph import START, END, StateGraph
from langchain_core.messages import AnyMessage, AIMessage, HumanMessage, RemoveMessage, trim_messages

# Set up env variables
print("Is env variables loaded?", dotenv.load_dotenv(".env"))

# 1. Implementing filtering through graph modification, adding a new node
chat_model = ChatOpenAI(model="gpt-3.5-turbo")

# Filtering Node
def filter_messages_node(state: MessagesState):
    # Delete all except the last message
    messages_to_delete = [RemoveMessage(id=msg.id) for msg in state["messages"][:-2]]
    return {"messages": messages_to_delete}

# Chat node for graph modification example
def chat_node_graph_modification(state: MessagesState):
    return {"messages": [chat_model.invoke(input=state["messages"])]}

# Graph for graph modification example
def create_graph_modification_example():
    graph = StateGraph(MessagesState)

    graph.add_node("filter node", filter_messages_node)
    graph.add_node("chat node", chat_node_graph_modification)

    graph.add_edge(START, "filter node")
    graph.add_edge("filter node", "chat node")
    graph.add_edge("chat node", END)

    graph = graph.compile()

    return graph

def test_graph_with_modifications(messages):
    graph_with_modification = create_graph_modification_example()

    # save graph schema
    with open("figures/filtering_modified_graph.png", "wb") as f:
        f.write(graph_with_modification.get_graph().draw_mermaid_png())

    response = graph_with_modification.invoke(input=messages)

    for msg in response["messages"]:
        msg.pretty_print()

##================================================

# 2. Filtering messages without modifying the graph. Just sets the number of messages sent to the chat model

# Define the chat node
def chat_node_with_inplace_filtering(state: MessagesState):
    return {"messages": [chat_model.invoke(input=state["messages"][-1:])]}

# Create the graph
def create_graph_with_inplace_filtering():
    graph = StateGraph(MessagesState)

    graph.add_node("chat node", chat_node_with_inplace_filtering)

    graph.add_edge(START, "chat node")
    graph.add_edge("chat node", END)

    graph = graph.compile()

    return graph

def test_graph_with_inplace_filtering(messages):
    graph = create_graph_with_inplace_filtering()
    response = graph.invoke(input=messages)

    for msg in response["messages"]:
        msg.pretty_print()

##================================================

# 3. Trimming messages

def chat_node_with_trimming(state: MessagesState):
    messages = trim_messages(
        messages = state["messages"],
        max_tokens = 50,
        strategy = "last",
        token_counter = ChatOpenAI(model="gpt-3.5-turbo"),
        allow_partial = True
    )

    return {"messages": [chat_model.invoke(input=messages)]}

def create_graph_trimming():
    graph = StateGraph(MessagesState)

    graph.add_node("chat node trimming", chat_node_with_trimming)

    graph.add_edge(START, "chat node trimming")
    graph.add_edge("chat node trimming", END)

    graph = graph.compile()

    return graph

def test_graph_with_trimming(messages):
    ## Trim
    print(trim_messages(
        messages = messages["messages"],
        max_tokens = 50,
        strategy = "last",
        token_counter = ChatOpenAI(model="gpt-3.5-turbo"),
        allow_partial = True
    ))
    print("---"*10)
    print(trim_messages(
        messages = messages["messages"],
        max_tokens = 50,
        strategy = "first",
        token_counter = ChatOpenAI(model="gpt-3.5-turbo"),
        allow_partial=False
    ))

    ## Graph with trim
    graph = create_graph_trimming()
    response = graph.invoke(input=messages)
    for msg in response["messages"]:
        msg.pretty_print()


if __name__ == "__main__":
    messages = {"messages":[
        AIMessage(content="Olá, como posso te ajudar hoje?", name="Model"),
        HumanMessage(content="Oi, gostaria de saber sobre alimentação de gatos.", name="Marianna"),
        AIMessage(content="O que especificamente você deseja saber sobre alimentação de gatos?", name="Model"),
        HumanMessage(content="Como construir uma dieta saudável para eles.", name="Marianna")
    ]}
    
    ## Filtering examples
    test_graph_with_modifications(messages)
    test_graph_with_inplace_filtering(messages)

    ## Trimming examples
    test_graph_with_trimming(messages)
   