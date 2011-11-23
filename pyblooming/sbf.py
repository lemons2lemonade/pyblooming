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
    def __init__(self, filters=None, filenames=None, initial_capacity=1e6, prob=1e-4, scale_size=4, prob_reduction=0.9):
        """
        Creates a new ScalingBloomFilter that tries to enforce
        a given false positive probability by creating new Bloom Filters
        and stacking them.

        :Parameters:
            - filters (optional) : A list of filters to initialize with
            - filenames (optional) : A callable that generates file names
              for generating new persisteed BloomFilters. Without this,
              anonymous bitmaps will be used.
            - initial_capacity (optional) : Initial capacity.
            - prob (optional) : The false positive rate to enforce.
            - scale_size (optional) : The file size growth rate. Defaults to 4.
            - prob_reduction (optional) : The probability reduction with
              each new filter. Defaults to 0.9.
        """
        if filenames is not None and not callable(filenames): raise ValueError, "Filenames must be callable!"
        self.filenames = filenames
        self.prob = prob
        self.init_capacity = initial_capacity
        self.scale_size = scale_size
        self.prob_reduction = prob_reduction
        self.filters = filters if filters else []
        self._initialize()
        if len(self.filters) == 0: self.filters.append(self._create_filter())

    def _initialize(self):
        "Initializes the probability and capacity of existing filters"
        prob = self.prob
        for filt in self.filters:
            size = len(filt.bitmap) - 8*filt.extra_buffer()
            filt.info["prob"] = prob
            filt.info["capacity"] = int(BloomFilter.expected_capacity(size, prob))
            prob *= self.prob_reduction

    def _create_filter(self):
        "Creates a new filter"
        # Get the initial parameters
        capacity, prob = self.init_capacity, self.prob

        # Update our parameters if we have filters
        if len(self.filters) > 0:
            # Grow by the scale size
            capacity = self.filters[-1].info["capacity"] * self.scale_size

            # Reduce the probability by the probability reduction
            prob = self.filters[-1].info["prob"] * self.prob_reduction

        # Get the filename
        filename = None
        if self.filenames:
            filename = self.filenames()

        # Compute the new size and K
        length, k = BloomFilter.params_for_capacity(capacity, prob)

        # Create a new bitmap
        bitmap = bitmaplib.Bitmap(length, filename)
        filter = BloomFilter(bitmap, k)

        # Add the new properties
        filter.info["prob"] = prob
        filter.info["capacity"] = capacity
        return filter

    def add(self, key, check_first=False):
        "Add a key to the set"
        if check_first and key in self: return False

        # Check if we are over capacity, create a new filter
        filt = self.filters[-1]
        if len(filt)+1 >= filt.info["capacity"]:
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
        return sum(filt.info["capacity"] for filt in self.filters)

    def total_bitmap_size(self):
        "Returns the total size of the bitmaps in bytes"
        return sum(len(filt.bitmap) for filt in self.filters) / 8

