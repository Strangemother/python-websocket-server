from pydantic import BaseModel, create_model
from typing import Optional


class NewScene(BaseModel):
    unit: str
    new_network: int
    owner: int
    root: int


class NewClient(BaseModel):
    unit: str
    owner: int


# class Item(BaseModel):
#     name: str
#     description: Optional[str] = None
#     price: float
#     tax: Optional[float] = None

all_models = (
    NewScene,
    NewClient,
    # Item,
)

register = {}
for class_ in all_models:
    register[class_.__name__.lower()] = class_


def convert(packet, name):
    """Convert a packet to a model type, populating the model with the packet
    json content.
    """
    # DynamicFoobarModel = create_model('DynamicFoobarModel', foo=(str, ...), bar=123)
    # M = create_model(name)
    nn = register.get(name.lower())(**packet.get_json(), owner=packet.owner.uuid)
    return nn

