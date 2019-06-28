import logging

import pytest
from graphene import InputObjectType
from graphene.relay import Connection
from sqlalchemy import inspect

from .models import Editor as EditorModel
from .models import Pet as PetModel
from ..fields import SQLAlchemyConnectionField, SQLAlchemyFilteredConnectionField
from ..types import SQLAlchemyObjectType

log = logging.getLogger(__name__)
class Pet(SQLAlchemyObjectType):
    class Meta:
        model = PetModel


class Editor(SQLAlchemyObjectType):
    class Meta:
        model = EditorModel


class PetConn(Connection):
    class Meta:
        node = Pet


def test_where_filter_added():
    field = SQLAlchemyFilteredConnectionField(Pet)
    assert "where" in field.args
    assert issubclass(field.args['where']._type, InputObjectType)
    filter_fields = field.args['where']._type._meta.fields
    log.info(filter_fields)
    filter_column_names = [column.name for column in inspect(Pet._meta.model).columns.values()] + ['and', 'or']
    for field_name, value in filter_fields.items():
        assert field_name in filter_column_names


def test_init_raises():
    with pytest.raises(TypeError, match="Cannot create sort"):
        SQLAlchemyFilteredConnectionField(Connection)


def test_sort_added_by_default():
    field = SQLAlchemyConnectionField(PetConn)
    assert "sort" in field.args
    assert field.args["sort"] == Pet.sort_argument()


def test_sort_can_be_removed():
    field = SQLAlchemyConnectionField(PetConn, sort=None)
    assert "sort" not in field.args


def test_custom_sort():
    field = SQLAlchemyConnectionField(PetConn, sort=Editor.sort_argument())
    assert field.args["sort"] == Editor.sort_argument()


def test_init_raises():
    with pytest.raises(TypeError, match="Cannot create sort"):
        SQLAlchemyConnectionField(Connection)
