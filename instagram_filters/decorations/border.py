from decoration import Decoration


class Border(Decoration):

    def __init__(self, color = 'black', width = 20):
        self.color = color
        self.width = width

    def apply(self, filter):
        filter.add_filter_step(
            process_step_cmd="-bordercolor {color} -border {bwidth}x{bwidth}",
            color=self.color,
            bwidth=self.width
        )