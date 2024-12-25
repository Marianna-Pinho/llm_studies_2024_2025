import dotenv
import asyncio

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import START, END, StateGraph, MessagesState
from langgraph.checkpoint.memory import MemorySaver


# Set up env variables
print("Is env variables loaded?", dotenv.load_dotenv(".env"))

class Chatbot:
    def __init__(self, checkpointer=None):
        self.llm = ChatOpenAI(model="gpt-3.5-turbo", streaming=True)
        self.workflow = self.create_graph(checkpointer=checkpointer)
    
    async def assistant(self, state: MessagesState):
        response = await self.llm.ainvoke(state['messages'])
        return {'messages': response}
    
    def create_graph(self, checkpointer):
        graph = StateGraph(MessagesState)
        graph.add_node("assistant", self.assistant)
        graph.add_edge(START, "assistant")
        graph.add_edge("assistant", END)

        return graph.compile(checkpointer=checkpointer)
    

async def run_async(workflow, config, initial_message):
    # async for event in workflow.astream(input=initial_message, stream_mode="messages", config=config):
        # print(event)
    async for event in workflow.astream_events(input=initial_message, config=config, version="v2"):
        # print(f"Node: {event['metadata'].get('langgraph_node','')}. Type: {event['event']}. Name: {event['name']}")
        # print("---")
        if event["event"] == "on_chat_model_stream" and event["metadata"].get('langgraph_node','') == "assistant":
            print(event["data"]['chunk'].content, end = " | ")

if __name__ == "__main__":
    workflow = Chatbot(checkpointer=MemorySaver()).workflow

    initial_message = {"messages": [HumanMessage(content="Me fale sobre o palmeiras.", name="Marianna")]}
    config = {"configurable": {"thread_id":"1"}}

    print("============= Stream by Values ===============")
    for event in workflow.stream(input=initial_message, config=config, stream_mode="values"):
        print("EVENT:", event)
        print("---"*10)
        for msg in event["messages"]:
            msg.pretty_print()
        print("==="*10)
        

    print("============== Stream by Updates ==================")
    for chunk in workflow.stream(input=initial_message, config=config, stream_mode="updates"):
        print("CHUNK:", chunk)
        print("---"*10)
        chunk['assistant']['messages'].pretty_print()

    print("================== Stream by Tokens ================")
    asyncio.run(run_async(workflow=workflow, config=config, initial_message=initial_message))
