from instagram_filters.filter import Filter
from instagram_filters.decorations import Vignette, Border

class Toaster(Filter, Vignette, Border):
	
	def apply(self):
		self.colortone('#330000', 50, 0)
		self.execute("convert {0} -modulate 150,80,100 -gamma 1.2 -contrast -contrast {0}".format(r'"{filename}"'));
		self.vignette('none', 'LavenderBlush3');
		self.vignette('#ff9966', 'none');
		#self.border('white')
