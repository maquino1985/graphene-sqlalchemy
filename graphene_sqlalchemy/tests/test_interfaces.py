import logging

from graphene import Node
from graphene.relay.node import NodeField

from .models import Pet as PetModel, Dog as DogModel
from ..interfaces import SQLAlchemyInterface
from ..registry import Registry
from ..types import SQLAlchemyObjectType

log = logging.getLogger(__name__)


class PetIface(SQLAlchemyInterface):
    class Meta:
        model = PetModel
        name = 'PetInterface'
        registry = Registry()


def test_model_is_interface():
    reg = Registry()

    class Dog(SQLAlchemyObjectType):
        class Meta:
            model = DogModel
            registry = reg
            interfaces = (PetIface,)

    reg.register(Dog)

    assert reg.get_type_for_model(DogModel) is Dog
    d = DogModel(favorite_toy='stick', pet_kind='dog')
    assert Dog is PetIface.resolve_type(d, None, registry=reg)


def test_interface_is_node():
    class PetIface(SQLAlchemyInterface):
        class Meta:
            model = PetModel
            name = 'PetInterface'
            registry = Registry()

    assert issubclass(PetIface, Node)


def test_interface_field():
    field = PetIface.Field()
    assert isinstance(field, NodeField)
