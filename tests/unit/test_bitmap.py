"""
Contains tests for the Bitmap class.
"""

import pytest
from pyblooming.bitmap import Bitmap

class TestBitmap(object):

    @pytest.mark.xfail
    def test_get_length(self):
        """
        Tests that the length of the BitMap is the same number
        of bytes as those used to create the BitMap.
        """
        bitmap = Bitmap(16)
        assert 16 == len(bitmap)

    def test_all_zero(self):
        """
        Tests that a BitMap starts out with all zeros.
        """
        bitmap = Bitmap(16)
        for bit in xrange(16 * 8):
            assert 0 == bitmap[bit]

    def test_set_item(self):
        """
        Tests that a bit can be properly set and retrieved.
        """
        bitmap = Bitmap(16)

        assert 0 == bitmap[0]
        bitmap[0] = 1
        assert 1 == bitmap[0]

