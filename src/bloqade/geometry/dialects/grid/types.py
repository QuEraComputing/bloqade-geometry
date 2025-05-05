import dataclasses
from functools import cached_property
from itertools import chain
from typing import Any, Generic, Sequence, TypeVar

from kirin import ir, types
from kirin.dialects import ilist
from kirin.print.printer import Printer

NumX = TypeVar("NumX")
NumY = TypeVar("NumY")


@dataclasses.dataclass
class Grid(ir.Data["Grid"], Generic[NumX, NumY]):
    x_spacing: tuple[float, ...]
    y_spacing: tuple[float, ...]
    x_init: float | None
    y_init: float | None

    def __post_init__(self):
        assert all(ele >= 0 for ele in self.x_spacing)
        assert all(ele >= 0 for ele in self.y_spacing)
        self.type = types.Generic(
            Grid,
            types.Literal(len(self.x_spacing) + 1),
            types.Literal(len(self.y_spacing) + 1),
        )

    def __repr__(self):
        return (
            f"Grid({self.x_spacing!r}, "
            f"{self.y_spacing!r}, "
            f"{self.x_init!r}, {self.y_init!r})"
        )

    def is_equal(self, other: Any) -> bool:
        if not isinstance(other, Grid):
            return False
        return (
            self.x_spacing == other.x_spacing
            and self.y_spacing == other.y_spacing
            and self.x_init == other.x_init
            and self.y_init == other.y_init
        )

    @classmethod
    def from_positions(
        cls,
        x_positions: Sequence[float],
        y_positions: Sequence[float],
    ):
        x_init = x_positions[0] if len(x_positions) > 0 else None
        y_init = y_positions[0] if len(y_positions) > 0 else None

        if len(x_positions) > 1:
            x_spacing = tuple(
                x_positions[i + 1] - x_positions[i] for i in range(len(x_positions) - 1)
            )
        else:
            x_spacing = ()

        if len(y_positions) > 1:
            y_spacing = tuple(
                y_positions[i + 1] - y_positions[i] for i in range(len(y_positions) - 1)
            )
        else:
            y_spacing = ()

        return cls(x_spacing, y_spacing, x_init, y_init)

    @cached_property
    def shape(self) -> tuple[int, int]:
        num_x = 0 if self.x_init is None else len(self.x_spacing) + 1
        num_y = 0 if self.y_init is None else len(self.y_spacing) + 1
        return (num_x, num_y)

    @cached_property
    def width(self):
        return sum(self.x_spacing)

    @cached_property
    def height(self):
        return sum(self.y_spacing)

    def x_bounds(self):
        if self.x_init is None:
            return (None, None)

        return (self.x_init, self.x_init + self.width)

    def y_bounds(self):
        if self.y_init is None:
            return (None, None)

        return (self.y_init, self.y_init + self.height)

    @cached_property
    def x_positions(self) -> tuple[float, ...]:
        if self.x_init is None:
            return ()
        return tuple(
            chain(
                [pos := self.x_init],
                (pos := pos + spacing for spacing in self.x_spacing),
            )
        )

    @cached_property
    def y_positions(self) -> tuple[float, ...]:
        if self.y_init is None:
            return ()

        return tuple(
            chain(
                [pos := self.y_init],
                (pos := pos + spacing for spacing in self.y_spacing),
            )
        )

    def get(self, idx: tuple[int, int]) -> tuple[float, float]:
        return (self.x_positions[idx[0]], self.y_positions[idx[1]])

    def get_view(
        self, x_indices: ilist.IList[int, Any], y_indices: ilist.IList[int, Any]
    ):
        return SubGrid(parent=self, x_indices=x_indices, y_indices=y_indices)

    def __hash__(self) -> int:
        return id(self)

    def print_impl(self, printer: Printer) -> None:
        printer.plain_print("Grid(")
        printer.print(self.x_spacing)
        printer.plain_print(", ")
        printer.print(self.y_spacing)
        printer.plain_print(", ")
        printer.print(self.x_init)
        printer.plain_print(", ")
        printer.print(self.y_init)
        printer.plain_print(")")

    def unwrap(self):
        return self

    def scale(self, x_scale: float, y_scale: float) -> "Grid[NumX, NumY]":
        return Grid(
            x_spacing=tuple(spacing * x_scale for spacing in self.x_spacing),
            y_spacing=tuple(spacing * y_scale for spacing in self.y_spacing),
            x_init=self.x_init,
            y_init=self.y_init,
        )

    def set_init(
        self, x_init: float | None, y_init: float | None
    ) -> "Grid[NumX, NumY]":
        return Grid(self.x_spacing, self.y_spacing, x_init, y_init)

    def shift(self, x_shift: float, y_shift: float) -> "Grid[NumX, NumY]":
        return Grid(
            x_spacing=self.x_spacing,
            y_spacing=self.y_spacing,
            x_init=self.x_init + x_shift if self.x_init is not None else None,
            y_init=self.y_init + y_shift if self.y_init is not None else None,
        )

    def repeat(
        self, x_times: int, y_times: int, x_gap: float, y_gap: float
    ) -> "Grid[NumX, NumY]":

        if x_times < 1 or y_times < 1:
            raise ValueError("x_times and y_times must be non-negative")

        return Grid(
            x_spacing=sum((self.x_spacing + (x_gap,) for _ in range(x_times - 1)), ())
            + self.x_spacing,
            y_spacing=sum((self.y_spacing + (y_gap,) for _ in range(y_times - 1)), ())
            + self.y_spacing,
            x_init=self.x_init,
            y_init=self.y_init,
        )


@dataclasses.dataclass
class SubGrid(Grid[NumX, NumY]):
    x_spacing: tuple[float, ...] = dataclasses.field(init=False)
    y_spacing: tuple[float, ...] = dataclasses.field(init=False)
    x_init: float | None = dataclasses.field(init=False)
    y_init: float | None = dataclasses.field(init=False)

    parent: Grid[Any, Any]
    x_indices: ilist.IList[int, NumX]
    y_indices: ilist.IList[int, NumY]

    def __post_init__(self):
        if len(self.x_indices) == 0 or len(self.y_indices) == 0:
            raise ValueError("Indices cannot be empty")

        self.x_spacing = tuple(
            sum(self.parent.x_spacing[start:end])
            for start, end in zip(self.x_indices[:-1], self.x_indices[1:])
        )

        self.y_spacing = tuple(
            sum(self.parent.y_spacing[start:end])
            for start, end in zip(self.y_indices[:-1], self.y_indices[1:])
        )
        if self.parent.x_init is not None:
            self.x_init = self.parent.x_init + sum(
                self.parent.x_spacing[: self.x_indices[0]]
            )
        else:
            self.x_init = None

        if self.parent.y_init is not None:
            self.y_init = self.parent.y_init + sum(
                self.parent.y_spacing[: self.y_indices[0]]
            )
        else:
            self.y_init = None

        self.type = types.Generic(
            SubGrid,
            types.Literal(len(self.x_indices)),
            types.Literal(len(self.y_indices)),
        )

    def get_view(
        self, x_indices: ilist.IList[int, Any], y_indices: ilist.IList[int, Any]
    ):
        return self.parent.get_view(
            x_indices=ilist.IList([self.x_indices[x_index] for x_index in x_indices]),
            y_indices=ilist.IList([self.y_indices[y_index] for y_index in y_indices]),
        )

    def __hash__(self):
        return id(self)

    def __repr__(self):
        return super().__repr__()


GridType = types.Generic(Grid, types.TypeVar("NumX"), types.TypeVar("NumY"))
