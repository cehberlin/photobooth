from instagram_filters.filter import Filter
#from instagram_filters.decorations import Vignette, Border

class Toaster(Filter):
	
	def apply(self):
		self.colortone('#330000', 50, 0)
		self.add_process_step(process_step_cmd="-modulate 150,80,100 -gamma 1.2 -contrast -contrast")
		#TODO
		#self.vignette('none', 'LavenderBlush3');
		#self.vignette('#ff9966', 'none');
		#self.border('white')
		super(Toaster, self).apply()
