from kirin import ir
from kirin.serialization.base import Serializer
from kirin.serialization.jsonserializer import JSONSerializer

from bloqade.geometry import filled, grid
from bloqade.geometry.prelude import geometry

unit_serializer = Serializer()
json_serializer = JSONSerializer()


def to_json_str(program: ir.Method) -> str:
    encoded_module = unit_serializer.encode(program)
    json_str = json_serializer.encode(encoded_module)
    return json_str


def from_json_str(data: str, group: ir.DialectGroup) -> ir.Method:
    decoded_module = json_serializer.decode(data)
    program = group.decode(decoded_module)
    return program


def test_grid():
    @geometry
    def main():
        return grid.from_positions([0, 1, 2], [10, 20, 30])

    json_str = to_json_str(main)
    restored_main = from_json_str(json_str, main.dialects)
    assert restored_main.code.is_structurally_equal(main.code)


def test_subgrid():
    @geometry
    def main():
        g = grid.from_positions([0, 1, 2], [10, 20, 30])
        return g[[1, 2, 3], [20, 30]]

    json_str = to_json_str(main)
    restored_main = from_json_str(json_str, main.dialects)
    assert restored_main.code.is_structurally_equal(main.code)


def test_filled_grid():
    @geometry
    def main():
        g = grid.from_positions([0, 1, 2], [10, 20, 30])
        return filled.vacate(g, [(1, 2), (0, 1)])

    json_str = to_json_str(main)
    restored_main = from_json_str(json_str, main.dialects)
    assert restored_main.code.is_structurally_equal(main.code)
