from instagram_filters.filter import Filter

class BlackAndWhite(Filter):
	
	def apply(self):
		self.add_process_step(process_step_cmd="-separate -poly '0.25,1, 0.5,1, 0.25,1' -level 0%,100%,0.8")
		super(BlackAndWhite, self).apply()

