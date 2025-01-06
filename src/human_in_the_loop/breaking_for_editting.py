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
    def __init__(self, checkpointer=None, when_interrupt="tools"):
        self.llm = ChatOpenAI(model="gpt-3.5-turbo", streaming=True)
        self.tools = [self.sum_numbers, self.multiply_numbers]
        self.llm = self.llm.bind_tools(self.tools)
        self.when_interrupt = when_interrupt
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

        return graph.compile(checkpointer=checkpointer, interrupt_before=self.when_interrupt)
    

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
    workflow = Chatbot(checkpointer=MemorySaver(), when_interrupt="assistant").workflow
    initial_message = {"messages": [HumanMessage(content="Quanto é 2 mais 3?", name="Marianna")]}
    config = {"configurable": {"thread_id":"1"}}
   
    ## Experiment interrupting the workflow before the assistant node and asking for approval or an edditing.
    ## It continues the workflow if we answer yes or it edits the workflow if we answer no.
    print("=========== Asks for Editting =======")

    for event in workflow.stream(input=initial_message, config=config, stream_mode="values"):
        event['messages'][-1].pretty_print()
        state = workflow.get_state(config).next
    
    print("State:", state)
    
    if  state[0] == "assistant":
        choice = input("Do you want to continue the workflow? [y/n]: ")

        if choice.lower() == "y":
            ## Using input=None, the workflow follows from where it stopped before
            for event in workflow.stream(input=None, config=config, stream_mode="values"):
                event['messages'][-1].pretty_print()

            ## As the workflow always stops before the assistant, we need to call the stream again to the assistant give the final answer
            for event in workflow.stream(input=None, config=config, stream_mode="values"):
                event['messages'][-1].pretty_print()
        
        else:
            ## Changes the message to be given to the assistant
            new_message = {"messages": [HumanMessage(content="Não, na verdade quanto é 4 mais 3?", name="Marianna")]}

            ## Updates the graph state, setting the new message as the actual state
            status = workflow.update_state(
                config,
                new_message
            )

            ## Using input=None, the workflow follows from where it stopped before
            for event in workflow.stream(input=None, config=config, stream_mode="values"):
                event['messages'][-1].pretty_print()
            
            ## As the workflow always stops before the assistant, we need to call the stream again to the assistant give the final answer
            for event in workflow.stream(input=None, config=config, stream_mode="values"):
                event['messages'][-1].pretty_print()