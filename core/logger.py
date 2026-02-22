from __future__ import annotations

import logging


log = logging.getLogger("Playblast")
log.setLevel(logging.DEBUG)

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("[%(levelname)s] %(filename)s::%(funcName)s:%(lineno)d — %(message)s"))
log.addHandler(handler)
