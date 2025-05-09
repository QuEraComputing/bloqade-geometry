from kirin import types
from kirin.analysis import TypeInference
from kirin.interp import Frame, MethodTable, impl

from ._dialect import dialect
from .stmts import New
from .types import GridType


@dialect.register(key="typeinfer")
class TypeInferMethods(MethodTable):

    def get_len(self, typ: types.TypeAttribute):
        if isinstance(typ, types.Generic) and isinstance(typ.vars[1], types.Literal):
            return types.Literal(typ.vars[1].data + 1)
        else:
            return types.Any

    @impl(New)
    def inter_new(
        self, interp_: TypeInference, frame: Frame[types.TypeAttribute], node: New
    ):
        x_spacing_type = frame.get(node.x_spacing)
        y_spacing_type = frame.get(node.y_spacing)

        x_len = self.get_len(x_spacing_type)
        y_len = self.get_len(y_spacing_type)

        return (GridType[x_len, y_len],)
