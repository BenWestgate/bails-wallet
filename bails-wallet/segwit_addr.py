# Copyright (c) 2017, 2020 Pieter Wuille
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""Reference implementation for Bech32/Bech32m and segwit addresses."""


from enum import Enum

class Encoding(Enum):
    """Enumeration type to list the various supported encodings."""
    BECH32 = 1
    BECH32M = 2

CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
BECH32M_CONST = 0x2bc830a3

def bech32_polymod(values):
    """Internal function that computes the Bech32 checksum."""
    generator = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3]
    chk = 1
    for value in values:
        top = chk >> 25
        chk = (chk & 0x1ffffff) << 5 ^ value
        for i in range(5):
            chk ^= generator[i] if ((top >> i) & 1) else 0
    return chk


def bech32_hrp_expand(hrp):
    """Expand the HRP into values for checksum computation."""
    return [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]


def bech32_verify_checksum(hrp, data):
    """Verify a checksum given HRP and converted data characters."""
    const = bech32_polymod(bech32_hrp_expand(hrp) + data)
    if const == 1:
        return Encoding.BECH32
    if const == BECH32M_CONST:
        return Encoding.BECH32M
    return None

def bech32_create_checksum(hrp, data, spec):
    """Compute the checksum values given HRP and data."""
    values = bech32_hrp_expand(hrp) + data
    const = BECH32M_CONST if spec == Encoding.BECH32M else 1
    polymod = bech32_polymod(values + [0, 0, 0, 0, 0, 0]) ^ const
    return [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]


def bech32_encode(hrp, data, spec):
    """Compute a Bech32 string given HRP and data values."""
    combined = data + bech32_create_checksum(hrp, data, spec)
    return hrp + '1' + ''.join([CHARSET[d] for d in combined])

def bech32_decode(bech):
    """Validate a Bech32/Bech32m string, and determine HRP and data."""
    if ((any(ord(x) < 33 or ord(x) > 126 for x in bech)) or
            (bech.lower() != bech and bech.upper() != bech)):
        return (None, None, None)
    bech = bech.lower()
    pos = bech.rfind('1')
    if pos < 1 or pos + 7 > len(bech) or len(bech) > 90:
        return (None, None, None)
    if not all(x in CHARSET for x in bech[pos+1:]):
        return (None, None, None)
    hrp = bech[:pos]
    data = [CHARSET.find(x) for x in bech[pos+1:]]
    spec = bech32_verify_checksum(hrp, data)
    if spec is None:
        return (None, None, None)
    return (hrp, data[:-6], spec)

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


def decode(hrp, addr):
    """Decode a segwit address."""
    hrpgot, data, spec = bech32_decode(addr)
    if hrpgot != hrp:
        return (None, None)
    decoded = convertbits(data[1:], 5, 8, False)
    if decoded is None or len(decoded) < 2 or len(decoded) > 40:
        return (None, None)
    if data[0] > 16:
        return (None, None)
    if data[0] == 0 and len(decoded) != 20 and len(decoded) != 32:
        return (None, None)
    if data[0] == 0 and spec != Encoding.BECH32 or data[0] != 0 and spec != Encoding.BECH32M:
        return (None, None)
    return (data[0], decoded)


def encode(hrp, witver, witprog):
    """Encode a segwit address."""
    spec = Encoding.BECH32 if witver == 0 else Encoding.BECH32M
    ret = bech32_encode(hrp, [witver] + convertbits(witprog, 8, 5), spec)
    if decode(hrp, ret) == (None, None):
        return None
    return ret

import hmac
from hashlib import sha256
from bip32 import BIP32, utils
from bip32.utils import _pubkey_to_fingerprint

from secrets import token_bytes
import random
def add_errors(data, qty):
    ms32_corrupt_data = data
    error_locs = random.sample(range(0, len(data)), qty)
    for loc in error_locs:
        ms32_corrupt_data[loc] ^= random.randrange(1, 32)
    return ms32_corrupt_data
error_qty = 4
trials = 100000
errors_undetected = 0
pos = 0
def bech32_xor(data):
    xor = 0
    for value in data:
        xor ^= value
    return xor
for i in range(trials):
    data = random.randbytes(8)
    addr = encode('bc', 1, data)
    ms32_data = bech32_decode(addr)[1]
    #chk_two = bech32_create_checksum('bc', ms32_data, 1)
    chk_two = bech32_xor(ms32_data)
    ms32_corrupt_data = add_errors(ms32_data, error_qty)
    #chk_one = bech32_create_checksum('bc', ms32_corrupt_data, 1)
    chk_one = bech32_xor(ms32_corrupt_data)
    if chk_one == chk_two:
        errors_undetected += 1
print('undetected error rate')
print(100* errors_undetected/trials)

# 1 Error:

# pos 0 7%
# pos 1 0%
# pos 2 7%
# pos 3 0%
# pos 4 0%
# pos 5 0%

# 2 Errors:

# pos 0 2.7%
# pos 1 3.2%
# pos 2 2.8%
# pos 3 3.2%
# pos 4 3.2%
# pos 5 3.2%

# 3 Errors:

# pos 0 3.2%
# pos 1 3.2%
# pos 2 2.8%
# pos 3 3.2%
# pos 4 3.2%
# pos 5 3.2%



#print(bech32_encode('bc', [1] + ms32_corrupt_data, 1))
#print(encode('bc', 1, data))

exit()
def ms32_create_fingerprint_id(fp):
    """Converts the fingerprint to bech32 and truncates to length 4."""
    return

#master_pubkey = BIP32.from_seed(master_seed).get_pubkey_from_path("m")
#print(seed.get_extended_pubkey_from_path("m/0")[5:9])
master_seed = b'0123456789012345' # token_bytes(16)
print(master_seed)
fp = _pubkey_to_fingerprint(BIP32.from_seed(master_seed).pubkey)
print(fp)
print(fp.hex())
ms32_fp = "".join([CHARSET[d] for d in convertbits(fp, 8, 5)[:4]])
print(ms32_fp)
hrp = 'ms'
k = '2'
id = ms32_fp
index = 's'

shuffle_key = fp + bytes(hrp + k + id + index, 'utf')
print(shuffle_key)



exit()
bech32_hrp_expand(hrp) + [CHARSET.find(x.lower()) for x in k + id + index]

print(CHARSET.index('d'))
print(CHARSET.index('0'))
print(CHARSET.index('p'))
print(CHARSET.index('0'))
print(CHARSET.index('2'))
print(CHARSET.index('3'))
