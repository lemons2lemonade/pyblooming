#include <stdlib.h>
#include <unistd.h>
#include <sys/mman.h>

/**
 * Helper to grow an open file to a certain size
 * @arg filedes THe file descriptor to grow.
 * @arg len The size to grow it to.
 * @returns -1 on error, 0 on success;
 */
int grow_file(int filedes, int len) {
    // Seek to length - 1
    off_t result = lseek(filedes, len-1, SEEK_SET);
    
    // Check for an error, return an error code
    if (result == -1) return -1;

    // Write a byte to cause a sparse file to be made
    result = write(filedes, "", 1);

    // Check for an error, and exit
    if (result == -1) return -1;
    return 0;
}


/**
 * Helper to memory map open file descriptors.
 * @arg filedes The file descriptor to mmap in. -1 for anonymous.
 * @arg len The length of bytes to map in
 * @returns 0 on error, or the address of the memory map
 */
char* mmap_file(int filedes, int len) {
    int flags = 0;
    int fd = 0;

    // Handle anonymous or file backed
    if (filedes == -1) {
        flags |= MAP_ANON;
        flags |= MAP_PRIVATE;
        fd = -1;
    } else {
        flags |= MAP_FILE;
        flags |= MAP_PRIVATE;
        fd = filedes;
    }

    // Perform the map in
    char* addr = mmap(0, len, PROT_READ|PROT_WRITE, flags, fd, 0);

    // Check for an error, otherwise return
    if (addr == MAP_FAILED)
        return 0;
    else
        return addr;
}

/**
 * Helper to unmap memory mapped files.
 * @args addr The address to unmap
 * @args len The number of bytes to unmap
 * @returns -1 on error, else 0.
 */
int mummap_file(char* addr, int len) {
    int res = munmap(addr, len);
    if (res == -1) return -1;
    return 0;
}

/**
 * Helper to flush memory mapped files 
 * @arg filedes The file descriptor under the mmap file, -1 for anonymous
 * @arg addr The address of the memory mapped region
 * @arg len The length of bytes of the mmap region
 * @returns -1 on error, 0 on success
 */
int flush(int filedes, char* addr, int len) {
    // Don't bother if there is no file backing
    if (filedes >= 0) {
        // First flush the mmap regions syncronously
        int res = msync(addr, len, MS_SYNC);
        if (res == -1) return -1;

        res = fsync(filedes);
        if (res == -1) return -1;
    }

    return 0;
}

