from libc cimport stdlib
cimport cython
import os.path

cdef extern from "cbitmaputil.h" nogil:
    cdef char* mmap_file(int filedes, size_t len, int map_private)
    cdef int mummap_file(char* addr, size_t len)
    cdef int flush(int filedes, char* addr, size_t len)

cdef class Bitmap:
    cdef object fileobj
    cdef size_t size
    cdef int fileno
    cdef unsigned char* mmap

    def __cinit__(self, length, filename=None, private=False):
        """
        Creates a new Bitmap object. Bitmap wraps a memory mapped
        file and allows bit-level operations to be performed.
        A bitmap can either be created on a file, or using an anonymous map.

        :Parameters:
          - `length` : The length of the Bitmap in bytes. The number of bits is 8 times this.
          - `filename` (optional) : Defaults to None. If this is provided, the Bitmap will be file backed.
          - `private` (optional) : Defaults to False. If True, the bitmap
            is mapped using MAP_PRIVATE, making a private copy-on-write
            version of the memory mapped region. Otherwise, MAP_SHARED is used,
            and changes are reflected to other copies of the file.
        """
        # Check the length
        if length <= 0: raise ValueError, "Length must be positive!"
        self.size = length

        if not filename:
            # For anonymous mmaps, always use MAP_PRIVATE
            self.fileobj = None
            self.fileno = -1
            self.mmap = <unsigned char*>mmap_file(self.fileno, self.size, 1)
            if self.mmap == NULL:
                raise OSError, "Failed to create memory mapped region!"

        else:
            self.fileobj = open(filename, "a+")
            self.fileno = self.fileobj.fileno()

            # Zero-fill the file
            size_diff = length - os.path.getsize(filename)
            while size_diff > 0:
                self.fileobj.write(chr(0) * min(size_diff, 100000))
                self.fileobj.flush()
                size_diff = length - os.path.getsize(filename)

            # Create the memory mapped file
            priv = 1 if private else 0
            self.mmap = <unsigned char*>mmap_file(self.fileno, self.size, priv)
            if self.mmap == NULL:
                self.fileobj.close()
                raise OSError, "Failed to memory map the file!"

    def __len__(self):
        "Returns the size of the Bitmap in bits"
        return 8 * self.size

    @cython.boundscheck(False)
    @cython.wraparound(False)
    def __getitem__(self, size_t idx):
        "Gets the value of a specific bit. Must take an integer argument"
        return <int> (self.mmap[idx >> 3] >> (7 - idx % 8)) & 0x1

    @cython.boundscheck(False)
    @cython.wraparound(False)
    def __setitem__(self, size_t idx, unsigned int val):
        """
        Sets the value of a specific bit. The index must be an integer,
        but if val evaluates to True, the bit is set to 1, else 0.
        """
        if val:
            self.mmap[idx >> 3] = self.mmap[idx >> 3] | 1 << (7 - idx % 8)
        else:
            self.mmap[idx >> 3] = self.mmap[idx >> 3] & ~(1 << (7 - idx % 8))

    def flush(self):
        "Flushes the contents of the Bitmap to disk."
        cdef int flushres = 0
        if self.mmap:
            with nogil:
                flushres = flush(self.fileno, <char*>self.mmap, self.size)
            if flushres == -1:
                raise OSError, "Failed to flush the buffers!"
        if self.fileobj: 
            self.fileobj.flush()

    def close(self, flush=True):
        "Closes the Bitmap, flushing the data if requried."
        # Safety first!
        if flush:
            self.flush()

        # Close the mmap
        if self.mmap:
            mummap_file(<char*>self.mmap, self.size)
            self.mmap = NULL 

        # For non-anonymous maps, we need to close the file
        if self.fileobj:
            self.fileobj.close()
            self.fileobj = None 

    def __getslice__(self, i, j):
        "Allow direct access to the mmap, indexed by byte"
        if i >= j or i < 0 or j > self.size: raise ValueError, "Bad slice!"
        # Create a null terminated string
        return self.mmap[i:j]

    def __setslice__(self, i, j, char* val):
        "Allow direct access to the mmap, indexed by byte"
        if i >= j or i < 0 or j > self.size: raise ValueError, "Bad slice!"
        # Create a null terminated string
        cdef int size  = j-i
        cdef int x
        for x in xrange(size):
            self.mmap[i+x] = val[x]


