import operator
from typing import Annotated, TypedDict, Optional
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage, AIMessage, HumanMessage, RemoveMessage

# 1. State with default attributes update behavior: overwrite
class StateDefault(TypedDict):
    messages: str
    key1: int

# 2. State with Add reducer, used to append new messages to the attribute 'messages' instead of overwriting it.
class StateAppend(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    key1: int

# 3. State with the same previous behavior, but using prebuilt LangGraph structures.
class StatePrebuilt(MessagesState):
    # The 'messages' attribute, along with Annotated and operator.add/add_messages operations are prebuilt in this class.
    # So, we just need to specify the new attributes 
    key1: int

# 4. State with a Custom Reducer to treat None values
def custom_reduce_lists_with_none(left_list: Optional[list] = None, right_list: Optional[list] = None) -> list:
    if not left_list:
        left_list = []
    if not right_list:
        right_list = []
    
    return left_list + right_list

class StateCustomReducer(TypedDict):
    messages: Annotated[list[AnyMessage], custom_reduce_lists_with_none]
    key1: int


def test_state_reducers():
    initial_messages = [
        AIMessage(content="Olá, como posso te ajudar hoje?", name="Model", id=1),
        HumanMessage(content="Oii, gostaria de saber mais sobre a história do saxofone.", name="Marianna", id=2)
    ]

    new_message = HumanMessage(content="Quem o criou?", name="Marianna", id=3)

    print("------------------------ operator.add ------------------------\n")
    messages = operator.add(initial_messages, [new_message])
    for msg in messages:
        msg.pretty_print()
    
    try:
        messages = add_messages(initial_messages, None)
        for msg in messages:
            msg.pretty_print()
    except Exception as e:
        print("Error:", e)

    print("\n------------------------ add_messages ------------------------\n")
    messages = add_messages(initial_messages, new_message)
    for msg in messages:
        msg.pretty_print()

    try:
        messages = add_messages(initial_messages, None)
        for msg in messages:
            msg.pretty_print()
    except Exception as e:
        print("Error:", e)
    
    print("\n------------------------ custom reducer ------------------------\n")
    messages = custom_reduce_lists_with_none(initial_messages, [new_message])
    for msg in messages:
        msg.pretty_print()

    try:
        messages = custom_reduce_lists_with_none(initial_messages, None)
        for msg in messages:
            msg.pretty_print()
    except Exception as e:
        print("Error:", e)


def test_tricks_with_reducers():
    initial_messages = [
        AIMessage(content="Olá, como posso te ajudar hoje?", name="Model", id=1),
        HumanMessage(content="Oii, gostaria de saber mais sobre a história do saxofone.", name="Marianna", id=2)
    ]    

    print("------------------ Overwrite Message --------------")
    new_message = HumanMessage(content="Quem o criou?", name="Marianna", id=1)
    messages = add_messages(initial_messages, new_message)
    for msg in messages:
        msg.pretty_print()

    print("------------------ Remove Message --------------")
    new_message = HumanMessage(content="Quem o criou?", name="Marianna", id=3)
    messages = initial_messages + [new_message]
    print("BEFORE:")
    for msg in messages:
        msg.pretty_print()


    messages_to_delete = [RemoveMessage(id=msg.id) for msg in messages[:-1]]
    print(messages_to_delete)
    messages = add_messages(messages, messages_to_delete)

    print("AFTER:")
    for msg in messages:
        msg.pretty_print()

if __name__ == "__main__":
    test_state_reducers()
    test_tricks_with_reducers()
   
    