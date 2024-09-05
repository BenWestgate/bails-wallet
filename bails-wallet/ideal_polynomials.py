import random

from enum import Enum

class Encoding(Enum):
    """Enumeration type to list the various supported encodings."""
    CRC1 = 1 # x + 1
    CRC2 = 2 # x^2 + x + 1
    CRC3 = 3 # x^3 + x + 1
    CRC4 = 4 # x^4 + x + 1

def convertbits(data, frombits, tobits, pad=True):
    """General power-of-2 base conversion."""
    acc = 0
    bits = 0
    ret = []
    maxv = (1 << tobits) - 1
    max_acc = (1 << (frombits + tobits - 1)) - 1
    for value in data:
        if value < 0 or (value >> frombits):
            return None
        acc = ((acc << frombits) | value) & max_acc
        bits += frombits
        while bits >= tobits:
            bits -= tobits
            ret.append((acc >> bits) & maxv)
    if pad:
        if bits:
            ret.append((acc << (tobits - bits)) & maxv)
    elif bits >= frombits or ((acc << (tobits - bits)) & maxv):
        return None
    return ret

def bin_polymod(chk_len, data):
    """Internal function that computes the CRC checksum."""
    # Define the CRC polynomial (x^chk_len + x + 1)
    polynomial = (0b1 << chk_len) + 0b11
    crc = 0
    for bit in data:
        crc = (crc << 1) | int(bit) # Shift in the next bit
        # If the leftmost bit (MSB) is 1, XOR with the polynomial
        if crc & (0b1 << chk_len):
            crc ^= polynomial
    # Return the last chk_len bits as the CRC
    return crc & (2 ** chk_len - 1)

def bin_hrp_fp_expand(hrp, fp):
    """Expand HRP and fingerprint into values for crc computation."""
    return convertbits(fp + bytes(hrp,'utf'), 8, 1)

def bin_verify_crc(hrp, data, fp=b''):
    """Verify a CRC checksum given binary converted data characters."""
    # data: 5 bits threshold + 20 bits ID + 5 bits index + 128, 256 or 512 bit payload + crc padding to be divisible by 5
    #if len(data) % 5 or not 545 >= len(data) >= 160:
    #    return False
    payload_len = len(data) - 30
    chk_len = payload_len & 7
    if not chk_len: # No checksum bits, the payload is multiple of 40
        return None
    return bin_polymod(chk_len, bin_hrp_fp_expand(hrp, fp) + data) == 0

def bin_create_crc(hrp, data, fp=b''):
    """Compute the CRC checksum values given data and fingerprint."""
    chk_len = 5 - len(data) % 5
    values = bin_hrp_fp_expand(hrp, fp) + data
    polymod = bin_polymod(chk_len, values + [0] * chk_len)
    return convertbits([polymod], chk_len, 1)

def add_bit_errors(data, qty):
    #print(f"Original data:  {data}")
    # Convert binary string to integer
    for bit_flip in random.sample(range(len(data)), qty):
        # Generate a random bit position to flip the bit using XOR
        data[bit_flip] ^= 1
    # Convert back to binary string and preserve leading zeros
    corrupted_data = data
    #print(f"Corrupted data: {corrupted_data}")
    return corrupted_data


hrp = 'ms'

trials = 10000
error_qty = 3
errors_undetected = 0
seed_len = 256

for i in range(trials):
    fp = random.randbytes(4)
    id = convertbits(fp, 8, 1)[:20]
    seed = convertbits(random.randbytes(16), 8, 1)
    # threshold 2, share 's'
    bit_list = [0,1,0,1,0] + id + [1,0,0,0,0] + seed
    code_bits = bit_list + bin_create_crc(hrp, bit_list)
    error_bits = add_bit_errors(code_bits, error_qty)
    if bin_verify_crc(hrp, error_bits):
        errors_undetected += 1

print('my data')
print(bit_list)
print('the crc')
crc = bin_create_crc(hrp, bit_list, fp)
print(crc)
print('verifying code')
#crc[0] ^= 1
print(bin_verify_crc(hrp, bit_list + crc))
print('undetected error percent')
print(100 * errors_undetected/trials)

# Detects 1.5364% of single bit errors
# def checksum(data):
#    return '00'

# 49.2492% of double bit errors undetected
# 1.1291% of triple bit errors undetected
# 
#    sum = 0
#    for bit in data:
#        sum += int(bit)
#    msb = bin(sum % 2)[2:]
#    sum = 0
#    for bit in data[::2]:
#        sum += int(bit)
#    lsb = bin(sum % 2)[2:]
#    return msb + lsb

# 49.7229% of double bit errors undetected
# 1.1383% of triple bit errors undetected
# 48.4781% of quadruple bit errors undetected
#    sum = 0
#    for bit in data:
#        sum += int(bit)
#    return bin(sum % 4)[2:].zfill(2)

# Detects 72.2802% of single bit errors
#    data_bytes = int(data, 2).to_bytes(seed_len // 8, "big")
#    return bin(crc32(data_bytes))[2:].zfill(32)[:2]

# Detects 74.589%
#     data_bytes = int(data, 2).to_bytes(seed_len // 8, "big")
#    return bin(crc32(data_bytes))[2:].zfill(32)[4:6]
