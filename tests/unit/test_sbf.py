"""
Contains tests for the scaling bloom filter class.
"""
import time
import os
import os.path
import pytest
import hashlib
from pyblooming.bitmap import Bitmap
from pyblooming import ScalingBloomFilter, BloomFilter

class TestBloomFilter(object):

    @classmethod
    def setup_class(cls):
        # Remove the mmap files
        mmap_files = [f for f in os.listdir(".") if f.endswith(".mmap")]
        [os.remove(f) for f in mmap_files]

    def test_initial_size(self):
        """
        Tests the initial size
        """
        bytes,k = BloomFilter.params_for_capacity(1e4, 1e-4)
        s = ScalingBloomFilter(initial_capacity=1e4, prob=1e-4)
        assert len(s) == 0
        assert len(s.filters) == 1
        assert s.total_capacity() == 1e4
        assert s.total_bitmap_size() == bytes

    def test_add_filter(self):
        """
        Tests that the filter grows
        """
        s = ScalingBloomFilter(initial_capacity=1e3, prob=1e-4, scale_size=4)
        [s.add("test%d" % x,True) for x in xrange(2000)]

        assert len(s) == 2000
        assert s.total_capacity() == 5*1e3 # Scales 4x + first filter
        assert len(s.filters) == 2
        assert all([s.__contains__("test%d" % x) for x in xrange(2000)])

        # Byte size should be slightly greater than a single
        # static bloom filter of the same configuration
        bytes,k = BloomFilter.params_for_capacity(5e3, 1e-4)
        assert s.total_bitmap_size() > bytes
        assert s.total_bitmap_size() <= 1.1*bytes

    def test_multiple_filters(self):
        """
        Tests that the filter grows
        """
        s = ScalingBloomFilter(initial_capacity=1e3, prob=1e-4, scale_size=4)
        [s.add("test%d" % x,True) for x in xrange(10000)]

        assert len(s) == 10000
        assert s.total_capacity() == 21*1e3 # Scales 4x(4x) + 4x + first filter
        assert len(s.filters) == 3
        assert all([s.__contains__("test%d" % x) for x in xrange(10000)])

        # Byte size should be slightly greater than a single
        # static bloom filter of the same configuration
        bytes,k = BloomFilter.params_for_capacity(21e3, 1e-4)
        assert s.total_bitmap_size() > bytes
        assert s.total_bitmap_size() <= 1.1*bytes

    def test_filename_callback(self):
        """
        Tests that the filter makes the callback to get the filenames
        """
        data = {"counter": 0}
        def getname():
            name = "test.multiple.%03d.mmap" % data["counter"]
            data["counter"] += 1
            return name

        s = ScalingBloomFilter(filenames=getname,initial_capacity=1e3, prob=1e-4, scale_size=4)
        [s.add("test%d" % x,True) for x in xrange(10000)]

        # Counter should get called 3 times
        assert data["counter"] == 3

    def test_bitmap_callback(self):
        """
        Tests that the filter makes the callback to get bitmaps
        """
        data = {"counter": 0}
        def getbitmap(length):
            data["counter"] += 1
            return Bitmap(length, None)

        s = ScalingBloomFilter(callback=getbitmap,initial_capacity=1e3, prob=1e-4, scale_size=4)
        [s.add("test%d" % x,True) for x in xrange(10000)]

        # Counter should get called 3 times
        assert data["counter"] == 3

    def test_doubleclose(self):
        """
        Tests that calling close twice is okay
        """
        data = {"counter": 0}
        def getname():
            name = "test.doubleclose.%03d.mmap" % data["counter"]
            data["counter"] += 1
            return name

        s = ScalingBloomFilter(filenames=getname,initial_capacity=1e3, prob=1e-4, scale_size=4)
        [s.add("test%d" % x,True) for x in xrange(10000)]
        s.close()
        s.close()

    def test_flushclose(self):
        """
        Test that flush followed by close is okay
        """
        data = {"counter": 0}
        def getname():
            name = "test.flushclose.%03d.mmap" % data["counter"]
            data["counter"] += 1
            return name

        s = ScalingBloomFilter(filenames=getname,initial_capacity=1e3, prob=1e-4, scale_size=4)
        [s.add("test%d" % x,True) for x in xrange(10000)]
        s.flush()
        s.close()

    def test_flush(self):
        """
        Tests that a flushes flushes the contents
        """
        data = {"counter": 0, "files":[]}
        def getname():
            name = "test.flush.%03d.mmap" % data["counter"]
            data["files"].append(name)
            data["counter"] += 1
            return name

        s = ScalingBloomFilter(filenames=getname,initial_capacity=1e3, prob=1e-4, scale_size=4)
        [s.add("test%d" % x,True) for x in xrange(10000)]
        s.flush()

        # Create the bloom filters
        bitmaps = [Bitmap(os.path.getsize(f), f) for f in data["files"]]
        filters = [BloomFilter(b,1) for b in bitmaps]
        s1 = ScalingBloomFilter(filters=filters,filenames=getname,initial_capacity=1e3, prob=1e-4, scale_size=4)

        # Compare shit
        assert len(s) == len(s1)
        assert len(s.filters) == len(s1.filters)
        assert all([s1.__contains__("test%d" % x) for x in xrange(10000)])
        assert s.total_capacity() == s1.total_capacity()
        assert s.total_bitmap_size() == s1.total_bitmap_size()

        # Close up
        s.close()
        s1.close()

    def test_close_does_flush(self):
        """
        Tests that a close does flush
        """
        data = {"counter": 0, "files":[]}
        def getname():
            name = "test.close.%03d.mmap" % data["counter"]
            data["files"].append(name)
            data["counter"] += 1
            return name

        s = ScalingBloomFilter(filenames=getname,initial_capacity=1e3, prob=1e-4, scale_size=4)
        [s.add("test%d" % x,True) for x in xrange(10000)]
        s.close()
        s = None

        # Create the bloom filters
        bitmaps = [Bitmap(os.path.getsize(f), f) for f in data["files"]]
        filters = [BloomFilter(b,1) for b in bitmaps]
        s = ScalingBloomFilter(filters=filters,filenames=getname,initial_capacity=1e3, prob=1e-4, scale_size=4)

        # Compare shit
        assert len(s) == 10000
        assert len(s.filters) == 3
        assert all([s.__contains__("test%d" % x) for x in xrange(10000)])
        s.close()

    @classmethod
    def teardown_class(cls):
        # Remove the mmap files
        mmap_files = [f for f in os.listdir(".") if f.endswith(".mmap")]
        [os.remove(f) for f in mmap_files]

