from instagram_filters.filter import Filter
#from instagram_filters.decorations import Vignette

class Lomo(Filter):
	
	def apply(self):
		self.add_process_step(process_step_cmd="-channel R -level 33% -channel G -level 33%")
		#TODO
		#self.vignette()
		super(Lomo, self).apply()
