from __future__ import annotations
import copy
from dataclasses import dataclass, field
from typing import Dict, List

from maya import cmds

from ..core.logger import log
from ..maya import maya_ui


@dataclass
class ViewportFlag:
    name: str
    value: bool = False
    keep_visible: bool = False

    @property
    def as_dict(self) -> Dict[str, bool]:
        return {self.name: self.value}
    
    def viewport_state(self, panel: str) -> bool:
        return cmds.modelEditor(panel, query=True, **{self.name: True})

    def viewport_states(self) -> Dict[str, bool]:
        output = {}
        for panel in maya_ui.get_panels():
            output[panel] = self.viewport_state(panel)
    
    def set_from_viewport(self, panel: str):
        self.value = self.viewport_state(panel)


@dataclass
class ViewportFlags:
    flags: List[ViewportFlag] = field(default_factory=list)
    _index: Dict[str, ViewportFlag] = field(default_factory=dict, init=False, repr=False)

    def __iter__(self):
        return iter(self.flags)
    
    def __post_init__(self):
        self._index = {f.name: f for f in self.flags}

    def __getitem__(self, name: str) -> ViewportFlag:
        return self.get(name)
    
    def __setitem__(self, name: str, value: bool):
        self.set(name, value)

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

    def snapshot(self, panel: str) -> List[ViewportFlag]:
        result = []
        for flag in self.flags:
            try:
                result.append(ViewportFlag(flag.name, flag.viewport_state(panel), flag.keep_visible))
            except Exception as e:
                log.error(f"Error getting state of {flag.name} !", e)

        return result


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
    ViewportFlag("transpInShadows"),
])


def set_viewport_state(panel: str, state: ViewportFlag):
    try:
        cmds.modelEditor(panel, edit=True, **state.as_dict)
    except Exception as e:
        log.error(f"Error on set flag {state.name} !\n\t{e}")


def set_viewport_states(panel: str, states: List[ViewportFlag] | ViewportFlags):
    for state in states:
        set_viewport_states(panel, state)
