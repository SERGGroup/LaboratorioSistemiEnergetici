import numpy as np
import multiprocessing.shared_memory as shm
from multiprocessing import Process


def worker(shared_name, shape, dtype):
    existing_shm = shm.SharedMemory(name=shared_name)
    array = np.ndarray(shape, dtype=dtype, buffer=existing_shm.buf)

    # Modify the shared array
    array += 10
    print("Modified array in worker:", array)


if __name__ == "__main__":
    # Create a shared memory block
    shape = (3, 3)  # Shape of the array
    dtype = np.float64  # Data type
    shared_mem = shm.SharedMemory(create=True, size=int(np.prod(shape) * np.dtype(dtype).itemsize))

    # Create the NumPy array using shared memory
    shared_array = np.ndarray(shape, dtype=dtype, buffer=shared_mem.buf)
    shared_array[:] = np.random.rand(*shape)  # Initialize with some data

    print("Initial array:", shared_array)

    # Start the worker process
    p = Process(target=worker, args=(shared_mem.name, shape, dtype))
    p.start()
    p.join()

    # Check modifications
    print("Array after worker process:", shared_array)

    # Cleanup
    shared_mem.close()
    shared_mem.unlink()
