#include <stdlib.h>
#include <unistd.h>
#include <stdio.h>
#include <sys/mman.h>

/**
 * Helper to memory map open file descriptors.
 * @arg filedes The file descriptor to mmap in. -1 for anonymous.
 * @arg len The length of bytes to map in
 * @arg map_private Forces the mmap to use MAP_PRIVATE
 * @returns 0 on error, or the address of the memory map
 */
char* mmap_file(int filedes, size_t len, int map_private) {
    int flags = 0;
    int fd = 0;

    // Handle anonymous or file backed
    if (filedes == -1) {
        flags |= MAP_ANON;
        flags |= MAP_PRIVATE;
        fd = -1;
    } else {
        flags |= MAP_FILE;
        if (map_private) {
            flags |= MAP_PRIVATE;
        } else {
            flags |= MAP_SHARED;
        }
        fd = filedes;
    }

    // Perform the map in
    char* addr = mmap(NULL, len, PROT_READ|PROT_WRITE, flags, fd, 0);

    // Check for an error, otherwise return
    if (addr == MAP_FAILED) {
        perror("Failed to mmap");
        return 0;
    }

    // Fault the memory in 
    int res = madvise(addr, len, MADV_WILLNEED);
    if (res != 0) {
        perror("Failed to call madvise()");
    }

    return addr;
}

/**
 * Helper to unmap memory mapped files.
 * @args addr The address to unmap
 * @args len The number of bytes to unmap
 * @returns -1 on error, else 0.
 */
int mummap_file(char* addr, size_t len) {
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
int flush(int filedes, char* addr, size_t len) {
    // Don't bother if there is no file backing
    if (filedes == -1 ) 
        return 0;

    // First flush the mmap regions syncronously
    int res = msync(addr, len, MS_SYNC);
    if (res == -1) return -1;

    res = fsync(filedes);
    if (res == -1) return -1;

    return 0;
}

