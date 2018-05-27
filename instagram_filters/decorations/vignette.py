
from decoration import Decoration
import math


class Vignette(Decoration):

    def __init__(self, color_1 = 'none', color_2 = 'black', crop_factor = 1.5):
        self.color_1 = color_1
        self.color_2 = color_2
        self.crop_factor = crop_factor

    def apply(self, filter):

        width = filter.default_params['width']
        height = filter.default_params['height']
        crop_x = math.floor(width * self.crop_factor)
        crop_y = math.floor(height * self.crop_factor)

        filter.add_filter_step(
            process_step_cmd="\( -size {crop_x}x{crop_y} radial-gradient:{color_1}-{color_2} -gravity center -crop {width}x{height}+0+0 +repage \) -compose multiply -flatten",
            crop_x=crop_x,
            crop_y=crop_y,
            color_1=self.color_1,
            color_2=self.color_2,
        )