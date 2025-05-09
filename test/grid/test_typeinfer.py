from kirin import types

from bloqade.geometry.dialects import grid
from bloqade.geometry.prelude import geometry


def test_typeinfer():

    @geometry
    def test_method():
        return grid.New([1, 2], [1, 2], 0, 0)

    test_method.return_type.is_equal(grid.GridType[types.Literal(3), types.Literal(3)])


if __name__ == "__main__":
    test_typeinfer()
