import dotenv
import asyncio

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import START, END, StateGraph, MessagesState
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode, tools_condition
from langchain.tools import tool


# Set up env variables
print("Is env variables loaded?", dotenv.load_dotenv(".env"))

class Chatbot:
    def __init__(self, checkpointer=None):
        self.llm = ChatOpenAI(model="gpt-3.5-turbo", streaming=True)
        self.tools = [self.sum_numbers, self.multiply_numbers]
        self.llm = self.llm.bind_tools(self.tools)
        self.workflow = self.create_graph(checkpointer=checkpointer)
    
    @staticmethod
    @tool
    def sum_numbers(a:int, b:int):
        '''Sum two numbers'''
        return a+b
    
    @staticmethod
    @tool
    def multiply_numbers(a:int, b:int):
        '''Multiply two numbers'''
        return a*b
    
    def assistant(self, state: MessagesState):
        response = self.llm.invoke(state['messages'])
        return {'messages': response}
    
    def create_graph(self, checkpointer):
        graph = StateGraph(MessagesState)
        graph.add_node("assistant", self.assistant)
        graph.add_node("tools", ToolNode(self.tools))

        graph.add_edge(START, "assistant")
        graph.add_conditional_edges(
            "assistant",
            tools_condition
        )
        graph.add_edge("tools", "assistant")

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

    ## Creates the graph and set up configs and inital message
    workflow = Chatbot(checkpointer=MemorySaver()).workflow
    initial_message = {"messages": [HumanMessage(content="Quanto é 2 mais 3?", name="Marianna")]}
    config = {"configurable": {"thread_id":"1"}}
   
    print("=========== Complete Normal Execution ==============")
    for event in workflow.stream(input=initial_message, config=config, stream_mode="values"):
        event['messages'][-1].pretty_print()

    print("###"*50)
    print("\n============ Getting Graph Checkpoints History ==============")
    history = [state for state in workflow.get_state_history(config)]
    print("History length:", len(history), "\nHistory sample at t[0]:", history[-1])
    print("---"*50,"\nHistory at t[now]:", history[0])

    print("###"*50)
    print("\n=============== Replaying from a Specific Checkpoint ================")
    # In replay, the nodes are not reexecuted. This happens because the graph knows that the checkpoint has already been executed before.
    
    checkpoint_to_replay_from = history[-3]
    print("Checkpoint to replay from:", checkpoint_to_replay_from.values['messages'])
    print("---"*50)

    # In order to replay, we need the thread_id and checkpoint_id, which are both in the checkpoint_to_replay_from.config.
    # This is faster because the graph doesn't need to execure anything, just get the previous executed states.
    for event in workflow.stream(input=None, config=checkpoint_to_replay_from.config, stream_mode="values"):
        event['messages'][-1].pretty_print()

    print("###"*50)
    print("\n=============== Forking from a Specific Checkpoint ================")
    ## In forking, we are also starting from a previous executed state, but this time we update the state with a different input.
    ## This makes the graph be reexecuted from there.

    checkpoint_to_fork_from = history[-2]
    print("Checkpoint to fork from:", checkpoint_to_fork_from.values["messages"])
    print("---"*50)

    ## Update the state in order to fork. Also, uses the id of the message in the actual state to overwrite it and not just append the update
    fork_config = workflow.update_state(
        checkpoint_to_fork_from.config,
        {"messages": [HumanMessage(content="Quanto é 5 + 5?", id=checkpoint_to_fork_from.values["messages"][0].id)]}
    )

    ## Checking new history
    history = [state for state in workflow.get_state_history(config)]
    print("History length:", len(history), "\nHistory at t[now]:", history[0])

    print("---------------- Executing Fork ------------------------")
    for event in workflow.stream(input=None, config=fork_config, stream_mode="values"):
        event['messages'][-1].pretty_print()
