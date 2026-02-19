from maya import cmds, OpenMaya as om


def create_image() -> om.MImage:
    return om.MImage()

def current_time(current) -> int:
    return cmds.currentTime(current)


def get_animation_end() -> int:
    return int(cmds.playbackOptions(query=True, animationEndTime=True))


def get_animation_start() -> int:
    return int(cmds.playbackOptions(query=True, animationStartTime=True))


def get_frame_rate() -> int:
    return int(om.MTime(1.0, om.MTime.kSeconds).asUnits(om.MTime.uiUnit()))
