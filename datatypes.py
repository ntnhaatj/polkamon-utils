from dataclasses import dataclass
from functools import reduce

from datetime import datetime
import pytz


@dataclass
class Rarity:
    horn: float
    color: float
    background: float
    glitter: float
    type: float

    @classmethod
    def from_metadata(cls, metadata: dict):
        rarity = metadata['initialProbabilities']
        return cls(horn=rarity['horn'],
                   color=rarity['color'],
                   background=rarity['background'],
                   glitter=rarity['glitter'],
                   type=rarity['type'])

    @property
    def value(self):
        return reduce(lambda r, k: r * getattr(self, k),
                      self.__dataclass_fields__.keys(),
                      1)


@dataclass
class Attribute:
    birthday: str
    color: str

    @classmethod
    def __array_to_dict(cls, attributes: list):
        attributes_dict = {
            attr['trait_type']: attr['value']
            for attr in attributes
        }
        return attributes_dict

    @classmethod
    def from_metadata(cls, metadata: dict):
        attributes = cls.__array_to_dict(metadata['attributes'])
        return cls(
            birthday=datetime
                .fromtimestamp(attributes['Birthday'], tz=pytz.timezone("Asia/Singapore"))
                .strftime('%Y-%m-%d %H:%M:%S'),
            color=attributes['Color'])
