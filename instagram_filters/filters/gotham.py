from instagram_filters.filter import Filter
from instagram_filters.decorations import Border

class Gotham(Filter):
	
	def _filter_callback(self):
		self.add_filter_step(process_step_cmd="-modulate 120,10,100 -fill '#222b6d' -colorize 20 -gamma 0.5 -contrast")
		#Border(self).border()