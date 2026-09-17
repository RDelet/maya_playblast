from __future__ import annotations

import copy
from dataclasses import dataclass, field

from maya import cmds

from ..core.logger import log


@dataclass
class ViewportFlag:
    name: str
    value: bool = False
    keep_visible: bool = False

    @property
    def as_dict(self) -> dict[str, bool]:
        return {self.name: self.value}

    def viewport_state(self, panel: str) -> bool:
        return cmds.modelEditor(panel, query=True, **{self.name: True})


@dataclass
class ViewportFlags:
    flags: list[ViewportFlag] = field(default_factory=list)
    _index: dict[str, ViewportFlag] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self):
        self._index = {flag.name: flag for flag in self.flags}

    def get(self, name: str) -> ViewportFlag:
        if name not in self._index:
            raise ValueError(f"Viewport flag '{name}' not found")
        return self._index[name]

    def set(self, name: str, value: bool):
        flag = self.get(name)
        flag.value = value

    def copy(self) -> ViewportFlags:
        new_flags = copy.deepcopy(self.flags)
        return ViewportFlags(flags=new_flags)

    def snapshot(self, panel: str) -> ViewportFlags:
        result = []
        for flag in self.flags:
            try:
                result.append(ViewportFlag(flag.name, flag.viewport_state(panel), flag.keep_visible))
            except Exception as e:
                log.error(f"Error getting state of {flag.name} !", e)

        return ViewportFlags(flags=result)


VIEWPORT_FLAGS = ViewportFlags(flags=[
    ViewportFlag("cameras"),
    ViewportFlag("clipGhosts"),
    ViewportFlag("controlVertices"),
    ViewportFlag("deformers"),
    ViewportFlag("dimensions"),
    ViewportFlag("dynamicConstraints"),
    ViewportFlag("dynamics"),
    ViewportFlag("fluids"),
    ViewportFlag("follicles"),
    ViewportFlag("grid"),
    ViewportFlag("hairSystems"),
    ViewportFlag("handles"),
    ViewportFlag("headsUpDisplay"),
    ViewportFlag("hulls"),
    ViewportFlag("ikHandles"),
    ViewportFlag("imagePlane"),
    ViewportFlag("joints"),
    ViewportFlag("lights"),
    ViewportFlag("locators"),
    ViewportFlag("manipulators"),
    ViewportFlag("motionTrails"),
    ViewportFlag("nCloths"),
    ViewportFlag("nParticles"),
    ViewportFlag("nRigids"),
    ViewportFlag("nurbsCurves"),
    ViewportFlag("nurbsSurfaces"),
    ViewportFlag("particleInstancers"),
    ViewportFlag("pivots"),
    ViewportFlag("planes"),
    ViewportFlag("pluginShapes"),
    ViewportFlag("polymeshes", keep_visible=True),
    ViewportFlag("shadows"),
    ViewportFlag("strokes"),
    ViewportFlag("subdivSurfaces"),
    ViewportFlag("textures"),
    ViewportFlag("transpInShadows")
])


def set_viewport_state(panel: str, state: ViewportFlag):
    try:
        cmds.modelEditor(panel, edit=True, **state.as_dict)
    except Exception as e:
        log.error(f"Error on set flag {state.name} !\n\t{e}")


def set_viewport_states(panel: str, states: list[ViewportFlag] | ViewportFlags):
    flags = states.flags if isinstance(states, ViewportFlags) else states
    for state in flags:
        set_viewport_state(panel, state)
