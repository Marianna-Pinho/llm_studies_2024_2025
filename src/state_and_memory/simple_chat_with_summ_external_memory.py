import dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langgraph.graph import START, END, StateGraph
from langchain_core.messages import AnyMessage, AIMessage, HumanMessage, SystemMessage, RemoveMessage
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

# Set up env variables
print("Is env variables loaded?", dotenv.load_dotenv(".env"))

chat_model = ChatOpenAI(model="gpt-3.5-turbo")

# 1. Define the state of the graph, which will also have a summary key now
class StateSum(MessagesState):
    # It already has the built-in messages attribute
    summary: str

# 2. Create the nodes of the graph

## A. The model calling node
def chat_node_with_summary(state:StateSum):
    # Get the summary if it exists
    summary = state.get("summary", "")

    # Prepare the input for the model
    if summary:
        ## If the summary exists, we add it to the system message
        system_message = f"Summary of the conversation earlier: {summary}"
        ## Then, append the system message to the list of messages. 
        ## It makes the model knows about the summary when treating new messages
        messages = [SystemMessage(content=system_message)] + state["messages"]
    else:
        ## It there is no summary, we use just the messages in the list
        messages = state["messages"]
    
    # Then, we invoke the model
    response = chat_model.invoke(input=messages)

    # And updates the messages attribute
    return {"messages": response}

## B. The summarization node
def summarize_conversation(state: StateSum):
    # Get the summary if it exists
    summary = state.get("summary", "")

    # Create the summarization prompt
    if summary:
        # If a summary already exists, we ask the summarization model to extend it with a summarization of the new messages
        summary_message = (
            f"This is a summary of the conversation to date: {summary}\n\n"
            "Extend the summary by taking into account the new messages above."
        )
    else:
        # If there is no summary, we ask the summarization model to create one from the messages history
        summary_message = "Create a summary of the conversation above."
    
    # The summary prompt is added to the history as a new message from the user
    messages = state["messages"] + [HumanMessage(content=summary_message)]

    # We call the model to summarize the conversation
    response = chat_model.invoke(input=messages)

    # Once we have the summary, we can delete the N first messages from the history, to save space, token usage and latency
    messages_to_delete = [RemoveMessage(id=msg.id) for msg in state["messages"][:-3]]

    # Now, we update the state, setting the currently summary and the messages to be deleted (reducers tricks)
    return {"summary": response.content, "messages": messages_to_delete}


# 3. Define the conditional edges
## We don't want to create a summary at each new conversation step. So, we can create a conditional edge
## that routes us to the summarization node any time a number X of messages in the history is found.

def summarization_conditional_edge(state: StateSum):
    """
    Returns the next node to execute
    """

    messages = state["messages"]

    if len(messages) > 6:
        return "summarization node"
    else:
        return END


# 4. Create the graph

def create_graph(path_checkpoint):
    graph = StateGraph(StateSum)

    graph.add_node("chat node", chat_node_with_summary)
    graph.add_node("summarization node", summarize_conversation)

    graph.add_edge(START, "chat node")
    graph.add_conditional_edges(
        source="chat node",
        path = summarization_conditional_edge
    )
    graph.add_edge("summarization node", END)

    ## Here, we will use an SQLite database to persist the graph states
    sqlite_connection = sqlite3.connect(database=path_checkpoint, check_same_thread=False)
    memory = SqliteSaver(sqlite_connection)
    graph = graph.compile(checkpointer=memory)

    return graph

if __name__ == "__main__":
    initial_messages = {"messages": [
        AIMessage(content="Oi, como posso te ajudar?", name="Model"),
        HumanMessage(content="Olá, gostaria de saber mais sobre dinossauros.", name="Marianna"),
        AIMessage(content="Claro! O que você gostaria de saber especificamente?", name="Model"),
        HumanMessage(content="Temos dinossauros atualmente?", name="Marianna")
    ]}

    graph = create_graph(path_checkpoint="src/databases/chat_with_summ_and_external_memory.db")
    config = {"configurable": {"thread_id": "2"}}

    # save graph schema
    with open("figures/chat_summarization_graph.png", "wb") as f:
        f.write(graph.get_graph().draw_mermaid_png())

    response = graph.invoke(input=initial_messages, config=config)
    print("SUMMARY 1:", response.get("summary", ""))

    for msg in response["messages"]:
        msg.pretty_print()
    
    #----------------------------------------------------------------------

    new_message = [HumanMessage(content="aves podem ser consideradas dinossauros?", name="Marianna")]
    messages = initial_messages["messages"]+new_message

    response = graph.invoke(input={"messages": messages}, config=config)
    print("SUMMARY 2:", response.get("summary", ""))

    for msg in response["messages"]:
        msg.pretty_print()

    # ------------------------------------------------------------------
    graph_state_check = graph.get_state(config=config)
    print("=================================================================")
    print(graph_state_check)