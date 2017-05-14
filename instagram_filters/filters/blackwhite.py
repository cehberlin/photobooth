from instagram_filters.filter import Filter
from instagram_filters.decorations import Border

class BlackAndWhite(Filter, Border):
	
	def apply(self):
		self.execute('convert {filename} -separate -poly "0.25,1, 0.5,1, 0.25,1" {filename}')
