from __future__ import annotations
import copy
from dataclasses import dataclass, field
from typing import Dict, List

from maya import cmds

from maya_playblast.helpers.logger import log


@dataclass
class ViewportFlag:
    name: str
    value: bool = False
    keep_visible: bool = False

    @property
    def as_dict(self) -> Dict[str, bool]:
        return {self.name: self.value}


@dataclass
class ViewportFlags:
    flags: List[ViewportFlag] = field(default_factory=list)
    _index: Dict[str, ViewportFlag] = field(default_factory=dict, init=False, repr=False)

    def __iter__(self):
        return iter(self.flags)
    
    def __post_init__(self):
        self._index = {f.name: f for f in self.flags}
    
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
                current = cmds.modelEditor(panel, query=True, **{flag.name: True})
                result.append(ViewportFlag(flag.name, current, flag.keep_visible))
            except Exception as e:
                print(f"Error getting state of {flag.name}", e)

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


def disable_viewport_state(panel: str):
    filtered = [ViewportFlag(f.name, f.keep_visible, f.keep_visible) for f in VIEWPORT_FLAGS]
    set_viewport_state(panel, filtered)


def set_viewport_state(panel: str, states: List[ViewportFlag]):
    for state in states:
        try:
            cmds.modelEditor(panel, edit=True, **state.as_dict)
        except Exception as e:
            log.error(f"Error on set flag {state.name} !\n\t{e}")
