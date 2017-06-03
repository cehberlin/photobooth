from instagram_filters.filter import Filter
from instagram_filters.decorations import Frame

class Kelvin(Filter):

    def _filter_callback(self):
        self.add_filter_step(
            process_step_cmd="-auto-gamma -modulate 120,50,100 \) \( -size {width}x{height} -fill 'rgba(255,153,0,0.5)' -draw 'rectangle 0,0 {width},{height}' \) -compose multiply")
        #Frame(filter=self).frame("Kelvin.jpg");