from instagram_filters.filter import Filter


class BlackAndWhite(Filter):

    def _filter_callback(self):
        self.add_filter_step(process_step_cmd="-separate -poly '0.25,1, 0.5,1, 0.25,1' -sigmoidal-contrast 5,50%")
