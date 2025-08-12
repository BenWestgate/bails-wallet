

# Todo make it check the padding matches the CRC for "error detection mode"

from random import randbytes
seed = randbytes(32)
print(seed)
ms32 = convertbits(seed, 8, 5)
print(ms32)
corrupt_ms32 = ms32[:-1] + [ms32[-1] ^ 15]
print(corrupt_ms32)
data = convertbits(corrupt_ms32, 5, 8, False, False)
if data:
    print(data)
    print(bytes(data))