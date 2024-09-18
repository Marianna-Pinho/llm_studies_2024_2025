from typing import TypedDict
from langgraph.graph import START, END, StateGraph


# 1. Working with internal (private) and overall states

# A. Define the Private state
class StatePrivate(TypedDict):
    person_cpf: str
    person_address: str

# B. Define the Overall state
class StateOverall(TypedDict):
    name: str
    is_a_brazilizan_citizen: bool

# C. Create the nodes with different internal and overall states

def query_person_info_node(state: StateOverall) -> StatePrivate:
    print("---------- Query Person Info Node -----------")
    #Given the name, make queries in internal systems to find CPF and Address
    return {"person_cpf": "123456789", "person_address":"Rua da Aurora"}

def citizen_querying_node(state: StatePrivate) -> StateOverall:
    print("---------- Citizen Querying Node ------------------")
    # Check CPF and Address infos to validate citizenship
    return {"is_a_brazilizan_citizen": True}

# D. Create the graph
def create_private_overall_graph():
    graph = StateGraph(StateOverall)

    graph.add_node("query info", query_person_info_node)
    graph.add_node("check citizenship", citizen_querying_node)

    graph.add_edge(START, "query info")
    graph.add_edge("query info", "check citizenship")
    graph.add_edge("check citizenship", END)

    graph = graph.compile()

    return graph

# E. Create testing function
def test_internal_overall_states_graph():
    graph = create_private_overall_graph()
    person_info = {"name": "Marianna Pinho"}

    for chunk in graph.stream(input=person_info):
        print(chunk)

    response = graph.invoke(input=person_info)
    print(response)


#============================================

# 2. Working with different input/output schemas

# A. Define the overall state
class StateGeneral(TypedDict):
    name: str
    age: int
    cpf: str

# B. Define the input state
class StateInput(TypedDict):
    cpf: str

# C. Define the output state
class StateOutput(TypedDict):
    name: str

# D. Define the nodes
def query_by_cpf_node(state: StateInput) -> StateGeneral:
    print("---------- Query by CPF Node ----------------")
    # Query the name and age of a person, given the cpf.
    cpf = state["cpf"]
    # bla bla bla with cpf
    return {"name": "Marianna Pinho", "age": 80}

def create_answer_node(state: StateGeneral) -> StateOutput:
    print("---------------- Create Answer Node ---------------")
    return {"name": state["name"]}

# E. Create graph
def create_input_output_graph():
    graph = StateGraph(StateGeneral, input=StateInput, output=StateOutput)

    graph.add_node("query cpf", query_by_cpf_node)
    graph.add_node("create answer", create_answer_node)

    graph.add_edge(START, "query cpf")
    graph.add_edge("query cpf", "create answer")
    graph.add_edge("create answer", END)

    graph = graph.compile()

    return graph

# G. Create testing function
def test_input_output_states_graph():
    person_cpf = {"cpf": "123456789"}
    graph = create_input_output_graph()

    for chunk in graph.stream(input=person_cpf):
        print(chunk)

    response = graph.invoke(input=person_cpf)
    print(response)


if __name__ == "__main__":
    test_internal_overall_states_graph()
    test_input_output_states_graph()