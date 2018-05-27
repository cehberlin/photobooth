from decoration import Decoration

import os, inspect


class Frame(Decoration):

    def __init__(self, frame):
        self.frame = frame

    def apply(self, filter):
        path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        filter.add_filter_step(
            process_step_cmd="\( '{frame}' -resize {width}x{width}! -unsharp 1.5x1.0+1.5+0.02 \) -flatten",
            frame = os.path.join(path, "frames", self.frame)
        )