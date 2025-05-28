from typing import cast

from kirin import types
from kirin.analysis import TypeInference
from kirin.dialects import ilist, py
from kirin.interp import Frame, MethodTable, impl

from ._dialect import dialect
from .stmts import New
from .types import Grid, GridType


@dialect.register(key="typeinfer")
class TypeInferMethods(MethodTable):

    @classmethod
    def get_len(cls, typ: types.TypeAttribute):
        if (typ := cast(types.Generic, typ)).is_subseteq(
            ilist.IListType
        ) and isinstance(typ.vars[1], types.Literal):
            # assume typ is Generic since it must be if it passes the first check
            # and the second check is to ensure that the length is a literal
            return types.Literal(typ.vars[1].data + 1)

        return types.Any

    @impl(New)
    def inter_new(self, _: TypeInference, frame: Frame[types.TypeAttribute], node: New):
        x_len = self.get_len(frame.get(node.x_spacing))
        y_len = self.get_len(frame.get(node.y_spacing))

        return (GridType[x_len, y_len],)

    @classmethod
    def get_literal_value(cls, typ: types.TypeAttribute):
        return cast(int, typ.data) if isinstance(typ, types.Literal) else None

    @classmethod
    def infer_new_grid_size(
        cls, index_size: types.TypeAttribute, index_type: types.TypeAttribute
    ):
        if index_type.is_subseteq(types.Int):
            return types.Literal(1)

        index_type = cast(types.Generic, index_type)

        if index_type.is_subseteq(types.Slice[types.Int]):
            if (stop := cls.get_literal_value(index_type.vars[0])) is not None:
                return types.Literal(stop)

            return index_size
        elif index_type.is_subseteq(types.Slice3[types.Int, types.Int, types.Int]):
            if (size := cls.get_literal_value(index_size)) is None:
                return types.Any  # not error but we can't infer the size

            start = cls.get_literal_value(index_type.vars[0])
            stop = cls.get_literal_value(index_type.vars[1])
            step = cls.get_literal_value(index_type.vars[2])

            sequence = range(size)  # just use a range to infer the length
            return types.Literal(len(sequence[start:stop:step]))
        elif index_type.is_subseteq(ilist.IListType):
            return index_type.vars[1]
        else:
            # unrecognized index type, return bottom to indicate an error
            return types.Bottom

    @impl(py.indexing.GetItem, types.PyClass(Grid))
    def infer_getitem(
        self,
        interp: TypeInference,
        frame: Frame[types.TypeAttribute],
        stmt: py.indexing.GetItem,
    ):
        index = frame.get(stmt.index)

        if not (index := cast(types.Generic, index)).is_subseteq(
            types.Tuple[types.Any, types.Any]
        ):
            return (types.Bottom,)

        x_index, y_index = index.vars

        obj = frame.get_casted(
            stmt.obj,
            types.Generic,
        )
        x_size = obj.vars[0]
        y_size = obj.vars[1]

        x_len = self.infer_new_grid_size(x_size, x_index)
        y_len = self.infer_new_grid_size(y_size, y_index)

        if x_len.is_equal(types.Bottom) or y_len.is_equal(types.Bottom):
            return (types.Bottom,)

        return (GridType[x_len, y_len],)
