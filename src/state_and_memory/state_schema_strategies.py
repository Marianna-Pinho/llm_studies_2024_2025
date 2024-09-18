# Import libraries
from typing import TypedDict, Literal
from dataclasses import dataclass
from langchain_core.pydantic_v1 import BaseModel, validator, ValidationError


# 1. Commonly used TypedDict (It doesn't enforce types in running time)
class StateWithTypedDict(TypedDict):
    name: str
    favorite_food: Literal["pasta","sushi","ice cream"]

# 2. Alternative 1: Dataclass (It doesn't enforce types in running time)
@dataclass
class StateWithDataclass:
    name: str
    favorite_food: Literal["pasta","sushi","ice cream"]

# 3. Alternative 2: Pydantic (it can be used to enforce types, performing checkings and data validations in running time).
class StateWithPydantic(BaseModel):
    name: str
    favorite_food: Literal["pasta","sushi","ice cream"]

    @validator('favorite_food')
    def validate_food(cls, value):
        if value not in ["pasta","sushi","ice cream"]:
            raise ValueError("Favorite food must be either 'pasta', 'sushi' or 'ice cream'")
        
        return value
    

if __name__ == "__main__":
    try:
        state_typed_dict = StateWithTypedDict(name="marianna", favorite_food="lasanha")
        print("======= TypedDict =========\n", state_typed_dict)
    except ValidationError as e:
        print("Validation Error in State with TypedDict:", e)

    try:
        state_dataclass = StateWithDataclass(name="marianna", favorite_food="lasanha")
        print("======= Dataclass =========\n", state_dataclass)
    except ValidationError as e:
        print("Validation Error in State with Dataclass:", e)

    try:
        state_pydantic = StateWithPydantic(name="marianna", favorite_food="lasanha")
        print("======= Pydantic =========\n", state_pydantic)
    except ValidationError as e:
        print("Validation Error in State with Pydantic:", e)