PyBlooming
=========

PyBlooming is a library that encompasses provides three primary features: Bitmaps, classic bloom filters, and scaling bloom filters.

Bitmap support
-------------

The library includes the bitmap and cbitmap modules which provide
a simple interface to perform bit level operations on a memory mapped file. The size
of the bitmap is fixed, and it may optionally be a file-backed memory mapping. The cbitmap
module provides the same interface but provides a 5-10x speed improvement over the pure
Python implementation.

Classic bloom filters
--------------------

The library includes the bloom and cbloom modules which provide
support for classical, fixed size bloom filters. These static filters are initialized
on top of a Bitmap, and use a specified number of hash functions for their operations.
The BloomFilter classes provide a number of utility methods to build filters using the
appropriate parameters to meet specified capacity and false positive rate requirements.
Because of how the BloomFilters are layered on top of the Bitmap objects, they can very
easily persist and restore themselves by using file backed Bitmaps. The cbloom module provides
the same interface and is fully compatible with the pure python implementation but offers
a 20-50x speed improvement.

Scaling bloom filters
---------------------

Built on top of classic bloom filters, scaling bloom filters
are not contrained to a fix capacity and instead grow as needed to accomodate more
elements. SBF's are constructed by layering multiple classic bloom filters on top of
each other and adding new layers which grow geometrically as more space is needed.
SBF's also use a few techniques to maintain a fixed false positive rate as more 
filters are added. The ScalingBloomFilter class exposes a very similar interface to
the BloomFilters class.

Install
-------

Download and install from source::
    
    python setup.py install

Examples
------

Creating and using a bitmap is very simple::

    # Importing from pyblooming will automatically
    # try to import the more performant C implementation,
    # and fallback onto the pure python implementations
    # if necessary.
    from pyblooming import Bitmap 

    # Create an anonymous Bitmap, 32 bytes
    b = Bitmap(32)

    # Set the 5th bit to 1
    b[5] = 1
    assert b[5] == 1

    # Create a 4K file backed bitmap
    b = Bitmap(4096, "test.mmap")

    # Set the thousandth bit to 1
    b[1000] = 1
    assert b[1000] == 1

    # Bitmaps support slicing, which operates on bytes
    # We can assign the first 3 bytes
    b[0:3] = "foo"

    # Do a clean close to flush to disk
    b.close()

Using bloom filters is also similar to how native sets are used::
    
    # Importing from pyblooming will automatically
    # try to import the more performant C implementation,
    # and fallback onto the pure python implementations
    # if necessary.
    from pyblooming import BloomFilter, Bitmap

    # Create a new static bloom filter with room for
    # 1000 elements and a 1/100 error rate.
    bf = BloomFilter.for_capacity(1000, 0.01)
    
    # Do some set operations with the bloom filter
    assert "test" not in bf
    bf.add("test")
    assert "test" in bf
    assert len(bf) == 1

    # Creating a file backed filter is simple too
    bytes, k = BloomFilter.params_for_capacity(1000, 0.01)
    bf = BloomFilter(Bitmap(bytes, "test.mmap"), k)

    # Do some set operations with the bloom filter
    assert "foo" not in bf
    bf.add("foo")
    assert "foo" in bf
    assert len(bf) == 1

    # Flush and close the filter
    bf.flush()
    bf.close()

Lastly, scaling bloom filters can be more complicated to use, especially
if file backing is needed. To support file backing, the ScalingBloomFilter
supports a callback mechanism to generate the file name for the next filter
to create. However, in-memory usage remains very simple::

    from pyblooming import ScalingBloomFilter

    # Create a scaling bloom filter, with an initial capacity
    # and maximum false positive rate.
    sbf = ScalingBloomFilter(initial_capacity=1000, prob=0.01)
    assert sbf.total_capacity() == 10000

    # Add more than the available capacity
    for x in xrange(2000);
        sbf.add("test%d" % x)

    # Check the new size
    assert len(sbf) == 2000
    assert sbf.total_capacity() > 1000

    # Add a method to support file backed filters
    COUNT = 0
    def next_name():
        global COUNT
        COUNT += 1
        return COUNT
    
    # Create with our callback
    sbf = ScalingBloomFilter(filenames=next_name, initial_capacity=1000, prob=0.01)
    assert COUNT == 1

    # Add more than the available capacity
    for x in xrange(2000);
        sbf.add("test%d" % x)

    # At this point, we should have added a new bloom filter
    assert COUNT == 2


