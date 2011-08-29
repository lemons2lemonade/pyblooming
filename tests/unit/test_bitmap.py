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

    def test_union_fails_if_nonbitmap(self):
        """
        Tests that the union can only be calculated on another bitmap.
        """
        a = Bitmap(16)
        b = "Foo"

        with pytest.raises(ValueError):
            a | b

    def test_union_fails_if_unequal_size(self):
        """
        Tests that the union can only be calculated on another bitmap
        of the equivalent size.
        """
        a = Bitmap(16)
        b = Bitmap(32)

        with pytest.raises(ValueError):
            a | b

    def test_union(self):
        """
        Tests that the union of two bitmaps can be successfully calculated.
        """
        a = Bitmap(16)
        b = Bitmap(16)

        a[0] = 1
        b[1] = 1

        c = a | b
        assert 1 == c[0]
        assert 1 == c[1]
        assert 0 == c[2]


    def test_intersection_fails_if_nonbitmap(self):
        """
        Tests that the intersection can only be calculated on another bitmap.
        """
        a = Bitmap(16)
        b = "Foo"

        with pytest.raises(ValueError):
            a & b

    def test_intersection_fails_if_unequal_size(self):
        """
        Tests that the intersection can only be calculated on another bitmap
        of the equivalent size.
        """
        a = Bitmap(16)
        b = Bitmap(32)

        with pytest.raises(ValueError):
            a & b

    def test_intersection(self):
        """
        Tests that the intersection of two bitmaps can be calculated.
        """
        a = Bitmap(16)
        b = Bitmap(16)

        a[1] = 1
        b[1] = 1

        c = a & b
        assert 0 == c[0]
        assert 1 == c[1]
