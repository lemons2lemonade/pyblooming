"""
Implements an easy to use Bloom filter on top of
the bitmap implementation.
"""
from libc cimport stdlib
import operator
import math
import struct
import cbitmap as bitmaplib
cimport cython

cdef class BloomFilter:
    # This is the packing format we use to store the count
    SIZE_FMT = "<Q"
    K_NUM_FMT = "<I"

    # This is how many bytes we need to store the count
    SIZE_LEN = 8
    K_NUM_LEN = 4

    cdef public object info
    cdef public object bitmap
    cdef readonly unsigned int k_num
    cdef size_t bitmap_size
    cdef size_t count
    cdef size_t* hashes
    cdef readonly size_t offset

    def __cinit__(self, bitmap, k):
        """
        Creates a new Bloom Filter instance. A bloom filter
        requires a bitmap underneath.

        :Parameters:
          - bitmap : The bitmap that should be used. Must be large enough to
            store the additional meta data. extra_buffers() should be used to
            determine the amount of additional padding.
          - k : The number of hashing algorithms to
            use. Must be at least 1.
        """
        if bitmap is None or k is None: raise ValueError, "Must provide bitmap and k!"
        if k < 1: raise ValueError, "Bad value provided for k!"
        self.bitmap = bitmap
        self.bitmap_size = len(bitmap) - 8*self.extra_buffer() # Ignore our size
        if self.bitmap_size <= 0: raise ValueError, "Bitmap is not large enough!"

        # Restore the k num if we need to
        self.k_num = self._read_k_num() # Read the existing knum from the file
        if self.k_num == 0:
            self.k_num = k
            self._write_k_num()
    
        # Store a buffer for our hashes
        self.hashes = <size_t*>stdlib.malloc(self.k_num*8*sizeof(size_t))

        # Compute the offset size
        self.offset = self.bitmap_size / self.k_num

        # Restore the count
        self.count = self._read_count() # Read the count from the file
        self.info = {} # Allows dynamic properties

    def __dealloc__(self):
        "Cleanup"
        stdlib.free(self.hashes)

    @classmethod
    def extra_buffer(cls):
        """
        Returns the extra bytes we need for our buffer info.
        """
        return cls.SIZE_LEN + cls.K_NUM_LEN

    @classmethod
    def for_capacity(cls, capacity, probability):
        """
        Creates a new bloom filter that computes the
        size required for the given capacity and probability,
        and sets the ideal K. Uses an anonymous bitmap.
        """
        bytes, ideal_k = cls.params_for_capacity(capacity, probability)
        bitmap = bitmaplib.Bitmap(bytes)
        return BloomFilter(bitmap, ideal_k)

    @classmethod
    def params_for_capacity(cls, capacity, probability):
        """
        Returns the number of bytes and ideal K value that
        should be used to create a Bloom Filter for the given
        capacity and probability.
        """
        # Get the number of bytes and bits
        bytes = cls.required_bytes(capacity, probability)
        bits = bytes*8 # The bytes may round up, so get the bits again
        ideal_k = cls.ideal_k(bits, capacity)
        ideal_k = int(math.ceil(ideal_k))
        return bytes+cls.extra_buffer(), ideal_k

    @classmethod
    def required_bits(cls, capacity, prob):
        """
        Returns the number of bits required to achieve
        the desired false positive probability with a given
        capacity. Assumes optimal K.
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
        given a capacity and bit count. Assumes optimal K.
        """
        return math.e ** (-(float(bits)/float(capacity))*(math.log(2)**2))

    @classmethod
    def expected_capacity(cls, bits, prob):
        """
        Returns the expected capacity given a number
        of bits and an enforced probability. Assumes optimal K.
        """
        return -bits/math.log(prob)*(math.log(2)**2)

    @classmethod
    def ideal_k(cls, bits, capacity):
        """
        Calculates the ideal K to minimize false positives
        given the number of bits and capacity.
        """
        return math.log(2) * bits / capacity

    @cython.boundscheck(False)
    @cython.wraparound(False)
    cdef void _compute_hashes(self, char* key):
        "Generates a specified number of hashes for a key"
        cdef size_t djb_hash, dek_hash, fnv_hash, js_hash
        cdef size_t fnv_prime = 0x811C9DC5
        cdef size_t salt

        cdef int i,j,rounds
        cdef unsigned int k = self.k_num
        cdef unsigned char key_val

        # Compute the number of rounds we need
        rounds = k / 4
        if (k & 3) > 0:
            rounds += 1
        
        for i from 0 <= i < rounds:
            # Reset the hashes
            djb_hash = 5381
            dek_hash = len(key)
            fnv_hash = 0
            js_hash = 1315423911
          
            # Salt if necessary
            if i > 0:
                dek_hash += sizeof(size_t)
                for j in range(sizeof(size_t)):
                    key_val = (salt >> (j<<3)) & 255
                    djb_hash = ((djb_hash << 5) + djb_hash) + key_val
                    dek_hash = ((dek_hash << 6) ^ (dek_hash >> 27)) ^ key_val
                    fnv_hash *= fnv_prime
                    fnv_hash ^= key_val
                    js_hash ^= ((js_hash << 5) + key_val + (js_hash >> 2))

            for key_val in key:
                djb_hash = ((djb_hash << 5) + djb_hash) + key_val
                dek_hash = ((dek_hash << 6) ^ (dek_hash >> 27)) ^ key_val
                fnv_hash *= fnv_prime
                fnv_hash ^= key_val
                js_hash ^= ((js_hash << 5) + key_val + (js_hash >> 2))

            # Copy the hashes
            self.hashes[i*4] = djb_hash
            self.hashes[i*4+1] = dek_hash
            self.hashes[i*4+2] = fnv_hash
            self.hashes[i*4+3] = js_hash

            # Generate a new salt
            salt = djb_hash ^ dek_hash ^ fnv_hash ^ js_hash

    def print_hashes(self, char* key):
        self._compute_hashes(key)
        cdef int i
        cdef size_t h

        # Set the bits for the hashes
        for i from 0 <= i < self.k_num:
            h = self.hashes[i]
            print "%u" % h, sizeof(size_t)

    @cython.boundscheck(False)
    @cython.wraparound(False)
    def add(self, char* key, int check_first=0):
        "Add a key to the set"
        if check_first:
            if self.__contains__(key): 
                return False
        else:
            self._compute_hashes(key)

        cdef size_t m = self.offset
        cdef size_t offset = 0
        cdef size_t h
        cdef int i

        # Set the bits for the hashes
        for i from 0 <= i < self.k_num:
            h = self.hashes[i]
            self.bitmap[offset + (h % m)] = 1
            offset += m

        self.count += 1
        return True

    @cython.boundscheck(False)
    @cython.wraparound(False)
    def __contains__(self, char* key):
        "Checks if the set contains a given key"
        self._compute_hashes(key)
        cdef size_t m = self.offset
        cdef size_t offset = 0
        cdef size_t h
        cdef int i
    
        for i from 0 <= i < self.k_num:
            h = self.hashes[i]
            if self.bitmap[offset+ (h % m)] == 0: return False
            offset += m
        return True

    def __len__(self):
        "Returns the number of elements in the bitmap"
        return self.count

    def flush(self):
        """
        Forces us to write out the current count to the bitmap,
        and flushes the underlying bitmap.
        """
        # Get the count string
        count_str = struct.pack(self.SIZE_FMT, self.count)

        # Set the count as the last bytes
        size_offset = self.bitmap_size / 8
        if self.bitmap: self.bitmap[size_offset:size_offset+self.SIZE_LEN] = count_str

        # Flush the underlying bitmap
        if self.bitmap: self.bitmap.flush()

    def close(self):
        "Closes the bloom filter and the underlying bitmap"
        if self.bitmap:
            self.flush()
            self.bitmap.close()
            self.bitmap = None

    def _read_count(self):
        "Reads the count from the bitmap"
        # Set the count as the last bytes
        size_offset = self.bitmap_size / 8
        count_str = self.bitmap[size_offset:size_offset+self.SIZE_LEN]
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

