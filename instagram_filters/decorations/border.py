from decoration import Decoration


class Border(Decoration):

    def border(self, color = 'black', width = 20):
        self._filter.add_filter_step(
            process_step_cmd="-bordercolor {color} -border {bwidth}x{bwidth}",
            color = color,
            bwidth = width
        )