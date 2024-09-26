import dotenv
import asyncio
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver


# Set up env variables
print("Is env variables loaded?", dotenv.load_dotenv(".env"))

# 1. Define the state. We will use the prebuilt MessagesState

# 2. Define the nodes
chat_model = ChatOpenAI(model="gpt-3.5-turbo")

def chat_node(state: MessagesState):
    messages = state["messages"]
    return {"messages": chat_model.invoke(input=messages)}

# 3. Define the conditional edges. In this example, will be no conditional edge.

# 4. Create the graph
def create_graph():
    graph = StateGraph(MessagesState)

    graph.add_node("chat node", chat_node)

    graph.add_edge(START, "chat node")
    graph.add_edge("chat node", END)

    memory = MemorySaver()
    graph = graph.compile(checkpointer=memory)

    return graph


def test_stream_by_update_and_value(graph, config, initial_messages):

    print("\n========= INITIAL MESSAGES ==============")
    response = graph.invoke(input=initial_messages, config=config)
    for msg in response["messages"]:
        msg.pretty_print()

    print("\n========= Streaming by Update ==============")
    messages = initial_messages["messages"] + [HumanMessage(content="Quantos deles falam português?", name="Marianna")]

    for chunk in graph.stream(input={"messages":messages}, config=config, stream_mode="updates"):
        print(chunk)
        print("---"*10, "Formated", "---"*10)
        # We can use pretty_print here because there is only one message.
        # Besides that, as we receive just the updates, the response also tells us which node produced the message.
        chunk["chat node"]["messages"].pretty_print()
    
    print("\n========= Streaming by Values ==============")
    messages = messages + [HumanMessage(content="Todos seguem o mesmo acordo ortográfico?", name="Marianna")]

    for chunk in graph.stream(input={"messages": messages}, config=config, stream_mode="values"):
        print(chunk)
        print("---"*10, "Formated", "---"*10)
        for msg in chunk["messages"]:
            msg.pretty_print()

# Solution for using async outside jupyter notebook: 
# https://community.deeplearning.ai/t/lesson4-persistence-and-streaming-last-part-gives-error-syntaxerror-async-for-outside-async-function/647018/4
async def stream_tokens(graph, config, messages):
    async for event in graph.astream_events(input={"messages": messages}, config=config, version="v2"):
        print(f"Node: {event['metadata'].get('langgraph_node', '')}. Type: {event['event']}. Name: {event['name']}")

async def stream_tokens_from_specific_flow(graph, config, messages):
    type_event = "on_chain_stream"
    node = "chat node"

    async for event in graph.astream_events(input={"messages": messages}, config=config, version="v2"):
        if event["event"] == type_event and event["metadata"].get("langgraph_node","") == node:
            data = event["data"]
            print(data)
            # print(data["chunk"]["messages"].content, end="|")

if __name__ == "__main__":

    initial_messages = {"messages":[
        HumanMessage(content="Ola", name="Marianna"),
        AIMessage(content="Olá, como posso te ajudar hoje?", name="Model"),
        HumanMessage(content="Gostaria de saber quantos paises existem no planeta terra", name="Marianna")
    ]}

    graph = create_graph()
    config = {"configurable": {"thread_id":"1"}}
    
    # test_stream_by_update_and_value(graph=graph, config=config, initial_messages=initial_messages)

    print("\n========= INITIAL MESSAGES ==============")
    response = graph.invoke(input=initial_messages, config=config)
    for msg in response["messages"]:
        msg.pretty_print()

    print("\n============= Streaming of Tokens ================")
    messages = initial_messages["messages"] + [HumanMessage(content="Quais deles falam português?", name="Marianna")]

    asyncio.run(stream_tokens(graph=graph, config=config, messages=messages))
    print("\n------------  Specific Node and Event type --------------")
    asyncio.run(stream_tokens_from_specific_flow(graph=graph, config=config, messages=messages))