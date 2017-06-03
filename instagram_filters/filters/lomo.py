from instagram_filters.filter import Filter
from instagram_filters.decorations import Vignette

class Lomo(Filter):

    def _filter_callback(self):
        self.add_filter_step(process_step_cmd="-channel R -level 33% -channel G -level 33%")
        Vignette(filter=self).vignette()