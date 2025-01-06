import dotenv
import asyncio

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import START, END, StateGraph, MessagesState
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode, tools_condition
from langchain.tools import tool
from langgraph.errors import NodeInterrupt

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
        if a < 0 or b < 0:
            raise NodeInterrupt(f"Received negative inputs: {a,b}")
        return a+b
    
    @staticmethod
    @tool
    def multiply_numbers(a:int, b:int):
        '''Multiply two numbers'''
        if a < 0 or b < 0:
            raise NodeInterrupt(f"Received negative inputs: {a,b}")
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
    workflow = Chatbot(checkpointer=MemorySaver(), when_interrupt=None).workflow
    initial_message = {"messages": [HumanMessage(content="Quanto é -1 mais 3?", name="Marianna")]}
    config = {"configurable": {"thread_id":"1"}}
   
    ## Experiment interrupting the workflow before the assistant node and asking for approval or an edditing.
    ## It continues the workflow if we answer yes or it edits the workflow if we answer no.
    print("=========== Example of Dynamic Break =======")

    for event in workflow.stream(input=initial_message, config=config, stream_mode="values"):
        event['messages'][-1].pretty_print()
    
    state = workflow.get_state(config)

    print("Next State:", state.next)
    print("Logs:", state.tasks)


    print("---"*10, "Repeating Error","---"*10)
    ## If we try to continue, nothing is gonna happen because we are going to try to execute the same node with the same inputs that raised the error.
    for event in workflow.stream(input=None, config=config, stream_mode="values"):
        event['messages'][-1].pretty_print()


    print("---"*10, "Updating State","---"*10)
    ## So, we need to update the inputs if we wanna continue.
    new_message = {'messages': [HumanMessage(content='Quanto é 5 mais 3?', additional_kwargs={}, response_metadata={}, name='Marianna', id='a1cac075-848e-4196-b6ec-4dbb1abe1fc6'), AIMessage(content='', additional_kwargs={'tool_calls': [{'index': 0, 'id': 'call_vQDNonoV5qyP4e1I2qldbbZy', 'function': {'arguments': '{"a":5,"b":3}', 'name': 'sum_numbers'}, 'type': 'function'}]}, response_metadata={'finish_reason': 'tool_calls', 'model_name': 'gpt-3.5-turbo-0125'}, id='run-4bc5d5cb-595b-4828-a069-372f33306ea8-0', tool_calls=[{'name': 'sum_numbers', 'args': {'a': 5, 'b': 3}, 'id': 'call_vQDNonoV5qyP4e1I2qldbbZy', 'type': 'tool_call'}])]}
    ## Updates the graph state, setting the new message as the actual state
    status = workflow.update_state(
        config,
        new_message
    )

    print("---"*10,"Finishing the workflow","---"*10)
    ## Now we can perform the new operation
    for event in workflow.stream(input=None, config=config, stream_mode="values"):
        event['messages'][-1].pretty_print()
