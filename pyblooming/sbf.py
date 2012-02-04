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
    def __init__(self, filters=None, filenames=None, callback=None, initial_capacity=1e6, prob=1e-4, scale_size=4, prob_reduction=0.9):
        """
        Creates a new ScalingBloomFilter that tries to enforce
        a given false positive probability by creating new Bloom Filters
        and stacking them.

        :Parameters:
            - filters (optional) : A list of filters to initialize with
            - filenames (optional) : A callable that generates file names
              for generating new persisteed BloomFilters. Without this,
              anonymous bitmaps will be used.
            - callback (optional) : A callable that generates bitmaps
              for generating new persisteed BloomFilters. Without this,
              anonymous bitmaps will be used. Function must take a size parameter,
              and return bitmaps of that size. The default callback will invoke
              the filenames callback to get a filename.
            - initial_capacity (optional) : Initial capacity.
            - prob (optional) : The false positive rate to enforce.
            - scale_size (optional) : The file size growth rate. Defaults to 4.
            - prob_reduction (optional) : The probability reduction with
              each new filter. Defaults to 0.9.
        """
        if filenames is not None and not callable(filenames):
            raise ValueError("Filenames must be callable!")
        self.filenames = filenames
        if callback is not None and not callable(callback):
            raise ValueError("Callback must be callable!")
        self.callback = callback or self._callback
        self.prob = prob
        self.init_capacity = initial_capacity
        self.scale_size = scale_size
        self.prob_reduction = prob_reduction
        self.filters = filters if filters else []
        self._initialize()
        if len(self.filters) == 0:
            self.filters.append(self._create_filter())

    def _initialize(self):
        "Initializes the probability and capacity of existing filters"
        # Bound the ultimate probability by adjusting for the initial
        # From "Scalable Bloom Filters", Almeida 2007
        # We use : P <= P0 * (1 / (1 - r))
        prob = (1 - self.prob_reduction) * self.prob

        for filt in self.filters:
            size = len(filt.bitmap) - 8 * filt.extra_buffer()
            filt.info["prob"] = prob
            filt.info["capacity"] = int(BloomFilter.expected_capacity(size, prob))
            prob *= self.prob_reduction

    def _callback(self, length):
        """
        Default callback used to make bitmaps. Tries to invoke the
        filenames callback for backwards compatibility, or creates a
        new anonymous bitmap if none is provided.
        """
        # Get the filename, default to None == Anonymous
        filename = None
        if self.filenames:
            filename = self.filenames()

        # Create a new bitmap
        bitmap = bitmaplib.Bitmap(length, filename)
        return bitmap

    def _create_filter(self):
        "Creates a new filter"
        # Get the initial parameters
        capacity, prob = self.init_capacity, self.prob

        # Bound the ultimate probability by adjusting for the initial
        # From "Scalable Bloom Filters", Almeida 2007
        # We use : P <= P0 * (1 / (1 - r))
        prob = (1 - self.prob_reduction) * prob

        # Update our parameters if we have filters
        if len(self.filters) > 0:
            # Grow by the scale size
            capacity = self.filters[-1].info["capacity"] * self.scale_size

            # Reduce the probability by the probability reduction
            prob = self.filters[-1].info["prob"] * self.prob_reduction

        # Compute the new size and K
        length, k = BloomFilter.params_for_capacity(capacity, prob)

        # Invoke our callback to get a bitmap
        bitmap = self.callback(length)

        # Create a new bloom filter
        filter = BloomFilter(bitmap, k)

        # Add the new properties
        filter.info["prob"] = prob
        filter.info["capacity"] = capacity
        return filter

    def add(self, key, check_first=False):
        "Add a key to the set"
        if check_first and key in self:
            return False

        # Check if we are over capacity, create a new filter
        filt = self.filters[-1]
        if len(filt) + 1 >= filt.info["capacity"]:
            filt = self._create_filter()
            self.filters.append(filt)

        # Add the key to the largest filter
        return filt.add(key)

    def __contains__(self, key):
        "Checks if the set contains a given key"
        # Walk over the indexes in reverse order
        for filt in self.filters[::-1]:
            if key in filt:
                return True
        return False

    def __len__(self):
        "Returns the number of elements in the bitmap"
        return sum(len(filt) for filt in self.filters)

    def flush(self):
        "Flushes all the underlying Bloom filters"
        for filt in self.filters:
            filt.flush()

    def close(self, flush=True):
        "Clses all the underlying bloom filters"
        for filt in self.filters:
            filt.close(flush=flush)

    def total_capacity(self):
        "Returns the total capacity"
        return sum(filt.info["capacity"] for filt in self.filters)

    def total_bitmap_size(self):
        "Returns the total size of the bitmaps in bytes"
        return sum(len(filt.bitmap) for filt in self.filters) / 8

