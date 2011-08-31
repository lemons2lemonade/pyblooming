"""
This module implements a scalable bloom filter
based on our static bloom filters.
"""
# Try to import the C version, fallback to Python
try:
    import cbitmap as bitmaplib
except ImportError:
    import bitmap as bitmaplib
try:
    from cbloom import BloomFilter
except ImportError:
    from bloom import BloomFilter

class ScalingBloomFilter(object):
    def __init__(self, filters=None, filenames=None, length=16777216, prob=1E-6, k=4, scale_size=4, prob_reduction=0.9):
        """
        Creates a new ScalingBloomFilter that tries to enforce
        a given false positive probability by creating new Bloom Filters
        and stacking them.

        :Parameters:
            - filters (optional) : A list of filters to initialize with
            - filenames (optional) : A callable that generates file names
              for generating new persisteed BloomFilters. Without this,
              anonymous bitmaps will be used.
            - length (optional) : Length of initial filter.
            - prob (optional) : The false positive rate to enforce.
            - k (optional) : The number of hash functions to start with.
            - scale_size (optional) : The file size growth rate. Defaults to 4.
            - prob_reduction (optional) : The probability reduction with
              eahc new filter. Defaults to 0.9.
        """
        if not callable(filenames): raise ValueError, "Filenames must be callable!"
        self.filenames = filenames
        self.prob = prob
        self.init_length = length
        self.init_k = k
        self.scale_size = scale_size
        self.prob_reduction = prob_reduction
        self.filters = filters if filters else []
        self._initialize()
        if len(self.filters) == 0: self.filters.append(self._create_filter())

    def _initialize(self):
        "Initializes the probability and capacity of existing filters"
        prob = self.prob
        for filt in self.filters:
            size = len(filt.bitmap)
            filt.prob = prob
            filt.capacity = BloomFilter.expected_capacity(size, prob)
            prob *= self.prob_reduction

    def _create_filter(self):
        "Creates a new filter"
        # Get the size of the filter and k val
        length = self.init_length
        new_k = self.init_k
        prob = self.prob
        if len(self.filters) > 0:
            length = len(self.filters[-1].bitmap)/8 * self.scale_size
            new_k = self.filters[-1].k_num + 1
            prob = self.filters[-1].prob * self.prob_reduction

        # Get the filename
        filename = None
        if self.filenames:
            filename = self.filenames()

        # Create a new bitmap
        bitmap = bitmaplib.Bitmap(length, filename)
        filter = BloomFilter(bitmap, k=new_k)

        # Add the new properties
        filter.prob = prob
        filter.capacity = BloomFilter.expected_capacity(len(bitmap),prob)
        return filter

    def add(self, key, check_first=False):
        "Add a key to the set"
        if check_first and key in self: return False

        # Check if we are over capacity, create a new filter
        filt = self.filters[-1]
        if len(filt)+1 >= filt.capacity:
            filt = self._create_filter()
            self.filters.append(filt)

        # Add the key to the largest filter
        return filt.add(key)

    def __contains__(self, key):
        "Checks if the set contains a given key"
        # Walk over the indexes in reverse order
        for filt in self.filters[::-1]:
            if key in filt: return True
        return False

    def __len__(self):
        "Returns the number of elements in the bitmap"
        return sum(len(filt) for filt in self.filters)

    def flush(self):
        "Flushes all the underlying Bloom filters"
        for filt in self.filters:
            filt.flush()

    def close(self):
        "Clses all the underlying bloom filters"
        for filt in self.filters:
            filt.close()

    def total_capacity(self):
        "Returns the total capacity"
        return sum(filt.capacity for filt in self.filters)

    def total_bitmap_size(self):
        "Returns the total size of the bitmaps in bytes"
        return sum(len(filt.bitmap) for filt in self.filters) / 8

