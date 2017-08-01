from instagram_filters.filters import Nashville
from timeit import default_timer as timer

start = timer()

filter = Nashville(filename='tmp/dummy_snap.jpg', output_filename='/tmp/dummy_snap_filtered.jpg')
# this is for comparision with the original  instagram_filters library
#filter = Nashville(filename='dsc_2017.jpg')

filter.apply()
end = timer()
print(end - start)