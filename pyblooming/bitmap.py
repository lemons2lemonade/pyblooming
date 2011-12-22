"""
Implements a simple class to address individual bits using
a memory mapped file.
"""
import mmap
import os.path

class Bitmap(object):
    def __init__(self, length, filename=None, private=False):
        """
        Creates a new Bitmap object. Bitmap wraps a memory mapped
        file and allows bit-level operations to be performed. A bitmap can
        either be created on a file or can use an anonymous map.

        :Parameters:
          - `length`: The length of the Bitmap in bytes. The number of bits
            is 8 times this.
          - `filename` (optional) : Defaults to None. If this is provided,
            the Bitmap will be file backed.
          - `private` (optional) : Defaults to False. If True, the bitmap
            is mapped using MAP_PRIVATE, making a private copy-on-write
            version of the memory mapped region. Otherwise, MAP_SHARED is used,
            and changes are reflected to other copies of the file.
        """
        # Save if  the size
        self.size = length

        # Get the mode
        flags = mmap.MAP_SHARED
        if private:
            flags = mmap.MAP_PRIVATE

        if not filename:
            # For an anonymous mmap, we always use private with no file descriptor
            self.fileobj = None
            self.mmap = mmap.mmap(-1, length, flags=mmap.MAP_PRIVATE)

        else:
            self.fileobj = open(filename, "a+")

            # Zero-fill the file
            size_diff = length - os.path.getsize(filename)
            while size_diff > 0:
                self.fileobj.write(chr(0) * min(size_diff, 100000))
                self.fileobj.flush()
                size_diff = length - os.path.getsize(filename)

            # Create the memory mapped file, using the proper flags
            self.mmap = mmap.mmap(self.fileobj.fileno(), length, flags=flags)

    def __len__(self):
        "Returns the size of the Bitmap in bits"
        return 8 * self.size

    def __getitem__(self, idx):
        "Gets the value of a specific bit. Must take an integer argument"
        byte = idx >> 3
        byte_off  = 7 - idx % 8
        byte_val = ord(self.mmap[byte])
        return (byte_val >> byte_off) & 0x1

    def __setitem__(self, idx, val):
        """
        Sets the value of a specific bit. The index must be an integer,
        but if val evaluates to True, the bit is set to 1, else 0.
        """
        byte = idx >> 3
        byte_off  = 7 - idx % 8
        byte_val = ord(self.mmap[byte])
        if val:
            byte_val |= 1 << byte_off
        else:
            byte_val &= ~(1 << byte_off)
        self.mmap[byte] = chr(byte_val)
        return val

    def flush(self):
        "Flushes the contents of the Bitmap to disk."
        if self.mmap: self.mmap.flush()
        if self.fileobj: self.fileobj.flush()

    def close(self, flush=True):
        "Closes the Bitmap, flushing the data if specified."
        # Safety first!
        if flush:
            self.flush()

        # Close the mmap
        if self.mmap: self.mmap.close()
        self.mmap = None

        # For non-anonymous maps, we need to close the file
        if self.fileobj:
            self.fileobj.close()
            self.fileobj = None

    def __getslice__(self, i, j):
        "Allow direct access to the mmap, indexed by byte"
        return self.mmap[i:j]

    def __setslice__(self, i, j, val):
        "Allow direct access to the mmap, indexed by byte"
        self.mmap[i:j] = val

