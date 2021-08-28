from dataclasses import dataclass
from datatypes import Type, Horn, Color


@dataclass
class FilterBuilder:
    type: Type = None
    horn: Horn = None
    color: Color = None

    @property
    def name(self):
        return " ".join((a.value for a in (self.horn, self.color, self.type) if a is not None))


@dataclass
class SCVFilterBuilder(FilterBuilder):
    base_url: str = "https://scv.finance/nft/collection/polychain-monsters"
    base_filters: tuple = (
        "sort=price_asc",
    )

    @property
    def filters(self):
        return filter(
            lambda f: f is not None,
            (*self.base_filters,
             f"meta_text_0={self.type.value}" if self.type else None,
             f"meta_text_1={self.horn.value}" if self.horn else None,
             f"meta_text_2={self.color.value}" if self.color else None)
        )

    @property
    def url(self):
        return "{base_url}?{filters}".format(
            base_url=self.base_url,
            filters="&".join(self.filters))


@dataclass
class OSFilterBuilder(FilterBuilder):
    base_url: str = "https://opensea.io/collection/polychainmonsters"
    base_filters: tuple = (
        "search[resultModel]=ASSETS",
        "search[sortAscending]=true",
        "search[sortBy]=PRICE"
    )

    @property
    def filters(self):
        return filter(
            lambda f: f is not None,
            (*self.base_filters,
             f"search[stringTraits][0][name]=Type"
             f"&search[stringTraits][0][values][0]={self.type.value}" if self.type else None,
             f"search[stringTraits][1][name]=Color"
             f"&search[stringTraits][1][values][0]={self.color.value}" if self.color else None,
             f"search[stringTraits][2][name]=Horn"
             f"&search[stringTraits][2][values][0]={self.horn.value}" if self.horn else None,)
        )

    @property
    def url(self):
        return "{base_url}?{filters}".format(
            base_url=self.base_url,
            filters="&".join(self.filters))
