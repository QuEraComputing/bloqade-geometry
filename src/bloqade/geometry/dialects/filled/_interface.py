from typing import Any, TypeVar

from kirin.dialects import ilist
from kirin.lowering import wraps as _wraps

from bloqade.geometry.dialects import grid

from .stmts import Fill, GetParent, Vacate
from .types import FilledGrid

Nx = TypeVar("Nx")
Ny = TypeVar("Ny")


@_wraps(Vacate)
def vacate(
    zone: grid.Grid[Nx, Ny],
    vacancies: ilist.IList[tuple[int, int], Any],
) -> FilledGrid[Nx, Ny]: ...


@_wraps(Fill)
def fill(
    zone: grid.Grid[Nx, Ny],
    filled: ilist.IList[tuple[int, int], Any],
) -> FilledGrid[Nx, Ny]: ...


@_wraps(GetParent)
def get_parent(filled_grid: FilledGrid[Nx, Ny]) -> grid.Grid[Nx, Ny]: ...
