from __future__ import absolute_import

import enum

from sqlalchemy import Column, Date, Enum, ForeignKey, Integer, String, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative.api import declared_attr
from sqlalchemy.orm import mapper, relationship

PetKind = Enum("cat", "dog", name="pet_kind")


class HairKind(enum.Enum):
    LONG = 'long'
    SHORT = 'short'


Base = declarative_base()

association_table = Table(
    "association",
    Base.metadata,
    Column("pet_id", Integer, ForeignKey("pets.id")),
    Column("reporter_id", Integer, ForeignKey("reporters.id")),
)


class Editor(Base):
    __tablename__ = "editors"
    editor_id = Column(Integer(), primary_key=True)
    name = Column(String(100))


class Pet(Base):
    __tablename__ = "pets"
    id = Column(Integer(), primary_key=True)
    name = Column(String(30))
    pet_kind = Column(PetKind, nullable=False)
    hair_kind = Column(Enum(HairKind, name="hair_kind"), nullable=False)
    reporter_id = Column(Integer(), ForeignKey("reporters.id"))

    @declared_attr
    def __mapper_args__(cls):
        if cls.__name__ == 'Pet':
            return {
                "polymorphic_on": cls.pet_kind,
                "polymorphic_identity": cls.__tablename__
            }
        else:
            return {"polymorphic_identity": cls.__tablename__}

class Reporter(Base):
    __tablename__ = "reporters"
    id = Column(Integer(), primary_key=True)
    first_name = Column(String(30))
    last_name = Column(String(30))
    email = Column(String())
    favorite_pet_kind = Column(PetKind)
    pets = relationship("Pet", secondary=association_table, backref="reporters")
    articles = relationship("Article", backref="reporter")
    favorite_article = relationship("Article", uselist=False)

    # total = column_property(
    #     select([
    #         func.cast(func.count(PersonInfo.id), Float)
    #     ])
    # )


class PetMixin:
    @declared_attr
    def id(cls) -> Column:
        return Column(ForeignKey('pets.id'), primary_key=True)


class Dog(PetMixin, Pet):
    __tablename__ = 'dog'
    favorite_toy = Column(String)


class Cat(PetMixin, Pet):
    __tablename__ = 'cat'
    favorite_toy = Column(String)

class Article(Base):
    __tablename__ = "articles"
    id = Column(Integer(), primary_key=True)
    headline = Column(String(100))
    pub_date = Column(Date())
    reporter_id = Column(Integer(), ForeignKey("reporters.id"))


class ReflectedEditor(type):
    """Same as Editor, but using reflected table."""

    @classmethod
    def __subclasses__(cls):
        return []


editor_table = Table("editors", Base.metadata, autoload=True)

mapper(ReflectedEditor, editor_table)
