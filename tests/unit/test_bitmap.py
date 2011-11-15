"""
Contains tests for the Bitmap class.
"""
import time
import os
import pytest
from pyblooming.bitmap import Bitmap as pyBitmap
from pyblooming.cbitmap import Bitmap as cBitmap

class TestBitmap(object):

    @classmethod
    def setup_class(cls):
        # Remove the mmap files
        mmap_files = [f for f in os.listdir(".") if f.endswith(".mmap")]
        [os.remove(f) for f in mmap_files]

    def test_get_length(self):
        """
        Tests that the length of the BitMap is the same number
        of bytes as those used to create the BitMap. Handle the bit/byte
        conversion.
        """
        bitmap = pyBitmap(16)
        assert 16*8 == len(bitmap)

    def test_all_zero(self):
        """
        Tests that a BitMap starts out with all zeros.
        """
        bitmap = pyBitmap(16)
        for bit in xrange(16 * 8):
            assert 0 == bitmap[bit]

    def test_set_item(self):
        """
        Tests that a bit can be properly set and retrieved.
        """
        bitmap = pyBitmap(16)

        assert 0 == bitmap[0]
        bitmap[0] = 1
        assert 1 == bitmap[0]
        for bit in xrange(1,16 * 8):
            assert 0 == bitmap[bit]

    def test_setslice(self):
        """
        Tests that a slice can be properly set and retrieved
        """
        bitmap = pyBitmap(16)

        # Set all the bits to 1
        for bit in xrange(16 * 8):
            bitmap[bit] = 1

        bitmap[0:4] = "test"
        assert bitmap[0:4] == "test"

        for bit in xrange(4*8,16 * 8):
            assert 1 == bitmap[bit]

    def test_doubleclose(self):
        """
        Tests that a double close does not cause problems
        """
        bitmap = pyBitmap(16)
        bitmap.close()
        bitmap.close()

    def test_flushclose(self):
        """
        Tests that a flush and close does not cause issues
        """
        bitmap = pyBitmap(16)
        bitmap.flush()
        bitmap.close()

    def test_flush(self):
        """
        Tests that a flushes flushes the contents
        """
        bitmap = pyBitmap(16, "testflush.mmap")
        for bit in xrange(16*8):
            bitmap[bit] = 1
        bitmap.flush()

        bitmap1 = pyBitmap(16, "testflush.mmap")
        for bit in xrange(16*8):
            assert bitmap1[bit] == 1

        bitmap.close()
        bitmap1.close()

    def test_async_flush_notimpl(self):
        """
        Tests that async flushes are not implemented
        """
        with pytest.raises(NotImplementedError):
            bitmap = pyBitmap(16, "testflush.mmap")
            bitmap.flush(True)

    def test_close_does_flush(self):
        """
        Tests that a close does flush
        """
        bitmap = pyBitmap(16, "testcloseflush.mmap")
        for bit in xrange(16*8):
            bitmap[bit] = 1
        bitmap.close()
        bitmap = None

        bitmap = pyBitmap(16, "testcloseflush.mmap")
        for bit in xrange(16*8):
            assert bitmap[bit] == 1
        bitmap.close()

    @classmethod
    def teardown_class(cls):
        # Remove the mmap files
        mmap_files = [f for f in os.listdir(".") if f.endswith(".mmap")]
        [os.remove(f) for f in mmap_files]


class TestCBitmap(object):

    @classmethod
    def setup_class(cls):
        # Remove the mmap files
        mmap_files = [f for f in os.listdir(".") if f.endswith(".mmap")]
        [os.remove(f) for f in mmap_files]

    def test_get_length(self):
        """
        Tests that the length of the BitMap is the same number
        of bytes as those used to create the BitMap. Handle the bit/byte
        conversion.
        """
        bitmap = cBitmap(16)
        assert 16*8 == len(bitmap)

    def test_all_zero(self):
        """
        Tests that a BitMap starts out with all zeros.
        """
        bitmap = cBitmap(16)
        for bit in xrange(16 * 8):
            assert 0 == bitmap[bit]

    def test_set_item(self):
        """
        Tests that a bit can be properly set and retrieved.
        """
        bitmap = cBitmap(16)

        assert 0 == bitmap[0]
        bitmap[0] = 1
        assert 1 == bitmap[0]
        for bit in xrange(1,16 * 8):
            assert 0 == bitmap[bit]

    def test_setslice(self):
        """
        Tests that a slice can be properly set and retrieved
        """
        bitmap = cBitmap(16)

        # Set all the bits to 1
        for bit in xrange(16 * 8):
            bitmap[bit] = 1

        bitmap[0:4] = "test"
        assert bitmap[0:4] == "test"

        for bit in xrange(4*8,16 * 8):
            assert 1 == bitmap[bit]

    def test_doubleclose(self):
        """
        Tests that a double close does not cause problems
        """
        bitmap = cBitmap(16)
        bitmap.close()
        bitmap.close()

    def test_flushclose(self):
        """
        Tests that a flush and close does not cause issues
        """
        bitmap = cBitmap(16)
        bitmap.flush()
        bitmap.close()

    def test_flush(self):
        """
        Tests that a flushes flushes the contents
        """
        bitmap = cBitmap(16, "testcflush.mmap")
        for bit in xrange(16*8):
            bitmap[bit] = 1
        bitmap.flush()

        bitmap1 = cBitmap(16, "testcflush.mmap")
        for bit in xrange(16*8):
            assert bitmap1[bit] == 1

        bitmap.close()
        bitmap1.close()

    def test_async_flush(self):
        """
        Tests that an async flushes flushes the contents
        """
        bitmap = cBitmap(16, "testcasyncflush.mmap")
        for bit in xrange(16*8):
            bitmap[bit] = 1
        bitmap.flush(True)

        bitmap1 = cBitmap(16, "testcasyncflush.mmap")
        for bit in xrange(16*8):
            assert bitmap1[bit] == 1

        bitmap.close()
        bitmap1.close()

    def test_close_does_flush(self):
        """
        Tests that a close does flush
        """
        bitmap = cBitmap(16, "testccloseflush.mmap")
        for bit in xrange(16*8):
            bitmap[bit] = 1
        bitmap.close()
        bitmap = None

        bitmap = cBitmap(16, "testccloseflush.mmap")
        for bit in xrange(16*8):
            assert bitmap[bit] == 1
        bitmap.close()

    @classmethod
    def teardown_class(cls):
        # Remove the mmap files
        mmap_files = [f for f in os.listdir(".") if f.endswith(".mmap")]
        [os.remove(f) for f in mmap_files]

