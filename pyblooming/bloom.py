"""
Implements an easy to use Bloom filter on top of
the bitmap implementation.
"""
import math
import bitmap as bitmaplib

class BloomFilter(object):
    def __init__(self, bitmap=None, length=16777216, k=4):
        """
        Creates a new Bloom Filter instance. A bloom filter
        requires a bitmap underneath, which can either be
        provided or created. If a bitmask is not provided, then
        an anonymous bitmap is created and used. The anonymous
        bitmap defaults to 16M but that can be changed.

        :Parameters:
            - bitmap (optional) : The bitmap that should be used.
                An anonymous bitmap will be created if one is not
                provided.

            - length (optional) : The size of the anonymous bitmap
                in bytes to create. Defaults to 16M.

            - k (optional) : The number of hashing algorithms to
                use. Must be at least 1, up to 4. All 4 are computed
                simultaneously, so there is not much performance
                saving in reducing this.
        """
        if k < 1 or k > 4: raise ValueError, "Bad value provided for k!"
        if not bitmap: bitmap = bitmaplib.Bitmap(length)
        self.bitmap = bitmap
        self.bitmap_size = len(bitmap)
        self.k_num = k

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

    def _hash(self, key):
        "Computes and returns the DJB, DEK, FNV, and JS hashes"
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

    def add(self, key):
        "Add a key to the set"
        if not isinstance(key, str): raise ValueError, "Key must be a string!"
        hashes = self._hash(key)[:self.k_num]
        m = self.bitmap_size
        for h in hashes:
            self.bitmap[h % m] = 1

    def __contains__(self, key):
        "Checks if the set contains a given key"
        if not isinstance(key, str): raise ValueError, "Key must be a string!"
        hashes = self._hash(key)[:self.k_num]
        m = self.bitmap_size
        return all(self.bitmap[h % m] for h in hashes)

    def __or__(self, bloom):
        "Implements a set union"
        if not isinstance(bloom, BloomFilter): raise ValueError, "Cannot perform union with non-BloomFilter!"
        bitmap = self.bitmap | bloom.bitmap
        return BloomFilter(bitmap=bitmap,k=self.k_num)

    def __and__(self, bloom):
        "Implements a set intersection"
        if not isinstance(bloom, BloomFilter): raise ValueError, "Cannot perform intersection with non-BloomFilter!"
        bitmap = self.bitmap & bloom.bitmap
        return BloomFilter(bitmap=bitmap,k=self.k_num)

    def __len__(self):
        "Returns the length of the bitmap"
        return len(self.bitmap)

