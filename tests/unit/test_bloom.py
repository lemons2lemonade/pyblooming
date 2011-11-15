"""
Contains tests for the main bloom filter class.
"""
import time
import os
import pytest
import hashlib
from pyblooming import Bitmap
from pyblooming.bloom import BloomFilter as pyBloom
from pyblooming.cbloom import BloomFilter as cBloom

class TestBloomFilter(object):

    @classmethod
    def setup_class(cls):
        # Remove the mmap files
        mmap_files = [f for f in os.listdir(".") if f.endswith(".mmap")]
        [os.remove(f) for f in mmap_files]

    def test_no_bitmap(self):
        """
        Tests the constructor complains when there is no bitmap
        """
        with pytest.raises(ValueError):
            pyBloom(None, 3)

    def test_sane_k(self):
        """
        Test the k value is sanity checked
        """
        with pytest.raises(ValueError):
            pyBloom(Bitmap(16), 0)

    def test_small_bitmap(self):
        """
        Tests initializing with a bitmap that is too small
        (e.g. less than or equal to the extra_buffer() size)
        """
        with pytest.raises(ValueError):
            pyBloom(Bitmap(pyBloom.extra_buffer()), 3)

    def test_required_bits(self):
        """
        Tests that the number of required bits that the bloom filter
        says it needs is correct given some known-sane values.
        """
        # From http://hur.st/bloomfilter?n=1e6&p=1e-4
        assert pyBloom.required_bits(1e6,1e-4) == 19170117

    def test_required_bytes(self):
        """
        Tests that the number of required bytes that the bloom filter
        says it needs is the correct given some known-sane values.
        """
        # From http://hur.st/bloomfilter?n=1e6&p=1e-4
        assert round(pyBloom.required_bits(1e6,1e-4) / 8.0) == round(19170117 / 8.0)

    def test_expected_prob(self):
        """
        Tests that the expected probability of false positives
        is correct given known-sane values.
        """
        # From http://hur.st/bloomfilter?n=1e6&p=1e-4
        assert round(pyBloom.expected_probability(19170117, 1e6),4) == 1e-4

    def test_expected_capacity(self):
        """
        Tests that the expected capacity is correct given known-sane values.
        """
        # From http://hur.st/bloomfilter?n=1e6&p=1e-4
        assert round(pyBloom.expected_capacity(19170117, 1e-4)) == 1e6

    def test_ideal_k(self):
        """
        Tests that the ideal K is correct given known-sane values.
        """
        # From http://hur.st/bloomfilter?n=1e6&p=1e-4
        assert round(pyBloom.ideal_k(19170117, 1e6)) == 13

    def test_params_for_capacity(self):
        """
        Tests that the parameters that are generated for a given
        capacity and probability are correct given known sane values.
        """
        # From http://hur.st/bloomfilter?n=1e6&p=1e-4
        bytes, k = pyBloom.params_for_capacity(1e6, 1e-4)
        assert bytes-pyBloom.extra_buffer() == round(19170117 / 8.0)
        assert k == 14 # Parameters uses the ceiling instead of rounding

    def test_for_capacity(self):
        """
        Tests that the for_capacity method makes a sane bloom filter
        using parameters that are generated for a given
        capacity and probability are correct given known sane values.
        """
        # From http://hur.st/bloomfilter?n=1e6&p=1e-4
        bf = pyBloom.for_capacity(1e6,1e-4)

        # Check the bitmap size
        assert (len(bf.bitmap)/8)-pyBloom.extra_buffer() == round(19170117 / 8.0)

        # Check the k num
        assert bf.k_num == 14 # Parameters uses the ceiling instead of rounding


    def test_add_with_check(self):
        """
        Tests that adding to a bloom filter while checking
        for existing entries works
        """
        bf = pyBloom.for_capacity(1000,1e-4)

        # Assert all adds work
        assert all([bf.add("test%d" % x,True) for x in xrange(1000)])
        assert all([bf.__contains__("test%d" % x) for x in xrange(1000)])
        assert len(bf) == 1000

        # Assert all adds fail
        assert not any([bf.add("test%d" % x,True) for x in xrange(1000)])
        assert len(bf) == 1000

    def test_add_without_check(self):
        """
        Tests that adding to a bloom filter while checking
        for existing entries works
        """
        bf = pyBloom.for_capacity(1000,1e-4)

        # Assert all adds work
        assert all([bf.add("test%d" % x,False) for x in xrange(1000)])
        assert all([bf.__contains__("test%d" % x) for x in xrange(1000)])
        assert len(bf) == 1000

        # Assert all adds work
        assert all([bf.add("test%d" % x,False) for x in xrange(1000)])
        assert len(bf) == 2000

    def test_add_none(self):
        """
        Tests adding None to a set. This should fail.
        """
        bf = pyBloom.for_capacity(1000,1e-4)
        with pytest.raises(TypeError):
            bf.add(None)

    def test_add_int(self):
        """
        Tests adding an int to a set. This should fail.
        """
        bf = pyBloom.for_capacity(1000,1e-4)
        with pytest.raises(TypeError):
            bf.add(1234)

    def test_check_none(self):
        """
        Tests checking None in a set. This should fail.
        """
        bf = pyBloom.for_capacity(1000,1e-4)
        with pytest.raises(TypeError):
            None in bf

    def test_check_int(self):
        """
        Tests checking for an int in a set. This should fail.
        """
        bf = pyBloom.for_capacity(1000,1e-4)
        with pytest.raises(TypeError):
            1234 in bf

    def test_length(self):
        """
        Tests that length works
        """
        bf = pyBloom.for_capacity(1000,1e-4)
        assert len(bf) == 0
        [bf.add("test%d" % x) for x in xrange(1000)]
        assert len(bf) == 1000

    def test_doubleclose(self):
        """
        Tests that a double close does not cause problems
        """
        bitmap = Bitmap(1024, "testdoubleclose.mmap")
        bf = pyBloom(bitmap, 2)
        bf.close()
        bf.close()

    def test_flushclose(self):
        """
        Tests that a flush and close does not cause issues
        """
        bitmap = Bitmap(1024, "testflushclose.mmap")
        bf = pyBloom(bitmap, 2)
        bf.flush()
        bf.close()

    def test_flush(self):
        """
        Tests that a flushes flushes the contents
        """
        bitmap = Bitmap(1024, "testpyflush.mmap")
        bf = pyBloom(bitmap, 2)
        [bf.add("test%d" % x) for x in xrange(1000)]
        bf.flush()

        # Make a new bitmap
        bitmap2 = Bitmap(1024, "testpyflush.mmap")
        bf1 = pyBloom(bitmap2, 20)
        assert bf1.k_num == 2 # Should restore
        assert len(bf1) == 1000
        assert all([bf1.__contains__("test%d" % x) for x in xrange(1000)])

        bf1.close()
        bf.close()

    def test_async_flush(self):
        """
        Tests that a flushes flushes the contents
        """
        bitmap = Bitmap(1024, "testpyasyncflush.mmap")
        bf = pyBloom(bitmap, 2)
        [bf.add("test%d" % x) for x in xrange(1000)]
        bf.flush(True)
        time.sleep(1)

        # Make a new bitmap
        bitmap2 = Bitmap(1024, "testpyasyncflush.mmap")
        bf1 = pyBloom(bitmap2, 20)
        assert bf1.k_num == 2 # Should restore
        assert len(bf1) == 1000
        assert all([bf1.__contains__("test%d" % x) for x in xrange(1000)])

        bf1.close()
        bf.close()

    def test_close_does_flush(self):
        """
        Tests that a close does flush
        """
        bitmap = Bitmap(1024, "testpycloseflush.mmap")
        bf = pyBloom(bitmap, 2)
        [bf.add("test%d" % x) for x in xrange(1000)]
        bf.close()

        # Make a new bitmap
        bitmap = Bitmap(1024, "testpycloseflush.mmap")
        bf = pyBloom(bitmap, 20)
        assert bf.k_num == 2 # Should restore
        assert len(bf) == 1000
        assert all([bf.__contains__("test%d" % x) for x in xrange(1000)])
        bf.close()

    def test_prob(self):
        """
        Tests that the bloom filter is only wrong within
        a certain threshold.
        """
        # Only wrong once per hundred
        bf = pyBloom.for_capacity(1000,0.01)
        res = [bf.add("test%d" % x,True) for x in xrange(1000)]
        num_wrong = len([x for x in res if x is False])

        # Should get about 10 wrong
        assert num_wrong >= 5
        assert num_wrong <= 15

    @classmethod
    def teardown_class(cls):
        # Remove the mmap files
        mmap_files = [f for f in os.listdir(".") if f.endswith(".mmap")]
        [os.remove(f) for f in mmap_files]

class TestCBloomFilter(object):

    @classmethod
    def setup_class(cls):
        # Remove the mmap files
        mmap_files = [f for f in os.listdir(".") if f.endswith(".mmap")]
        [os.remove(f) for f in mmap_files]

    def test_no_bitmap(self):
        """
        Tests the constructor complains when there is no bitmap
        """
        with pytest.raises(ValueError):
            cBloom(None, 3)

    def test_sane_k(self):
        """
        Test the k value is sanity checked
        """
        with pytest.raises(ValueError):
            cBloom(Bitmap(16), 0)

    def test_small_bitmap(self):
        """
        Tests initializing with a bitmap that is too small
        (e.g. less than or equal to the extra_buffer() size)
        """
        with pytest.raises(ValueError):
            cBloom(Bitmap(cBloom.extra_buffer()), 3)

    def test_required_bits(self):
        """
        Tests that the number of required bits that the bloom filter
        says it needs is correct given some known-sane values.
        """
        # From http://hur.st/bloomfilter?n=1e6&p=1e-4
        assert cBloom.required_bits(1e6,1e-4) == 19170117

    def test_required_bytes(self):
        """
        Tests that the number of required bytes that the bloom filter
        says it needs is the correct given some known-sane values.
        """
        # From http://hur.st/bloomfilter?n=1e6&p=1e-4
        assert round(cBloom.required_bits(1e6,1e-4) / 8.0) == round(19170117 / 8.0)

    def test_expected_prob(self):
        """
        Tests that the expected probability of false positives
        is correct given known-sane values.
        """
        # From http://hur.st/bloomfilter?n=1e6&p=1e-4
        assert round(cBloom.expected_probability(19170117, 1e6),4) == 1e-4

    def test_expected_capacity(self):
        """
        Tests that the expected capacity is correct given known-sane values.
        """
        # From http://hur.st/bloomfilter?n=1e6&p=1e-4
        assert round(cBloom.expected_capacity(19170117, 1e-4)) == 1e6

    def test_ideal_k(self):
        """
        Tests that the ideal K is correct given known-sane values.
        """
        # From http://hur.st/bloomfilter?n=1e6&p=1e-4
        assert round(cBloom.ideal_k(19170117, 1e6)) == 13

    def test_params_for_capacity(self):
        """
        Tests that the parameters that are generated for a given
        capacity and probability are correct given known sane values.
        """
        # From http://hur.st/bloomfilter?n=1e6&p=1e-4
        bytes, k = cBloom.params_for_capacity(1e6, 1e-4)
        assert bytes-cBloom.extra_buffer() == round(19170117 / 8.0)
        assert k == 14 # Parameters uses the ceiling instead of rounding

    def test_for_capacity(self):
        """
        Tests that the for_capacity method makes a sane bloom filter
        using parameters that are generated for a given
        capacity and probability are correct given known sane values.
        """
        # From http://hur.st/bloomfilter?n=1e6&p=1e-4
        bf = cBloom.for_capacity(1e6,1e-4)

        # Check the bitmap size
        assert (len(bf.bitmap)/8)-cBloom.extra_buffer() == round(19170117 / 8.0)

        # Check the k num
        assert bf.k_num == 14 # Parameters uses the ceiling instead of rounding


    def test_add_with_check(self):
        """
        Tests that adding to a bloom filter while checking
        for existing entries works
        """
        bf = cBloom.for_capacity(1000,1e-4)

        # Assert all adds work
        assert all([bf.add("test%d" % x,True) for x in xrange(1000)])
        assert all([bf.__contains__("test%d" % x) for x in xrange(1000)])
        assert len(bf) == 1000

        # Assert all adds fail
        assert not any([bf.add("test%d" % x,True) for x in xrange(1000)])
        assert len(bf) == 1000

    def test_add_without_check(self):
        """
        Tests that adding to a bloom filter while checking
        for existing entries works
        """
        bf = cBloom.for_capacity(1000,1e-4)

        # Assert all adds work
        assert all([bf.add("test%d" % x,False) for x in xrange(1000)])
        assert all([bf.__contains__("test%d" % x) for x in xrange(1000)])
        assert len(bf) == 1000

        # Assert all adds work
        assert all([bf.add("test%d" % x,False) for x in xrange(1000)])
        assert len(bf) == 2000

    def test_add_none(self):
        """
        Tests adding None to a set. This should fail.
        """
        bf = cBloom.for_capacity(1000,1e-4)
        with pytest.raises(TypeError):
            bf.add(None)

    def test_add_int(self):
        """
        Tests adding an int to a set. This should fail.
        """
        bf = cBloom.for_capacity(1000,1e-4)
        with pytest.raises(TypeError):
            bf.add(1234)

    def test_check_none(self):
        """
        Tests checking None in a set. This should fail.
        """
        bf = cBloom.for_capacity(1000,1e-4)
        with pytest.raises(TypeError):
            None in bf

    def test_check_int(self):
        """
        Tests checking for an int in a set. This should fail.
        """
        bf = cBloom.for_capacity(1000,1e-4)
        with pytest.raises(TypeError):
            1234 in bf

    def test_length(self):
        """
        Tests that length works
        """
        bf = cBloom.for_capacity(1000,1e-4)
        assert len(bf) == 0
        [bf.add("test%d" % x) for x in xrange(1000)]
        assert len(bf) == 1000

    def test_doubleclose(self):
        """
        Tests that a double close does not cause problems
        """
        bitmap = Bitmap(1024, "testdoubleclose.mmap")
        bf = cBloom(bitmap, 2)
        bf.close()
        bf.close()

    def test_flushclose(self):
        """
        Tests that a flush and close does not cause issues
        """
        bitmap = Bitmap(1024, "testflushclose.mmap")
        bf = cBloom(bitmap, 2)
        bf.flush()
        bf.close()

    def test_flush(self):
        """
        Tests that a flushes flushes the contents
        """
        bitmap = Bitmap(1024, "testcflush.mmap")
        bf = cBloom(bitmap, 2)
        [bf.add("test%d" % x) for x in xrange(1000)]
        bf.flush()

        # Make a new bitmap
        bitmap2 = Bitmap(1024, "testcflush.mmap")
        bf1 = cBloom(bitmap2, 20)
        assert bf1.k_num == 2 # Should restore
        assert len(bf1) == 1000
        assert all([bf1.__contains__("test%d" % x) for x in xrange(1000)])

        bf1.close()
        bf.close()

    def test_async_flush(self):
        """
        Tests that a flushes flushes the contents
        """
        bitmap = Bitmap(1024, "testcasyncflush.mmap")
        bf = cBloom(bitmap, 2)
        [bf.add("test%d" % x) for x in xrange(1000)]
        bf.flush(True)
        time.sleep(1)

        # Make a new bitmap
        bitmap2 = Bitmap(1024, "testcasyncflush.mmap")
        bf1 = cBloom(bitmap2, 20)
        assert bf1.k_num == 2 # Should restore
        assert len(bf1) == 1000
        assert all([bf1.__contains__("test%d" % x) for x in xrange(1000)])

        bf1.close()
        bf.close()

    def test_close_does_flush(self):
        """
        Tests that a close does flush
        """
        bitmap = Bitmap(1024, "testccloseflush.mmap")
        bf = cBloom(bitmap, 2)
        [bf.add("test%d" % x) for x in xrange(1000)]
        bf.close()

        # Make a new bitmap
        bitmap = Bitmap(1024, "testccloseflush.mmap")
        bf = cBloom(bitmap, 20)
        assert bf.k_num == 2 # Should restore
        assert len(bf) == 1000
        assert all([bf.__contains__("test%d" % x) for x in xrange(1000)])
        bf.close()

    def test_prob(self):
        """
        Tests that the bloom filter is only wrong within
        a certain threshold.
        """
        # Only wrong once per hundred
        bf = cBloom.for_capacity(1000,0.01)
        res = [bf.add("test%d" % x,True) for x in xrange(1000)]
        num_wrong = len([x for x in res if x is False])

        # Should get about 10 wrong
        assert num_wrong >= 5
        assert num_wrong <= 15

    @classmethod
    def teardown_class(cls):
        # Remove the mmap files
        mmap_files = [f for f in os.listdir(".") if f.endswith(".mmap")]
        [os.remove(f) for f in mmap_files]

class TestFilterCompatibility(object):
    """
    Tests that cBloomFilter and pyBloomFilter are compatible
    """

    @classmethod
    def setup_class(cls):
        # Remove the mmap files
        mmap_files = [f for f in os.listdir(".") if f.endswith(".mmap")]
        [os.remove(f) for f in mmap_files]

    @classmethod
    def compare_files(cls, file1, file2):
        "Compares the md5 hashes of the files"
        raw1 = open(file1).read()
        raw2 = open(file2).read()
        hash1 = hashlib.md5(raw1).digest()
        hash2 = hashlib.md5(raw2).digest()
        assert hash1 == hash2

    def test_equality_1(self):
        """
        Tests that the two implementation generate matching mmaps
        """
        bytes, k = cBloom.params_for_capacity(1e4, 1e-4)
        bitmap = Bitmap(bytes, "testcompatc.mmap")
        bf1 = cBloom(bitmap, k)
        [bf1.add("test%d" % x) for x in xrange(10000)]

        # Make a new bitmap
        bitmap = Bitmap(bytes, "testcompatpy.mmap")
        bf2 = pyBloom(bitmap, k)
        [bf2.add("test%d" % x) for x in xrange(10000)]

        # Check the lengths
        assert len(bf1) == len(bf2)
        bf1.close()
        bf2.close()

        # Compare the mmap files
        self.compare_files("testcompatc.mmap", "testcompatpy.mmap")

    def test_equality_2(self):
        """
        Tests that the two implementation generate matching mmaps
        """
        bytes, k = cBloom.params_for_capacity(2e4, 1e-3)
        bitmap = Bitmap(bytes, "testcompatc2.mmap")
        bf1 = cBloom(bitmap, k)
        [bf1.add("foo%d" % x) for x in xrange(20000)]

        # Make a new bitmap
        bitmap = Bitmap(bytes, "testcompatpy2.mmap")
        bf2 = pyBloom(bitmap, k)
        [bf2.add("foo%d" % x) for x in xrange(20000)]

        # Check the lengths
        assert len(bf1) == len(bf2)
        bf1.close()
        bf2.close()

        # Compare the mmap files
        self.compare_files("testcompatc2.mmap", "testcompatpy2.mmap")

    def test_swap(self):
        """
        Swaps the mmap files from one implementation to another,
        check that things work. Start with cBloom, then pyBloom.
        """
        bytes, k = cBloom.params_for_capacity(2e4, 1e-3)
        bitmap = Bitmap(bytes, "testswap1.mmap")
        bf1 = cBloom(bitmap, k)
        [bf1.add("foo%d" % x) for x in xrange(20000)]
        bf1.close()

        # Make a new bitmap
        bitmap = Bitmap(bytes, "testswap1.mmap")
        bf2 = pyBloom(bitmap, 50)
        assert len(bf2) == 20000 # Should reload size and k
        assert bf2.k_num == k

        # Check all the entries
        assert all([bf2.__contains__("foo%d" % x) for x in xrange(20000)])
        bf2.close()

    def test_swap_2(self):
        """
        Swaps the mmap files from one implementation to another,
        check that things work. Start with pyBloom, then cBloom.
        """
        bytes, k = pyBloom.params_for_capacity(2e4, 1e-3)
        bitmap = Bitmap(bytes, "testswap2.mmap")
        bf1 = pyBloom(bitmap, k)
        [bf1.add("foo%d" % x) for x in xrange(20000)]
        bf1.close()

        # Make a new bitmap
        bitmap = Bitmap(bytes, "testswap2.mmap")
        bf2 = cBloom(bitmap, 50)
        assert len(bf2) == 20000 # Should reload size and k
        assert bf2.k_num == k

        # Check all the entries
        assert all([bf2.__contains__("foo%d" % x) for x in xrange(20000)])
        bf2.close()

    @classmethod
    def teardown_class(cls):
        # Remove the mmap files
        mmap_files = [f for f in os.listdir(".") if f.endswith(".mmap")]
        [os.remove(f) for f in mmap_files]

