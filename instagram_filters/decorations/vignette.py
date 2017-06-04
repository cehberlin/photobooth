
from decoration import Decoration
import math


class Vignette(Decoration):

    def vignette(self, color_1 = 'none', color_2 = 'black', crop_factor = 1.5):

        width = self._filter.default_params['width']
        height = self._filter.default_params['height']
        crop_x = math.floor(width * crop_factor)
        crop_y = math.floor(height * crop_factor)

        self._filter.add_filter_step(
            process_step_cmd="\( -size {crop_x}x{crop_y} radial-gradient:{color_1}-{color_2} -gravity center -crop {width}x{height}+0+0 +repage \) -compose multiply -flatten",
            crop_x=crop_x,
            crop_y=crop_y,
            color_1=color_1,
            color_2=color_2,
        )