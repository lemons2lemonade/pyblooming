"""
This package provides all the modules for PyBlooming.
"""
try:
    from cbitmap import Bitmap
except ImportError:
    from bitmap import Bitmap
try:
    from cbloom import BloomFilter
except ImportError:
    from bloom import BloomFilter

from sbf import ScalingBloomFilter

__all__ = ["Bitmap", "BloomFilter", "ScalingBloomFilter"]
__version__ = "0.2.0"
