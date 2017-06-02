from instagram_filters.filter import Filter


class Nashville(Filter):
	
	def apply(self):
		self.colortone('#222b6d', 50, 0);
		self.colortone('#f7daae', 120, 1);
		#self.execute("convert {0} -contrast -modulate 100,150,100 -auto-gamma {0}".format(r'"{filename}"'));
		#self.frame("Nashville.jpg");
		super(Nashville, self).apply()
		
