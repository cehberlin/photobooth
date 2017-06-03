from instagram_filters.filter import Filter


class Nashville(Filter):

    def apply(self):
        self.colortone('#222b6d', 50, 0)
        self.colortone('#f7daae', 120, 1)
        self.add_process_step(process_step_cmd="-contrast -modulate 100,150,100 -auto-gamma")
        #self.frame("Nashville.jpg");
        super(Nashville, self).apply()