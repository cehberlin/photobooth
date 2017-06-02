from instagram_filters.filter import Filter
#from instagram_filters.decorations import Border

class Gotham(Filter):
	
	def apply(self):
		self.add_process_step(process_step_cmd="-modulate 120,10,100 -fill '#222b6d' -colorize 20 -gamma 0.5 -contrast")
		# self.border()
		super(Gotham, self).apply()
