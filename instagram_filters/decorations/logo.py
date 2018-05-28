from decoration import Decoration

class Logo(Decoration):

    def __init__(self, logo_path):
        self.logo_path = logo_path

    def apply(self, filter):

        filter.add_filter_step(
            process_step_cmd="'{logo}' -gravity NorthEast -geometry +200+150 -composite",
            logo=self.logo_path
        )


