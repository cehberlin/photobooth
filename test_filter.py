from instagram_filters.filters import Nashville, Toaster, BlackAndWhite
from timeit import default_timer as timer

start = timer()

filter = Nashville(filename='tmp/dummy_snap.jpg', output_filename='/tmp/dummy_snap_nashville_filtered.jpg')
# this is for comparision with the original  instagram_filters library
#filter = Nashville(filename='dsc_2017.jpg')
filter.apply()
filter = Toaster(filename='tmp/dummy_snap.jpg', output_filename='/tmp/dummy_snap_toaster_filtered.jpg')
filter.apply()
filter = BlackAndWhite(filename='tmp/dummy_snap.jpg', output_filename='/tmp/dummy_snap_bw_filtered.jpg')
filter.apply()

end = timer()
print(end - start)