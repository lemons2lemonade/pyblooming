"""
This package provides all the modules for PyBlooming.
"""
try:
    from cbitmap import Bitmap
except ImportError:
    from bitmap import Bitmap
from bloom import BloomFilter, ScalingBloomFilter

__all__ = ["Bitmap", "BloomFilter", "ScalingBloomFilter"]
__version__ = "0.1.0"
