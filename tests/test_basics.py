"""Test methods."""
from inspect import signature
import os

import bmt_lite

file_dir = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(file_dir, "data", "toy_model.yml")) as stream:
    tk = bmt_lite.Toolkit(stream)


def test_get_element():
    gene = tk.get_element("gene")
    locus = tk.get_element("locus")

    assert gene == locus
    assert gene is not None


def test_edgelabel():
    assert not tk.is_edgelabel("named thing")
    assert not tk.is_edgelabel("gene")
    assert tk.is_edgelabel("causes")


def test_category():
    assert tk.is_category("named thing")
    assert tk.is_category("gene")
    assert not tk.is_category("causes")


def test_ancestors():
    assert "related to" in tk.ancestors("causes")
    assert "named thing" in tk.ancestors("gene")


def test_descendents():
    assert "causes" in tk.descendents("related to")
    assert "gene" in tk.descendents("named thing")


def test_children():
    assert "causes" in tk.children("contributes to")


def test_parent():
    assert "contributes to" == tk.parent("causes")


def test_mapping():
    # The following tests apply to the two ancestor paths:
    #    Path 1:
    #    "negatively regulates, process to process"    probe2   probe3  probe4
    #        "regulates, process to process"                    probe3  probe4
    #            "regulates"
    #                "affects"              probe1     probe2           probe4
    #                    "related to"
    #    Path 2:
    #    "negatively regulates, entity to entity"               probe3
    #        "regulates, entity to entity"                      probe3  probe4
    #            "regulates"
    #                "affects"              probe1     probe2           probe4
    #                    "related to"

    # probe0 has no mappings
    assert set() == tk.get_all_by_mapping("biolink:probe0")
    assert tk.get_by_mapping("biolink:probe0") is None

    #  probe1 should return "affects"
    assert {"affects"} == tk.get_all_by_mapping("biolink:probe1")
    assert "affects" == tk.get_by_mapping("biolink:probe1")

    #  probe2 should return "affects"
    assert {"negatively regulates, process to process", "affects"} == tk.get_all_by_mapping("biolink:probe2")
    assert "affects" == tk.get_by_mapping("biolink:probe2")

    #  probe3 should return None
    assert {
        "negatively regulates, process to process",
        "regulates, process to process",
        "positively regulates, entity to entity",
        "regulates, entity to entity"
    } == tk.get_all_by_mapping("biolink:probe3")

    #  probe4 should return "affects
    assert {
        "negatively regulates, process to process",
        "regulates, process to process",
        "positively regulates, entity to entity",
        "regulates, entity to entity",
        "affects"
    } == tk.get_all_by_mapping("biolink:probe4")
    assert "affects" == tk.get_by_mapping("biolink:probe4")


def test_inputs():
    """
    All methods in toolkit.ToolKit take a single string as an input. This test
    checks that they still work for invalid inputs and return None.
    """

    for name in dir(tk):
        if name.startswith("_"):
            continue
        method = getattr(tk, name)
        if hasattr(method, "__call__"):
            sig = signature(method)
            if len(sig.parameters) == 1:
                # Testing the standard lookup methods
                method(None)
                method(3)
                method("invalid")
                method(0.25)
            else:
                method(*sig.parameters.keys())
