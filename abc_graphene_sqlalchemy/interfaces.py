from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Tuple, Union, Optional
from uuid import UUID

import graphene
import sqlalchemy
from graphene.relay.node import NodeField, AbstractNode
from graphene.types.interface import InterfaceOptions
from sqlalchemy.ext.declarative import DeclarativeMeta

from .registry import Registry
from .utils import is_mapped_class

if TYPE_CHECKING:
    from typing import List

from graphene import Field
from graphene.relay import Connection, Node
from graphene.types.utils import yank_fields_from_attrs
from .fields import default_connection_field_factory, UnsortedSQLAlchemyConnectionField
from .registry import get_global_registry

log = logging.getLogger(__name__)


class SQLAlchemyInterfaceOptions(InterfaceOptions):
    model: DeclarativeMeta = None
    registry: Registry = None
    connection: Connection = None
    id: Union[str, int, UUID] = None


def exclude_autogenerated_sqla_columns(model: DeclarativeMeta) -> Tuple[str]:
    # always pull ids out to a separate argument
    autoexclude: List[str] = []
    for col in sqlalchemy.inspect(model).columns:
        if ((col.primary_key and col.autoincrement) or
                (isinstance(col.type, sqlalchemy.types.TIMESTAMP) and
                 col.server_default is not None)):
            autoexclude.append(col.name)
            assert isinstance(col.name, str)
    return tuple(autoexclude)


class SQLAlchemyInterface(Node):
    @classmethod
    def __init_subclass_with_meta__(
            cls,
            model: DeclarativeMeta = None,
            registry: Registry = None,
            only_fields: Tuple[str] = (),
            exclude_fields: Tuple[str] = (),
            connection_field_factory: UnsortedSQLAlchemyConnectionField = default_connection_field_factory,
            **options
    ):
        _meta = SQLAlchemyInterfaceOptions(cls)
        _meta.name = f'{cls.__name__}Node'

        autoexclude_columns = exclude_autogenerated_sqla_columns(model=model)
        exclude_fields += autoexclude_columns

        assert is_mapped_class(model), (
            "You need to pass a valid SQLAlchemy Model in " '{}.Meta, received "{}".'
        ).format(cls.__name__, model)

        if not registry:
            registry = get_global_registry()

        assert isinstance(registry, Registry), (
            "The attribute registry in {} needs to be an instance of "
            'Registry, received "{}".'
        ).format(cls.__name__, registry)
        from .types import construct_fields

        sqla_fields = yank_fields_from_attrs(
            construct_fields(
                obj_type=cls,
                model=model,
                registry=registry,
                only_fields=only_fields,
                exclude_fields=exclude_fields,
                connection_field_factory=connection_field_factory
            ),
            _as=Field
        )
        if not _meta:
            _meta = SQLAlchemyInterfaceOptions(cls)
        _meta.model = model
        _meta.registry = registry
        connection = Connection.create_type(
            "{}Connection".format(cls.__name__), node=cls)
        assert issubclass(connection, Connection), (
            "The connection must be a Connection. Received {}"
        ).format(connection.__name__)
        _meta.connection = connection
        if _meta.fields:
            _meta.fields.update(sqla_fields)
        else:
            _meta.fields = sqla_fields
        _meta.fields['id'] = graphene.GlobalID(cls, description="The ID of the object.")
        # call super of AbstractNode directly because it creates its own _meta, which we don't want
        super(AbstractNode, cls).__init_subclass_with_meta__(_meta=_meta, **options)

    @classmethod
    def Field(cls, *args, **kwargs):  # noqa: N802
        return NodeField(cls, *args, **kwargs)

    @classmethod
    def node_resolver(cls, only_type, root, info, id):
        return cls.get_node_from_global_id(info, id, only_type=only_type)

    @classmethod
    def get_node_from_global_id(cls, info, global_id, only_type=None):
        try:
            node: DeclarativeMeta = info.context.get('session').query(cls._meta.model).filter_by(id=global_id).one()
            return node
        except Exception:
            return None

    @classmethod
    def from_global_id(cls, global_id):
        return global_id

    @classmethod
    def to_global_id(cls, type, id):
        return id

    @classmethod
    def resolve_type(cls, instance, info, registry: Optional[Registry] = None):
        if isinstance(instance, graphene.ObjectType):
            return type(instance)
        if not registry:
            if not hasattr(cls._meta, 'registry'):
                registry = get_global_registry()
            else:
                registry = cls._meta.registry
        graphene_model = registry.get_type_for_model(type(instance))
        if graphene_model:
            return graphene_model
        else:
            raise ValueError(f'{type(instance)} must be a SQLAlchemy model or graphene.ObjectType')