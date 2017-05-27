from instagram_filters.filter import Filter
from instagram_filters.decorations import Border

class Gotham(Filter, Border):
	
	def apply(self):
		self.execute("convert {0} -modulate 120,10,100 -fill '#222b6d' -colorize 20 -gamma 0.5 -contrast {0}".format(r'"{filename}"'))
		#self.border()
