"""bmt module."""
from collections import defaultdict
from io import TextIOWrapper
from functools import lru_cache
from typing import Dict, List, Union, TextIO, Optional, Set

import requests
import yaml

REMOTE_PATH = 'https://biolink.github.io/biolink-model/biolink-model.yaml'


class Toolkit(object):
    """
    Provides a series of methods for performing lookups on the
    biolink-model.yaml file.
    """

    def __init__(self, schema: Union[str, TextIO] = REMOTE_PATH) -> None:
        """
        Instantiates a Toolkit object.

        Parameters
        ----------
        schema : Union[str, TextIO, SchemaDefinition]
            The path or url to an instance of the biolink-model.yaml file.
        """
        if isinstance(schema, str):
            response = requests.get(schema)
            response.encoding = "ascii"
            self.model = yaml.load(response.text, Loader=yaml.SafeLoader)
        elif isinstance(schema, TextIOWrapper):
            self.model = yaml.load(schema.read(), Loader=yaml.SafeLoader)
        else:
            raise ValueError()

        self.slots = self.model["slots"]
        self.classes = self.model["classes"]
        self.elements = {
            **self.slots,
            **self.classes,
        }
        self.slot_parents = {
            key: [value.get("is_a", None)]
            for key, value in self.slots.items()
        }
        self.slot_children = defaultdict(list)
        for child, parents in self.slot_parents.items():
            for parent in parents:
                self.slot_children[parent].append(child)
        self.class_parents = {
            key: [value.get("is_a", None)]
            for key, value in self.classes.items()
        }
        self.class_children = defaultdict(list)
        for child, parents in self.class_parents.items():
            for parent in parents:
                self.class_children[parent].append(child)
        self._children = {
            **self.slot_children,
            **self.class_children,
        }
        self._parents = {
            **self.slot_parents,
            **self.class_parents,
        }

    @lru_cache()
    def names(self) -> List[str]:
        """
        Gets the list of names of all elements

        Returns
        -------
        List[str]
            The names of all elements in biolink-model.yaml
        """
        # this is not quite the same as previously - it's too long
        return list(self.model["classes"].keys()) + list(self.model["slots"].keys())

    @lru_cache()
    def ancestors(self, name: str) -> List[str]:
        """
        Gets a list of names of ancestors.

        Parameters
        ----------
        name : str
            The name of an element in the biolink model.

        Returns
        -------
        List[str]
            The names of the given elements ancestors.
        """
        parent = self.parent(name)
        if parent is None:
            return []
        return [parent] + self.ancestors(parent)


    @lru_cache()
    def descendents(self, name: str) -> List[str]:
        """
        Gets a list of names of descendents.

        Parameters
        ----------
        name : str
            The name of an element in the biolink model.

        Returns
        -------
        List[str]
            The names of the given elements descendents.
        """
        c = []
        for child in self.children(name):
            c.append(child)
            c += self.descendents(child)
        return c

    @lru_cache()
    def children(self, name: str) -> List[str]:
        """
        Gets a list of names of children.

        Parameters
        ----------
        name : str
            The name of an element in the biolink model.

        Returns
        -------
        List[str]
            The names of the given elements children.
        """
        return self._children.get(name, [])

    @lru_cache()
    def parent(self, name: str) -> Optional[str]:
        """
        Gets the name of the parent.

        Parameters
        ----------
        name : str
            The name of an element in the biolink model.

        Returns
        -------
        Optional[str]
            The name of the given elements parent
        """
        try:
            parents = self._parents[name]
        except KeyError:
            return None
        return parents[0]

    @lru_cache()
    def get_element(self, name: str) -> Optional[Dict]:
        """
        Gets an element that is identified by the given name, either as its name
        or as one of its aliases.

        Parameters
        ----------
        name : str
            The name or alias of an element in the biolink model.

        Returns
        -------
        Element
            The element identified by the given name
        """
        return self.elements.get(name, None)

    @lru_cache()
    def is_edgelabel(self, name: str) -> bool:
        """
        Determines whether the given name is the name of an edge label in the
        biolink model. An element is an edge label just in case it's in the
        `translator_minimal` subset.

        Parameters
        ----------
        name : str
            The name or alias of an element in the biolink model.

        Returns
        -------
        bool
            That the named element is in the translator_minimal subset
        """
        element = self.get_element(name)
        if element is None:
            return False
        return "translator_minimal" in element.get("in_subset", [])

    @lru_cache()
    def is_category(self, name: str) -> bool:
        """
        Determines whether the given name is the name of a category in the
        biolink model. An element is a category just in case it descends from
        `named thing`

        Parameters
        ----------
        name : str
            The name or alias of an element in the biolink model.

        Returns
        -------
        bool
            That the named element descends from `named thing`
        """
        return name == "named thing" or "named thing" in self.ancestors(name)

    @lru_cache()
    def get_all_by_mapping(self, uriorcurie: str) -> Set[str]:
        """
        Gets the set of biolink entities that the given uriorcurie maps to. Mappings
        are determined by the combination of the entity URI (if one exists) combined
        with the entities `mappings` property.

        For example:

              causes:
                description: >-
                  holds between two entities where the occurrence, existence,
                  or activity of one causes the occurrence or  generation of
                  the other
                is_a: contributes to
                in_subset:
                  - translator_minimal
                mappings:
                  - RO:0002410
                  - SEMMEDDB:CAUSES
                  - WD:P1542

        Parameters
        ----------
        uriorcurie : str
            A URI or CURIE (compact URI) identifier of an entity in biolink-model.yaml

        Returns
        -------
        Set[str]
            The set of names of entities that the given uriorcurie maps onto
        """
        mappings = set()
        for key, element in self.elements.items():
            if uriorcurie in element.get("mappings", []):
                mappings.add(key)
        return mappings

    @lru_cache()
    def get_by_mapping(self, uriorcurie: str) -> Optional[str]:
        """
        Return the most distal common ancestor of the set of elements referenced buy uriorcurie


        Parameters
        ----------
        uriorcurie : str
            A URI or CURIE (compact URI) identifier of an entity in biolink-model.yaml

        Returns
        -------
        Optional[str]
            The most distal common ancestor of URI in the model hierarhy
        """
        mappings = list(self.get_all_by_mapping(uriorcurie))
        if not mappings:
            return None
        shared_ancestors = [mappings[0]] + self.ancestors(mappings[0])
        if not shared_ancestors:
            return None
        for mapping in mappings[1:]:
            ancestors = [mapping] + self.ancestors(mapping)
            shared_ancestors = [
                shared_ancestor
                for shared_ancestor in shared_ancestors
                if shared_ancestor in ancestors
            ]
            if not shared_ancestors:
                return None
        return shared_ancestors[0]
