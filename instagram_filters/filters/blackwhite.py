from instagram_filters.filter import Filter
from instagram_filters.decorations import Border

class BlackAndWhite(Filter, Border):
	
	def apply(self):
		self.execute("convert {0} -separate -poly '0.25,1, 0.5,1, 0.25,1' -level 0%,100%,0.8 {0}".format(r'"{filename}"'))

