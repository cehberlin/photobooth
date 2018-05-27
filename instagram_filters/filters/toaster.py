from instagram_filters.filter import Filter
from instagram_filters.decorations import Vignette, Border


class Toaster(Filter):

    def _filter_callback(self):
        self.colortone('#330000', 50, 0)
        self.add_filter_step(process_step_cmd="-modulate 150,80,100 -gamma 1.2 -contrast -contrast")

        Vignette('none', 'LavenderBlush3',crop_factor=1.6).apply(filter=self)
        Vignette('#ff9966', 'none',crop_factor=1.6).apply(filter=self)

        #Border('white').apply(filter=self)
