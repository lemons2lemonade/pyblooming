"""
Implements an easy to use Bloom filter on top of
the bitmap implementation.
"""
import operator
import math
import struct
import bitmap as bitmaplib

class BloomFilter(object):
    # This is the packing format we use to store the count
    SIZE_FMT = "<Q"
    K_NUM_FMT = "<I"

    # This is how many bytes we need to store the count
    SIZE_LEN = 8
    K_NUM_LEN = 4

    def __init__(self, bitmap=None, length=16777216, k=4):
        """
        Creates a new Bloom Filter instance. A bloom filter
        requires a bitmap underneath, which can either be
        provided or created. If a bitmap is not provided, then
        an anonymous bitmap is created and used. The anonymous
        bitmap defaults to 16M but that can be changed.

        :Parameters:
          - bitmap (optional) : The bitmap that should be used.
            An anonymous bitmap will be created if one is not
            provided.
          - length (optional) : The size of the anonymous bitmap
            in bytes to create. Defaults to 16M. Must be at least
            large enough to store the count, which means at least
            SIZE_LEN bytes (8).
          - k (optional) : The number of hashing algorithms to
            use. Must be at least 1.
        """
        if k < 1:
            raise ValueError, "Bad value provided for k!"

        if not bitmap:
            bitmap = bitmaplib.Bitmap(length+self.SIZE_LEN+self.K_NUM_LEN)

        self.bitmap = bitmap
        self.bitmap_size = len(bitmap) - 8*(self.SIZE_LEN+self.K_NUM_LEN) # Ignore our size

        # Restore the k num if we need to
        self.k_num = self._read_k_num() # Read the existing knum from the file
        if self.k_num == 0:
            self.k_num = k
            self._write_k_num()

        # Restore the count
        self.count = self._read_count() # Read the count from the file

    @classmethod
    def required_bits(cls, capacity, prob):
        """
        Returns the number of bits required to achieve
        the desired false positive probability with a given
        capacity.
        """
        raw = -capacity*math.log(prob)/(math.log(2)**2)
        return int(math.ceil(raw))

    @classmethod
    def required_bytes(cls, capacity, prob):
        "Returns the same as required_bits, but in bytes."
        return int(math.ceil(cls.required_bits(capacity, prob) / 8.0))

    @classmethod
    def expected_probability(cls, bits, capacity):
        """
        Returns the expected probability of false positives
        given a capacity and bit count.
        """
        return math.e ** (-(float(bits)/float(capacity))*(math.log(2)**2))

    @classmethod
    def expected_capacity(cls, bits, prob):
        """
        Returns the expected capacity given a number
        of bits and an enforced probability
        """
        return -bits/math.log(prob)*(math.log(2)**2)

    def _get_hashes(self, key, k):
        "Generates a specified number of hashes for a key"
        hashes = []
        salt = ""
        while len(hashes) < k:
            # Get a set of new hashes
            new_hashes = self._hash(key, salt)
            hashes.extend(new_hashes)

            # Generate a new salt
            salt_raw = reduce(operator.xor, new_hashes) % 9223372036854775808L
            salt = struct.pack("<q", salt_raw)
        return hashes[:k]

    def _hash(self, key, salt=""):
        "Computes and returns the DJB, DEK, FNV, and JS hashes"
        if salt: key = salt + key
        djb_hash = 5381
        dek_hash = len(key)
        fnv_prime = 0x811C9DC5
        fnv_hash = 0
        js_hash = 1315423911

        for elem in key:
            key_val = ord(elem)
            djb_hash = ((djb_hash << 5) + djb_hash) + key_val
            dek_hash = ((dek_hash << 6) ^ (dek_hash >> 27)) ^ key_val
            fnv_hash *= fnv_prime
            fnv_hash ^= key_val
            js_hash ^= ((js_hash << 5) + key_val + (js_hash >> 2))

        return (djb_hash, dek_hash, fnv_hash, js_hash)

    def add(self, key, check_first=False):
        "Add a key to the set"
        hashes = self._get_hashes(key, self.k_num)
        m = self.bitmap_size

        # Set the bits for the hashes
        for h in hashes:
            if check_first and self.bitmap[h % m] == 0: return False
            self.bitmap[h % m] = 1
        self.count += 1

        return True

    def __contains__(self, key):
        "Checks if the set contains a given key"
        hashes = self._get_hashes(key, self.k_num)
        m = self.bitmap_size
        for h in hashes:
            if self.bitmap[h % m] == 0: return False
        return True

    def __or__(self, bloom):
        "Implements a set union"
        if not isinstance(bloom, BloomFilter): raise ValueError, "Cannot perform union with non-BloomFilter!"
        bitmap = self.bitmap | bloom.bitmap
        new = BloomFilter(bitmap=bitmap,k=self.k_num)
        new.count = self.count + bloom.count # Sum the counts, as an approximation
        new.flush(size_only=True) # Resave the size, otherwise it is garbage
        return new

    def __and__(self, bloom):
        "Implements a set intersection"
        if not isinstance(bloom, BloomFilter): raise ValueError, "Cannot perform intersection with non-BloomFilter!"
        bitmap = self.bitmap & bloom.bitmap
        new = BloomFilter(bitmap=bitmap,k=self.k_num)
        new.count = min(self.count, bloom.count) # Use the minimum count, as an approximation
        new.flush(size_only=True) # Resave the size, otherwise it is garbage
        return new

    def __len__(self):
        "Returns the number of elements in the bitmap"
        return self.count

    def flush(self, size_only=False):
        """
        Forces us to write out the current count to the bitmap,
        and flushes the underlying bitmap.
        """
        # Get the count string
        count_str = struct.pack(self.SIZE_FMT, self.count)

        # Set the count as the last bytes
        size_offset = self.bitmap_size / 8
        self.bitmap[size_offset:size_offset+self.SIZE_LEN] = count_str

        # Flush the underlying bitmap
        if not size_only: self.bitmap.flush()

    def close(self):
        "Closes the bloom filter and the underlying bitmap"
        if self.bitmap:
            self.flush()
            self.bitmap.close()

    def _read_count(self):
        "Reads the count from the bitmap"
        # Set the count as the last bytes
        size_offset = self.bitmap_size / 8
        count_str = self.bitmap[size_offset:size_offset+self.SIZE_LEN]

        # Unpack
        unpacked = struct.unpack(self.SIZE_FMT, count_str)
        return unpacked[0]

    def _read_k_num(self):
        "Reads the k-num we should use"
        size_offset = self.bitmap_size / 8 + self.SIZE_LEN
        knum_str = self.bitmap[size_offset:size_offset+self.K_NUM_LEN]
        unpacked = struct.unpack(self.K_NUM_FMT, knum_str)
        return unpacked[0]

    def _write_k_num(self):
        "Writes the k-num we should use"
        size_offset = self.bitmap_size / 8 + self.SIZE_LEN
        knum_str = struct.pack(self.K_NUM_FMT, self.k_num)
        self.bitmap[size_offset:size_offset+self.K_NUM_LEN] = knum_str
        self.bitmap.flush()


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

