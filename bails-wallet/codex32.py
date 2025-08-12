#!/bin/python3
# Author: Leon Olsson Curr and Pearlwort Sneed <pearlwort@wpsoftware.net>
# License: BSD-3-Clause

"""Reference implementation for codex32/codexQR BIP32 seed backups."""


import hmac
from hashlib import sha512, sha256, scrypt
from bip32 import BIP32
from bip32.utils import _pubkey_to_fingerprint, _ripemd160
from secrets import token_bytes
from segwit_addr import bech32_hrp_expand
from enum import Enum


#from electrum.bip32 import BIP32Node


CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
BASE45_CHARSET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:"
MS32_CONST = 0x10CE0795C2FD1E62A
MS32_LONG_CONST = 0x43381E570BF4798AB26
bech32_inv = [
    0, 1, 20, 24, 10, 8, 12, 29, 5, 11, 4, 9, 6, 28, 26, 31,
    22, 18, 17, 23, 2, 25, 16, 19, 3, 21, 14, 30, 13, 7, 27, 15,
]


def ms32_polymod(values):
    GEN = [
        0x19DC500CE73FDE210,
        0x1BFAE00DEF77FE529,
        0x1FBD920FFFE7BEE52,
        0x1739640BDEEE3FDAD,
        0x07729A039CFC75F5A,
    ]
    residue = 0x23181B3
    for v in values:
        b = residue >> 60
        residue = (residue & 0x0FFFFFFFFFFFFFFF) << 5 ^ v
        for i in range(5):
            residue ^= GEN[i] if ((b >> i) & 1) else 0
    return residue


def ms32_verify_checksum(data):
    if len(data) >= 96:  # See Long codex32 Strings
        return ms32_verify_long_checksum(data)
    if len(data) <= 93:
        return ms32_polymod(data) == MS32_CONST
    return False


def ms32_create_checksum(data):
    if len(data) > 80:  # See Long codex32 Strings
        return ms32_create_long_checksum(data)
    values = data
    polymod = ms32_polymod(values + [0] * 13) ^ MS32_CONST
    return [(polymod >> 5 * (12 - i)) & 31 for i in range(13)]


def ms32_long_polymod(values):
    GEN = [
        0x3D59D273535EA62D897,
        0x7A9BECB6361C6C51507,
        0x543F9B7E6C38D8A2A0E,
        0x0C577EAECCF1990D13C,
        0x1887F74F8DC71B10651,
    ]
    residue = 0x23181B3
    for v in values:
        b = residue >> 70
        residue = (residue & 0x3FFFFFFFFFFFFFFFFF) << 5 ^ v
        for i in range(5):
            residue ^= GEN[i] if ((b >> i) & 1) else 0
    return residue


def ms32_verify_long_checksum(data):
    return ms32_long_polymod(data) == MS32_LONG_CONST


def ms32_create_long_checksum(data):
    values = data
    polymod = ms32_long_polymod(values + [0] * 15) ^ MS32_LONG_CONST
    return [(polymod >> 5 * (14 - i)) & 31 for i in range(15)]


def bech32_mul(a, b):
    res = 0
    for i in range(5):
        res ^= a if ((b >> i) & 1) else 0
        a *= 2
        a ^= 41 if (32 <= a) else 0
    return res


# noinspection PyPep8
def bech32_lagrange(l, x):
    n = 1
    c = []
    for i in l:
        n = bech32_mul(n, i ^ x)
        m = 1
        for j in l:
            m = bech32_mul(m, (x if i == j else i) ^ j)
        c.append(m)
    return [bech32_mul(n, bech32_inv[i]) for i in c]


def ms32_interpolate(l, x):
#    print(l)
    w = bech32_lagrange([s[5] for s in l], x)
    res = []
    for i in range(len(l[0])):
        n = 0
        for j in range(len(l)):
            n ^= bech32_mul(w[j], l[j][i])
        res.append(n)
    return res


def ms32_recover(l):
    return ms32_interpolate(l, 16)


# Copyright (c) 2024 Ben Westgate
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


class Encoding(Enum):
    """Enumeration type to list the various supported encodings."""
    CODEX32_SHARE = 0 # Codex32 share
    CODEX32_SECRET = 1 # Codex32 secret
    CODEXQR_SHARE = 2 # CodexQR share (compatible with codex32)
    CODEXQR_SECRET = 3 # CodexQR secret (compatible with codex32)

class Binary:
    def __init__(self, bin_data: list):
        self.bin_data = bin_data

    @classmethod
    def from_ms32(cls, ms32str):
        MS32.decode(ms32str)

def bin_crc(crc_len, values):
    """Internal function that computes the codexQR CRC checksum."""
    if crc_len < 5: # Codex32 string padding
        # Define the CRC polynomial (x^crc_len + x + 1) optimal for 1-4
        polynomial = (0b1 << crc_len) | 0b11
    elif crc_len == 7: # 21x21 CodexQR share index and padding
        # Define the CRC-7 0x5b => factors	x^7+x^5+x^4+x^2+x+1 
        polynomial = 0b10110111
        # when a symbol errors occurs, odds 16:15 it is odd parity
        # this checksum detects all odd errors, so slightly outperforms
        # when there are 9 errors which codex32 checksum can't detect.
    crc = 0
    for bit in values:
        crc = (crc << 1) | int(bit) # Shift in the next bit
        # If the leftmost bit (MSB) is 1, XOR with the polynomial
        if crc & (0b1 << crc_len):
            crc ^= polynomial
    # Return the last crc_len bits as the CRC
    return crc & (2 ** crc_len - 1)


def convertbits(data, frombits, tobits, pad=True, verify=False):
    """General power-of-2 base conversion with CRC padding."""
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
    if pad and bits:
        crc_len = tobits - bits
        crc = bin_crc(crc_len, convertbits(data, frombits, 1) + crc_len * [0])
        ret.append(((acc << crc_len) + crc) & maxv)
    elif bits >= frombits:
        return None
    elif verify and bin_crc(bits, convertbits(data, frombits, 1)):
        return None
    return ret


class MS32:
    """Operations on MS32 encoded data."""
    def __init__(self, data: list, chk=True):
        self.data = data
        self.chk = chk

    @classmethod
    def decode(cls, ms32str):
        """Validate an MS32 string, and determine data."""
        if ((any(ord(x) < 33 or ord(x) > 126 for x in ms32str)) or
            (ms32str.lower() != ms32str and ms32str.upper() != ms32str)):
            raise Exception("Parsing failed: MUST be entirely uppercase or entirely lowercase")
        ms32str = ms32str.lower()
        pos = ms32str.rfind('1')
        if pos + 2 > len(ms32str):
            raise Exception("Parsing failed: Data part is too short, no threshold parameter found")
        if not all(x in '?' + CHARSET for x in ms32str[pos+1:]):
            raise Exception('Parsing failed: Data part should consist only of alphanumeric characters excluding "1", "b", "i", and "o"')
        return MS32([CHARSET.find(x) for x in ms32str[pos+1:]])
    
    @classmethod
    def from_binary(cls, bin_data, chk=False, pad=False):
        """Validate a binary string, and determine data."""
        if any(x not in [0, 1] for x in bin_data):
            raise Exception("Binary data must be a list of 0s and 1s")
        #if len(bin_data) % 5:
        #    raise Exception("Binary data length must be a multiple of 5")
        return MS32(convertbits(bin_data, 1, 5, pad), chk)


    def encode(self):
        """Compute codex32 string data characters given data values."""
        if not self.data:
            return ""
        combined = self.data
        combined += ms32_create_checksum(self.data) if self.chk else []
        return "".join([CHARSET[d] if d >= 0 else '?' for d in combined])
    
    def bin_encode(self):
        """Compute bit list data given data values"""
        return convertbits(self.data, 5, 1)


class Codex32:
    """Represents decoded codex32 parts."""
    def __init__(self, hrp: str, threshold: int, id: str, share_idx: str,
                 payload: list, spec: Encoding):
        self.hrp = hrp  # "ms"
        self.threshold = threshold  # 0, or 2-9
        # Four valid bech32 characters which identify this complete codex32 secret
        self.id = id.strip('?')
        # Valid bech32 character identifying this share of the secret, or `s` for unshared
        self.share_idx = share_idx
        # The MS32 data payload
        self.payload = payload
        # The actual data payload bytes
        self.payload_bytes = convertbits(payload, 5, 8, False)
        # Is this a share, or a secret?
        self.spec = spec 
        # The header as a string
        self.header = str(threshold) + id + share_idx

    def parse_header(codex):
        """Parse codex32 string to determine HRP, t, ID, index and data."""
        data = MS32.decode(codex).data
        codex = codex.lower()
        pos = codex.rfind('1')
        hrp = codex[:pos] if pos > 0 else ''
        t = codex[pos + 1]
        if not t.isdigit():
            raise Exception('Parsing failed: The threshold parameter MUST be a single digit between "2" and "9", or the digit "0"')
        id = codex[pos + 2:min(pos + 6, len(codex))] if len(codex) > pos + 2 else ''
        share_idx = codex[pos + 6] if len(codex) > pos + 6 else 's' if t == '0' else ''
        if t == '0' and share_idx not in 's' '?' '':
            raise Exception('Parsing failed: The threshold parameter is "0" but the share index is not "s"')
        data = [CHARSET.find(x) for x in codex[pos+1:]]
        return hrp, int(t), id, share_idx, data

    @classmethod
    def decode(cls, codex: str, hrp='ms'):
        """Decode a codex32 string and return a Codex32 instance."""
        try:
            hrpgot, threshold, id, index, data = cls.parse_header(codex)
        except Exception as e:
            raise e
        
        if hrp and hrpgot != hrp:
            raise Exception("Decoding failed: HRP does not match")
        if len(data) < 45 or len(data) > 124:
            raise Exception("Decoding failed: Invalid length")
        if not ms32_verify_checksum(data):
            raise Exception("Decoding failed: Invalid checksum")
        
        payload = data[6:-13 if len(data) < 96 else -15]
        spec = Encoding.CODEX32_SHARE if index != 's' else Encoding.CODEX32_SECRET
        
        codex32_instance = Codex32(
            hrp,
            threshold,
            id,
            index,
            payload,
            spec
        )
        return codex32_instance
    
    def get_fp_id(self): # TODO delete this if not used elsewhere
        """Compute the BIP32 fingerprint in bytes."""
        # TODO change this to use the new method I added to BIP32 library
        fp = _pubkey_to_fingerprint(BIP32.from_seed(self.payload).pubkey)
        return convertbits(fp, 8, 5)

    def encode(self):
        """Encode a codex32 string with or without codexQR support."""
        if self.share_idx == 's' and len(self.id) < 4:
            # fill the id with the BIP32 fingerprint
            fp = _pubkey_to_fingerprint(BIP32.from_seed(self.payload).pubkey)
            self.id += MS32(convertbits(fp, 8, 5)).encode()[len(self.id):4]
        header = MS32.decode(str(self.threshold) + self.id + self.share_idx).data
        ret = self.hrp + '1' + MS32(header + self.payload).encode()
        try: self.decode(self, ret, self.hrp)
        except: return None
        return ret

# Example usage:
codex32_instance = Codex32(
    "ms",
    2,
    "test",
    "q",
    b"1234567812345678",
    Encoding.CODEX32_SHARE
)

class CodexQR:
    """Represents decoded compactQR parts."""
    def __init__(self, threshold: int, id: str, share_idx='', payload=b'', spec=Encoding.CODEXQR_SHARE):
        # Shrink header into lossy values for CompactCodexQR support.
        self.id_len = 10 if threshold == 3 else 5 if threshold else 2
        if threshold > 8:
            raise ValueError('CodexQR supports thresholds 0 and 2-8')
        else:
            self.threshold = threshold
        threshold -= 1 if threshold else 0
        self.bin_threshold = convertbits([threshold], 3, 1)
        self.id = id[:self.id_len // 5]
        self.bin_id = MS32.decode(id).bin_encode()[:self.id_len]
        self.payload = convertbits(payload, 8, 1)
        self.share_idx = convertbits([CHARSET.find(share_idx)], 5, 1)
        # Is this codexQR compatible?

    @classmethod
    def from_header(cls, ms32str):
        _, threshold, id, share_idx, _ = Codex32.parse_header(ms32str)
        return CodexQR(threshold, id, share_idx)

    @classmethod
    def from_codex32str(cls, codex32str: str, hrp=''):
        """Instantiate a CodexQR from a codex32 string."""

        codex32 = Codex32.decode(codex32str, hrp)
        params = codex32.threshold, codex32.id, codex32.share_idx, codex32.payload_bytes
        codexqr = CodexQR(params)
        # Verify codexQR-compatible index and padding given header and data
        if len(codex32.payload) == 26 and codex32.threshold < 9: # Compact CodexQR reqs
            if codex32.share_idx == 's' and convertbits(codex32.payload, 5, 8, False, True):
                spec = Encoding.CODEXQR_SECRET
            elif codex32.share_idx == codexqr.qr_idx():
                spec = Encoding.CODEXQR_SHARE
            else:
                raise Exception('CodexQR incompatible: The share index and padding did not validate')
        else:
            raise Exception('CodexQR incompatible: Only 128-bit codex32 strings with threshold 0 or 2-8 have a compact encoding')
        return CodexQR(params.add(spec))

    def tiny_header(self):
        return self.bin_threshold + self.bin_id 

    def polymod(self):
        values = self.tiny_header() + self.payload
        return bin_crc(7, values + [0] * 7)

    def qr_idx(self):
        """Compute index and padding given header and binary data."""
        return CHARSET[self.polymod() & 31]
    
    def padded_payload(self):
        return self.payload + convertbits([self.polymod() >> 5], 2, 1)

    def lossy_encode(self): # TODO rename me
        """Encode a partial codex32 string from codexQR."""
        hrp = 'ms1' # only supported HRP
        ms32str = str(self.threshold)
        ms32str += MS32.from_binary(self.bin_id).encode().ljust(4, '?')
        ms32str += self.qr_idx() + MS32.from_binary(self.padded_payload()).encode()
        return hrp + ms32str + '?' * 13 # add erasures for chksum
        
    def encode(self): # TODO another system must translate this to QRdata
        # TODO another system will have to translate this into QR data
        # using the cut offs of each QR mode's data length to assign
        # all possible seeds and 
        return int.from_bytes(bytes(convertbits(self.tiny_header() + self.payload, 1, 8)))


    def is_compatible(self):
        for pad in [0, 0], [0, 1], [1, 0], [1, 1]:
            if bin_crc(7, self.tiny_header() + self.qr_idx + self.payload + pad) == 0:
                return True
        return False

from random import randbytes

print(CodexQR(0,'me', payload=randbytes(16)).lossy_encode())

def codex32_secret(hrp: str, id: str, threshold: int, seed: bytes):
    """Encode a seed into codex32 secret format."""
    payload = convertbits(seed, 8, 5) # adds CRC padding
    return Codex32(hrp, threshold, id, 's', payload, Encoding.CODEX32_SECRET)


def get_salt(header, available_indexes, codexqr=False, seedlen=16):
    """Create unique salt from codex32 header and available indexes."""
    hrp, t, id, index, _ = Codex32.parse_header(header)
    salt = seedlen.to_bytes(1)
    if codexqr: # no hrp, compact header, wont collide
        salt += bytes(CodexQR(t, id, index).tiny_header)
    else: # TODO May have to make 's' CodexQRs switch to t == 0
        salt += (hrp + '1' + t + id.ljust(4)).encode()
    salt += index.ljust(1).encode()
    salt += available_indexes.ljust(32).encode()
    salt += codexqr.to_bytes(1)
    return salt

"""print(bin_tiny_header('0q'))
print(bin_tiny_header('0s'))
print(bin_tiny_header('3????s'))
print(bin_tiny_header('3s???s'))


#print(parse_header(header))
print(get_salt('ms10q', CHARSET.replace('t',''), codexqr=True, seedlen=16))
print(get_salt('ms10s', CHARSET.replace('t',''), codexqr=True, seedlen=16))
print(get_salt('ms10?', CHARSET.replace('t',''), codexqr=True, seedlen=16))
"""
"""header = 'ms1'
count = 0
all_headers = set()
#for codexqr in True, False:
codexqr = True
for i in range(0,9):
        if i == 1:
            continue
        b = ''
        for a in [''] + ['?'] + list(CHARSET):
            if not i and CHARSET.find(a) % 8:
                continue
            header = str(i) + a
            if i == 3 and a:
                for b in [''] + ['?'] + list(CHARSET):
                    header = str(i) + a + b
                    new = get_salt('ms1' + header, CHARSET, codexqr=codexqr)
                    if new in all_headers:
                        print('ms1' + header)
                        print(new)
                    all_headers.add(new)
                    count += 1
            else:
                new = get_salt('ms1' + header, CHARSET, codexqr=codexqr)
                if new in all_headers:
                    print('ms1' + header)
                    print(new)
                all_headers.add(new)
                count += 1
print(len(all_headers))
print(count)
exit()
"""

# Note the passphrase can be provided as entropy with a shrunk header 
# and all indexes available except 's' for codexqr KDF share gen
def generate_share(entropy, header, available_indexes,
                    seedlen=16, codexqr=True):
    """Generate a codex32 string from header and entropy."""
    counter = 0  # Counter to track current position in the keystream.
    password = entropy
    salt = get_salt(header, available_indexes, codexqr, seedlen)
    dk = scrypt(password, salt=salt, n=2 ** 20, r=8, p=1, maxmem=1025 ** 3,
                 dklen=128)
    hrp, t, id, index, _ = Codex32.parse_header(header)
    if index in available_indexes:
        return Codex32(hrp, t, id, index, dk[:seedlen]).encode
    while index not in available_indexes:
        digest = hmac.digest(dk, counter.to_bytes(8), 'sha512')[:seedlen]
        counter += 1 # TODO may need to break if encode returns None
        try: 
            index = CodexQR('ms', t, id, '', digest).qr_idx # TODO test this doesn't give output w/o enough id
            payload = MS32.from_binary(CodexQR('ms', t, id, '', digest).padded_payload)
        except:
            return None
    return Codex32('ms', t, id, index, payload.data).encode


def kdf_share(passphrase, header, seedlen=16, codexqr=True):
    """Derive an MS32 share from a passphrase and a codex32 header"""
    available_indexes = CHARSET.replace('s','') # every index free but s
    entropy = passphrase.encode()
    return generate_share(entropy, header, available_indexes, seedlen, codexqr)

def validate_share_set(existing_shares, codexqr=False):
    """Validate a codex32 share set and return list of MS32 shares"""
    prefix = {}
    used_indexes = {}
    seedlen = {}
    for codex in existing_shares:
        header, data = decode('ms', codex, codexqr)
        if not header:
            return None
        k = int(header[0]) if int(header[0]) else 1
        # if k != len(existing_shares):
        #     return None
        prefix.add(header[:-1])
        used_indexes.add(header[-1])
        seedlen.add(len(data))
    if len(prefix) != 1 or len(used_indexes) != k or len(seedlen) != 1:
        return None
    free_indexes = list(CHARSET)
    for index in used_indexes:
        free_indexes.remove(index)
    return [ms32_decode(codex)[2] for codex in existing_shares], free_indexes, seedlen


"""def fresh_master_seed(seedlen, t):
    for i in range(t):
"""


def create_index_and_payload(header, entropy, seedlen=16,
                             free_indexes=CHARSET.replace("s", "")):
    """Compute the checksum index values given FP and seed"""
    counter = 0  # Counter to track current position in the keystream.
    digest = b""  # Storage for HMAC-SHA512 digest
    index = ''
    while CHARSET[index] not in free_indexes:
        
        
        data = digest[:seedlen]
        
    return CHARSET[index], seed, free_indexes.replace(CHARSET[index], ''), counter


def kdf_share(passphrase, codex32_str):
    """
    Derive codex32 share from a passphrase and the codex32 header.

    Args:
        passphrase: a seed backup passphrase as a string
        codex32_str: a valid codex32 string to derive kdf share with.

    Returns:
        the string encoded kdf_share

    """
    k, ident, _, payload = decode("ms", codex32_str)
    password = bytes(passphrase, "utf")
    salt = len(payload).to_bytes(1) + bytes(codex32_str[:8], "utf")
    derived_key = hashlib.scrypt(password, salt=salt, n=2 ** 20, r=8, p=1,
                                 maxmem=1025 ** 3, dklen=128)
    passphrase_index_seed = hmac.digest(
        derived_key, b"Passphrase share index seed", "sha512")[:32]
    share_index = shuffle_indices(
        passphrase_index_seed, list(CHARSET.replace("s", ""))).pop()
    payload = hmac.digest(derived_key, b"Passphrase share payload with index "
                          + bytes(share_index, "utf"), "sha512")[:len(payload)]
    return encode("ms", k, ident, share_index, payload)

# If an ID is provided, generate k shares first, then the secret.
# If an ID is not provided, generate the secret first, then k-1 shares.
# This way we do not have to relabel them.

def generate_shares(n, k, app_entropy, user_entropy=b'', id='', existing_shares={}, codexqr=True):
    """Generate n shares total from existing shares."""
    if n > 31:
        return None
    valid_shares, free_indexes, seedlen = validate_share_set(existing_shares, codexqr)
    counter = 0
    compatible_shares = []
    generated_list = []
    generated = []
    valid_shares = []
    
    key_identifier = hash_160(master_key.eckey.get_public_key_bytes())
    entropy_header = (seedlength.to_bytes(length=1, byteorder="big")
                      + bytes("ms" + k + ident + "s", "utf") + key_identifier)
    salt = entropy_header + bytes(CHARSET[n] + user_entropy, "utf")
    # This is equivalent to hmac-sha512(b"Bitcoin seed", master_seed).
    password = master_key.eckey.get_secret_bytes() + master_key.chaincode
    # If scrypt absent visit OWASP Password Storage or use pbkdf2_hmac(
    # 'sha512', password, salt, iterations=210_000 * 64, dklen=128)
    derived_key = scrypt(
        password, salt=salt, n=2 ** 20, r=8, p=1, maxmem=1025 ** 3, dklen=128)

    
    while len(valid_shares) < n:
        generated.clear()
        for _ in range(int(k)):
            ms32_data = [-1] * 6
            while ms32_data[5] not in free_indexes:
                counter += 1
                seed = randbytes(16)
                bin_seed = convertbits(seed, 8, 1)
                bin_data = bin_seed + bin_create_crc(7,convertbits(seed,8,1))
                ms32_data = [ms32_t] + [31,31,31,31] + convertbits(bin_data, 1, 5)
            free_indexes.remove(ms32_data[5])
            if ms32_data[5] == 16:
                ms32_secret = ms32_data
            valid_shares.append(ms32_data)
            generated.append(ms32_data)
        for index in free_indexes:
            ms32_derived = ms32_interpolate(generated[:int(t)], index)
            if ms32_derived[5] == 16:
                ms32_secret = ms32_derived
            else:
                bin_data = convertbits(ms32_derived[5:], 5, 1)
                if bin_verify_crc(7,bin_data):
                    compatible_shares += [ms32_derived]
        last_counter = counter
        counter += 1

    valid_shares = generated_list + compatible_shares

    

    return new_shares
    ms32_t = CHARSET.index(t)
    n = 10
    counter = 0
    compatible_shares = []
    generated_list = []
    generated = []
    compatible = []
    passing = []

    while len(valid_shares) < n:
        free_indexes = list(range(32))
        passing.clear()
        generated.clear()
        ms32_secret = None
        for i in range(int(k)):
            ms32_data = [-1] * 6
            while ms32_data[5] not in free_indexes:
                counter += 1
                seed = randbytes(16)
                bin_seed = convertbits(seed, 8, 1)
                bin_data = bin_seed + bin_create_crc(7,convertbits(seed,8,1))
                ms32_data = [ms32_t] + [31,31,31,31] + convertbits(bin_data, 1, 5)
            free_indexes.remove(ms32_data[5])
            if ms32_data[5] == 16:
                ms32_secret = ms32_data
            passing.append(ms32_data)
            generated.append(ms32_data)
        for index in free_indexes:
            ms32_derived = ms32_interpolate(generated[:int(t)], index)
            if ms32_derived[5] == 16:
                ms32_secret = ms32_derived
            else:
                bin_data = convertbits(ms32_derived[5:], 5, 1)
                if bin_verify_crc(7,bin_data):
                    compatible_shares += [ms32_derived]
        last_counter = counter
        counter += 1

    passing = generated_list + compatible_shares
    print('')
    if ms32_secret:
        print('compatible secret found')
        print(ms32_encode(ms32_secret)[5:32])
    else:
        print('non-compatible derived secret')
        print(ms32_encode(ms32_interpolate(passing[:int(t)]), 16))

    generated += [ms32_encode(codex)[5:32] for codex in generated_list]
    compatible += [ms32_encode(codex)[5:32] for codex in compatible_shares]
   


def validate_codex32_string_list(string_list, k_must_equal_list_length=True):
    """
    Validate uniform threshold, identifier, length, and unique indices.

    :param string_list: List of codex32 strings to be validated.
    :param k_must_equal_list_length: Flag for k must match list length.
    :return: List of decoded data if valid, else None.
    """
    ret = []
    for string in string_list:
        ret += [ms32_decode(string)[1]]
    return ret


def recover_master_seed(share_list):
    """
    Derive master seed from a list of threshold valid codex32 shares.

    :param share_list: List of codex32 shares to recover master seed.
    :return: The master seed as bytes, or None if share set is invalid.
    """
    ms32_share_list = validate_codex32_string_list(share_list)
    if not ms32_share_list:
        return None
    return bytes(convertbits(ms32_recover(ms32_share_list)[6:], 5, 8, False))


def derive_share(string_list, fresh_share_index="s"):
    """
    Derive an additional share from a valid codex32 string set.

    :param string_list: List of codex32 strings to derive from.
    :param fresh_share_index: New index character to derive share at.
    :return: Derived codex32 share or None if derivation fails.
    """
    ms32_share_index = CHARSET.find(fresh_share_index.lower())
    if ms32_share_index < 0:
        return None
    l = validate_codex32_string_list(string_list)
    return ms32_interpolate(l, ms32_share_index)


def relabel_codex32_strings(hrp, header, string_list, fp=b''):
    """Update headers on codex32 strings and recreate the checksums."""
    t = header[0]
    id = header[1:4]
    new_strings = []
    for codex32_string in string_list:
        data = decode(hrp, codex32_string, fp)
        new_strings.append(encode(hrp,))
    return new_strings


#def bin_encode_codexqr(header, entropy):
    """Compute CompactCodexQR data given header and entropy values."""
    bin_entropy = convertbits(entropy, 8, 1)
    combined = bin_entropy + bin_create_codexqr_padding(header, bin_entropy)
    return CodexQR.from_header(header).tiny_header + combined[5:5 + len(bin_entropy)]


def bin_decode_codexqr(data):
    bin_header = data[:29]
    t = '0' if data[:4] == [0] * 4 else str(convertbits(data[:4], 4, 1)[0] + 1)
    header = t + [CHARSET.find(x) for x in convertbits(bin_header[4:], 1, 5)]
    if bin_verify_codexqr_padding(header, data[24:]):
        return (header, convertbits(data[29:], 1, 8, False))
    return (None, None)


def shuffle_indexes(index_seed, indices=CHARSET.replace("s", "")):
    """Shuffle indexes deterministically with index_seed."""
    counter = 0  # Counter to track current position in the keystream.
    digest = b""  # Storage for HMAC-SHA256 digest
    value = b""  # Storage for the assigned random value
    assigned_values = {}  # Dictionary to store characters and values.
    for char in indices:
        # Generates a new random value when there's a collision.
        while value in assigned_values.values() or not value:
            if not counter % 32:  # Generate new digest every 32 bytes.
                digest = hmac.digest(
                    index_seed, (counter // 32).to_bytes(8, "big"), sha256)
            value = digest[counter % 32]  # rand byte
            counter += 1
        assigned_values[char] = value
    return sorted(assigned_values.keys(), key=lambda x: assigned_values[x])


def shuffle_indexes(index_seed, indices=CHARSET.replace("s", "")):
    """Shuffle indexes deterministically with index_seed."""
    counter = 0  # Counter to track current position in the keystream.
    digest = b""  # Storage for HMAC-SHA256 digest
    value = b""  # Storage for the assigned random value
    assigned_values = {}  # Dictionary to store characters and values.
    for char in indices:
        # Generates a new random value when there's a collision.
        while value in assigned_values.values() or not value:
            if not counter % 32:  # Generate new digest every 32 bytes.
                digest = hmac.digest(
                    index_seed, (counter // 32).to_bytes(8, "big"), sha256)
            value = digest[counter % 32]  # rand byte
            counter += 1
        assigned_values[char] = value
    return sorted(assigned_values.keys(), key=lambda x: assigned_values[x])


def _validate_codex32_string_list(string_list, k_must_equal_list_length=True):
    """
    Validate uniform threshold, identifier, length, and unique indices.

    :param string_list: List of codex32 strings to be validated.
    :param k_must_equal_list_length: Flag for k must match list length.
    :return: List of decoded data if valid, else None.
    """
    list_len = len(string_list)
    headers = set()
    share_indices = set()
    lengths = set()

    for codex32_string in string_list:
        headers.add(tuple(decode("ms", codex32_string)[:2]))
        share_indices.add(decode("ms", codex32_string)[2])
        lengths.add(len(codex32_string))
        if len(headers) > 1 or len(lengths) > 1:
            return None

    if (k_must_equal_list_length and int(headers.pop()[0]) != list_len
            or len(share_indices) < list_len):
        return None

    return [ms32_decode(codex32_string)[1] for codex32_string in string_list]


def recover_master_seed(share_list):
    """
    Derive master seed from a list of threshold valid codex32 shares.

    :param share_list: List of codex32 shares to recover master seed.
    :return: The master seed as bytes, or None if share set is invalid.
    """
    ms32_share_list = validate_codex32_string_list(share_list)
    if not ms32_share_list:
        return None
    return bytes(convertbits(ms32_recover(ms32_share_list)[6:], 5, 8, False))


def _derive_share(string_list, fresh_share_index="s"):
    """
    Derive an additional share from a valid codex32 string set.

    :param string_list: List of codex32 strings to derive from.
    :param fresh_share_index: New index character to derive share at.
    :return: Derived codex32 share or None if derivation fails.
    """
    ms32_share_index = CHARSET.find(fresh_share_index.lower())
    if ms32_share_index < 0:
        return None
    return ms32_encode("ms", ms32_interpolate(
        validate_codex32_string_list(string_list), ms32_share_index))


def ms32_fingerprint(seed):
    """
    Calculate and convert the BIP32 fingerprint of a seed to MS32.

    :param seed: The master seed used to derive the fingerprint.
    :return: List of 4 base32 integers representing the fingerprint.
    """
    return convertbits(BIP32Node.from_rootseed(
        seed, xtype="standard").calc_fingerprint_of_this_node(), 8, 5)[:4]


def relabel_codex32_strings(hrp, header, string_list):
    """
    Change the k and ident on a list of codex32 strings.

    :param hrp: Human-readable part of the codex32 strings.
    :param string_list: List of codex32 strings to be relabeled.
    :param new_k: New threshold parameter as a string, if provided.
    :param new_id: New identifier as a string, if provided.
    :return: List of relabeled codex32 strings.
    """
    new_strings = []
    for codex32_string in string_list:
        decoded = decode(hrp, codex32_string)
        new_k = k if not new_k else new_k
        new_id = ident if not new_id else new_id
        new_strings.append(encode(hrp, new_k, new_id, share_index, decoded))
    return new_strings

def generate_shares(master_key="", user_entropy="", n=31, k="2", ident="NOID",
                    seedlength=16, existing_codex32_strings=[]):
    """
    Generate new codex32 shares from provided or derived entropy.

    :param master_key: BIP32 extended private master key from bitcoind.
    :param user_entropy: User-provided entropy for improved security.
    :param n: Total number of codex32 shares to generate (default: 31).
    :param k: Threshold parameter (default: 2).
    :param ident: Identifier (4 bech32 characters) or 'NOID' (default).
    :param seedlength: Length of seed (16 to 64 bytes, default: 16).
    :param existing_codex32_strings: List of existing codex32 strings.
    :return: Tuple: master_seed (bytes), list of new codex32 shares.
    """
    master_seed = b""
    if existing_codex32_strings is None:
        existing_codex32_strings = []
    new_shares = []
    num_strings = len(existing_codex32_strings)
    if (not validate_codex32_string_list(existing_codex32_strings, False)
            and existing_codex32_strings):
        return None
    available_indices = list(CHARSET)
    for string in existing_codex32_strings:
        k, ident, share_index, payload = decode("ms", string)
        available_indices.remove(share_index)
        if share_index == "s":
            master_seed = payload
        seedlength = len(payload)

    if num_strings == int(k) and not master_seed:
        master_seed = recover_master_seed(existing_codex32_strings)
    if master_seed:
        master_key = BIP32Node.from_rootseed(master_seed, xtype="standard")
    elif master_key:
        master_key = BIP32Node.from_xkey(master_key)
    else:
        return None
    key_identifier = hash_160(master_key.eckey.get_public_key_bytes())
    entropy_header = (seedlength.to_bytes(length=1, byteorder="big")
                      + bytes("ms" + k + ident + "s", "utf") + key_identifier)
    salt = entropy_header + bytes(CHARSET[n] + user_entropy, "utf")
    # This is equivalent to hmac-sha512(b"Bitcoin seed", master_seed).
    password = master_key.eckey.get_secret_bytes() + master_key.chaincode
    # If scrypt absent visit OWASP Password Storage or use pbkdf2_hmac(
    # 'sha512', password, salt, iterations=210_000 * 64, dklen=128)
    derived_key = scrypt(
        password, salt=salt, n=2 ** 20, r=8, p=1, maxmem=1025 ** 3, dklen=128)
    index_seed = hmac.digest(derived_key, b"Index seed", "sha512")[:32]
    available_indices.remove("s")
    available_indices = shuffle_indices(index_seed, available_indices)
    tmp_id = "temp" if ident == "NOID" else ident

    # Generate new shares, if necessary, to reach a threshold.
    for i in range(num_strings, int(k)):
        share_index = available_indices.pop()
        info = bytes("Share payload with index: " + share_index, "utf")
        payload = hmac.digest(derived_key, info, "sha512")[:seedlength]
        new_shares.append(encode("ms", k, tmp_id, share_index, payload))
    existing_codex32_strings.extend(new_shares)
    # Relabel existing codex32 strings, if necessary, with default ID.
    if tmp_id == "temp":
        master_seed = recover_master_seed(existing_codex32_strings)
        ident = "".join([CHARSET[d] for d in ms32_fingerprint(master_seed)])
        existing_codex32_strings = relabel_codex32_strings(
            "ms", existing_codex32_strings, k, ident)
    # Derive new shares using ms32_interpolate.
    for i in range(int(k), n):
        fresh_share_index = available_indices.pop()
        new_share = derive_share(existing_codex32_strings, fresh_share_index)
        new_shares.append(new_share)

    return master_seed, new_shares


def regenerate_shares(existing_codex32_strings, unique_string,
                      monotonic_counter, n=31, new_id=""):
    """
    Regenerate fresh shares for an existing master seed & update ident.

    :param existing_codex32_strings: List of codex32 strings to reuse.
    :param unique_string: Unique string for entropy.
    :param monotonic_counter: Hardware or app monotonic counter value.
    :param n: Number of shares to generate, default is 31.
    :param new_id: New identifier, if provided.
    :return: List of regenerated codex32 shares.
    """
    master_seed, new_shares = generate_shares(
        user_entropy=unique_string + f"{monotonic_counter:016x}", n=n,
        existing_codex32_strings=existing_codex32_strings)
    k, ident, _, _ = decode("ms", new_shares[0])
    if not new_id or new_id != ident:
        new_id = encrypt_fingerprint(master_seed, k, unique_string)
    return relabel_codex32_strings("ms", new_shares, new_id=new_id)


def decrypt_ident(codex32_string, unique_string=""):
    """
    Decrypt a codex32 string identifier ciphertext using unique string.

    :param codex32_string: Codex32 string with an encrypted identifier.
    :param unique_string: Optional unique string encryption password.
    :return: Tuple with decrypted identifier (hex and MS32 string).
    """
    k, ident, _, data = decode("ms", codex32_string)
    enc_key = ident_encryption_key(data, k, unique_string)
    ciphertext = [CHARSET.find(x) for x in ident]
    plaintext = [x ^ y for x, y in zip(ciphertext, enc_key)]
    return bytes(convertbits(plaintext, 5, 8)).hex()[:5], "".join(
        [CHARSET[d] for d in plaintext])


def shuffle_indexes(index_seed, indices=CHARSET.replace("s", "")):
    """Shuffle indices deterministically with index_seed: HMAC-SHA256.

    Args:
        index_seed (bytes): The seed used for deterministic shuffling.
        indices (str): Characters to be shuffled.

    Returns:
        list: Shuffled characters sorted based on assigned values.

    Provided only as a reference in case ChaCha20 is unavailable.
    """
    counter = 0  # Counter to track current position in the keystream.
    digest = b""  # Storage for HMAC-SHA256 digest
    value = b""  # Storage for the assigned random value
    assigned_values = {}  # Dictionary to store characters and values.
    for char in indices:
        # Generates a new random value when there's a collision.
        while value in assigned_values.values() or not value:
            if not counter % 32:  # Generate new digest every 32 bytes.
                digest = hmac.digest(
                    index_seed, (counter // 32).to_bytes(8, "big"), sha256)
            value = digest[counter % 32]  # rand byte
            counter += 1
        assigned_values[char] = value
    return sorted(assigned_values.keys(), key=lambda x: assigned_values[x])


def numberToBase(n, b, fixed_length=0):
    if not fixed_length and n == 0:
        return [0]
    digits = []
    while n or len(digits) < fixed_length:
        digits.append(int(n % b))
        n //= b
    return digits[::-1]

def encode_compact_qr(codex32_str):
    import qrcode
    from qrcode.image.styledpil import StyledPilImage
    from qrcode.image.styles.moduledrawers.pil import CircleModuleDrawer
    big_num = 0
    b45_encoded = ''
    hrp, k, ident, share_index, data = Codex32.parse_header(codex32_str)
    if hrp != 'ms':
        return None
    if share_index == 's':
        _, _, _, master_seed = decode('ms', codex32_str)
        parity = ecc_padding(master_seed)
        last_two_bits = int.from_bytes(parity, 'big') % 64 >> 4
    elif int(k) < 6:
        last_two_bits = int(k) - 2
    else:
        return None
    base32 = data[5:]
    for i, character in enumerate(base32):
        big_num += character * 32 ** (26 - i)
    bigger_num = big_num * 4 + last_two_bits
    for index in numberToBase(bigger_num, 45, 25):
        b45_encoded += BASE45_CHARSET[index]
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=24,
        border=4,
    )
    qr.add_data(b45_encoded)
    img = qr.make_image(image_factory=StyledPilImage, module_drawer=CircleModuleDrawer())
    img.show()


def decode_compact_qr(hrp, last_k, ident, string):
    big_num = 0
    for i, character in enumerate(string):
        big_num += BASE45_CHARSET.find(character) * 45 ** (24 - i)
    bech32 = numberToBase(big_num//4, 32, 27)
    k = '0' if bech32[0] == 16 else str(big_num % 4 + 2)
    if last_k != '?' and k != last_k:
        return None
    if ident != '????':
        return ms32_encode(hrp, [CHARSET.find(x.lower()) for x in k + ident] + bech32)
    return hrp + "1" + k + ident + "".join([CHARSET[d] for d in bech32]) + '?' * 13


def bin_decode(codex):
    """Validate a codex32/codexQR share, and determine HRP and data."""
    hrp, header, ms32_data = ms32_decode(codex)
    if len(ms32_data) != 32:
        return (None, None, None)
    bin_data = convertbits(ms32_data, 5, 1)
    if bin_verify_index_and_padding(header, bin_data):
        return (hrp, header, bin_data[30:-2])
    return (None, None, None)


def bin_decode(codex):
    """Validate a codex32 string, and determine CodexQR data."""
    hrp, header, ms32_data = ms32_decode(codex) # must be valid codex32
    if header[0] == '9': # t=9 unsupported
        return None
    data = convertbits(ms32_data, 5, 1)
    # FIXME: How the 's' share is currently CRC'd requires fingerprint ID.

    if bin_verify_crc(hrp, header, data): # string is compatible with CodexQR
        if len(ms32_data) == 32: # 21x21, 16 bytes entropy
            return CodexQR.from_header(header).tiny_header + data[30:-2]
    return None


def qr_decode(qr_data):
    t = int(convertbits(qr_data[:3], 1, 3))
    ms32_data = CHARSET.find(str(t))
    if len(qr_data) == 3 + 10 + 128:
        entropy_len = 128
        id_len = 10
    ms32_data += qr_data[3:10] + [-1, -1]
    index = [16] if not t else [qr_data[-128:]]
    entropy_len = len(qr_data) - 15
    entropy_len = len(qr_data) - 15


def bin_encode(hrp, data):
    """Compute a codex32 secret given HRP and binary data values."""
    ms32_data = convertbits(data + bin_create_crc(hrp, data), 1, 5)
    combined = ms32_data + ms32_create_checksum(ms32_data)
    return hrp + '1' + ''.join([CHARSET[d] for d in combined])


def ident_encryption_key(payload, k, unique_string=""):
    """
    Generate an MS32 encryption key from unique string and header data.

    :param payload: Payload for getting the length component of header.
    :param k: Threshold component of header for key generation.
    :param unique_string: Optional unique string to avoid ident reuse.
    :return: Four symbol MS32 Encryption key derived from parameters.
    """
    password = bytes(unique_string, "utf")
    salt = len(payload).to_bytes(1, "big") + bytes("ms1" + k, "utf")
    return convertbits(scrypt(
        password, salt=salt, n=2 ** 20, r=8, p=1, maxmem=1025 ** 3, dklen=3),
        8, 5, pad=False)


def encrypt_fingerprint(master_seed, k, unique_string=""):
    """
    Encrypt the MS32 fingerprint using a unique string and header data.

    :param master_seed: The master seed used for fingerprint.
    :param k: The threshold parameter as a string.
    :param unique_string: Optional unique string encryption password.
    :return: Encrypted fingerprint as a bech32 string.
    """
    enc_key = ident_encryption_key(master_seed, k, unique_string)
    new_id = [x ^ y for x, y in zip(ms32_fingerprint(master_seed), enc_key)]
    return "".join([CHARSET[d] for d in new_id])



# KDF SHARES:
# There is some info in the CompactQR to use as salt: namely the
# threshold or id.

import random
from random import randrange
from random import randbytes

def add_errors(data, qty, burst=False, rand=True):
    #print(data)
    corrupt_data = data.copy()
    error_symbol_locs = random.sample(range(0, len(data)//5), qty)
    for loc in error_symbol_locs:
        #print(loc)
        if burst:
            for i in range(5):
                if not rand or randrange(2):
                    corrupt_data[loc * 5 + i] ^= 1
        else:
            corrupt_data[loc * 5 + randrange(5)] ^= 1
    #print(corrupt_data)
    return corrupt_data
# CRC-7 test results.
#(x^7 + x^3 + 1)
# 2 errors: 0.0902%
# 3 errors: 
# 4 errors: 
# 5 errors: 0.7759%
# x^7+x^6+x^3+x+1
# 2 errors: 0.0927
# 5 errors: 0.7819
# x^7+x^6+x^5+x^3+x^2+x+1
# 2 errors: 0.0917
# 5 errors: 0.7719

# x^7+x^6+x^5+x^2+1  TESTED
# 2 errors: 0.0867
# 3 errors: 0.8013
# 4 errors: 0.7815
# 5 errors: 0.7823
# 6 errors: 0.7723
# 9 errors: 0.7893
# 10 errors: 0.7956
# 1 5-bit burst error: 0.0
# 2 5-bit burst error: 0.0
# 3 5-bit burst error: 0.6324
# 4 5-bit burst error: 0.7747
# 5 5-bit burst error: 0.8161
# 9 5-bit burst error: 0.7936
# 10 5-bit burst error: 0.7797
# 1 random 5-bit burst error: 3.1509
# 2 random 5-bit burst error: 0.7799
# 3 random 5-bit burst error: 0.7983
# 4 random 5-bit burst error: 0.7704
# 5 random 5-bit burst error: 0.777
# 9 random 5-bit burst error: 0.7816

# x^7+x^5+x^4+x^2+x+1 TESTED
# 2 errors: 0.9355
# 3 errors: 0.0
# 4 errors: 1.5756
# 5 errors: 0.0
# 6 errors: 1.5598
# 9 errors: 0.0
# 10 errors: 1.5768
# 1-3 5-bit burst error: 0.0
# 4 5-bit burst error: 1.6009
# 5 5-bit burst error: 0.0
# 9 5-bit burst error: 0.0
# 10 5-bit burst error: 1.5574
# 1 random 5-bit burst error: 3.1328
# 2 random 5-bit burst error: 0.7911
# 3 random 5-bit burst error: 0.7752
# 4 random 5-bit burst error: 0.7736
# 5 random 5-bit burst error: 0.7809
# 9 random 5-bit burst error: 0.7925

# TO generate a backup set: First get entropy from KDF for each share.
# initialize a counter at 0, HMAC the share's entropy with the counter
# continue until all k - 1 shares have unique_indexes.

# If using a seed backup passphrase: KDF the passphrase w/ tiny header as salt 
# use that as the entropy for a share. The KDF share's counter will increment until the index is not 's'.
# this guarantees the KDF share always knows its index.

# For the 21x21 CodexQR, encode 16-bytes of , 5-bits of codex32 checksum, and 2.3 bits of 



# The secret does not need CRC-7 padding and should not have it.
# When we ask for n shares, they must be non-'s' indexes.
# When we encode Compact CodexQR now we should encode it index first.
# the first 128 bits, are enough to determine the padding and last
# data character precisely. This will reduce hunting without harming
# correction capacity. We've essentially gained 5 bits of ECC on the
# shares, so now 9.3 bits performs like 14.3 would have.
#
"""print('')
print('compatible shares found:')
print(len(passing))
print('')
print('compatible shares generated:')
print(int(t))
print('')
print('compatible generated shares')
print(generated)
print('')
print('compatible derived shares')
print(compatible)
print('')
print('counts required to generate')
print(counter)"""

    
# Removing the index from the CRC-2 would avoid having to recalculate it when an index is derived
# 16 bytes > index. CRC-2 after index is known

# If I am using 2 codex32 characters as bonus, the crc-2 should not include the ID, just fp.
# If I am using no codex32 characters as bonus, include the header so that I can instantly
# Detect mismatched shares.

failures = 0
counts = 0
trials = 10000
#for i in range(trials):
#    seed = randbytes(16)
#    fp = get_fp(seed) # b'deadbeef' #

    #data, seed, counter = create_index_checksum(fp, seed, CHARSET[:11]+CHARSET[19:])
#    counts += counter
#    ms32_data = [10] + ms32_expand(fp)[:4] + data
#    ms32_interpolate([ms32_data])
#    if not ms32_verify_index_checksum(fp, ms32_data):
#        failures += 1

#print(failures/trials)
#print(counts/trials)


#print(encode('ms', k, id, index, master_seed, fp))
#print('key identifier')
#key_id = convertbits(_ripemd160(sha256(BIP32.from_seed(master_seed).pubkey).digest()), 8, 5)
#print(key_id)

#shuffle_key = fp + bytes(hrp + k + id + index, 'utf')
#print(shuffle_key)
#index_list = shuffle_indexes(shuffle_key)
#print(index_list)
