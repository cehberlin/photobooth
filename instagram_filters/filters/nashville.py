from instagram_filters.filter import Filter
from instagram_filters.decorations import Frame

class Nashville(Filter):

    def _filter_callback(self):
        self.colortone('#222b6d', 50, 0)
        self.colortone('#f7daae', 120, 1)
        self.add_filter_step(process_step_cmd="-contrast -modulate 100,150,100 -auto-gamma")
        #Frame(filter=self).frame("Nashville.jpg");