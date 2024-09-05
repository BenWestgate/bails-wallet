#!/bin/python3
# Author: Leon Olsson Curr and Pearlwort Sneed <pearlwort@wpsoftware.net>
# License: BSD-3-Clause

import hashlib
import hmac
import functools
from hashlib import sha256, sha512, scrypt

#from electrum.bip32 import BIP32Node
#from electrum.crypto import hash_160

CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
MS32_CONST = 0x10CE0795C2FD1E62A
MS32_LONG_CONST = 0x43381E570BF4798AB26
bech32_inv = [
    0, 1, 20, 24, 10, 8, 12, 29, 5, 11, 4, 9, 6, 28, 26, 31,
    22, 18, 17, 23, 2, 25, 16, 19, 3, 21, 14, 30, 13, 7, 27, 15,
]

BASE45_CHARSET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:"


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

@functools.lru_cache(maxsize=None)
def ms32_create_checksum(data):
    data = list(data)
    if len(data) > 80:  # See Long codex32 Strings
        return ms32_create_long_checksum(data)
    values = data
    polymod = ms32_polymod(values + [0] * 13) ^ MS32_CONST
    return tuple([(polymod >> 5 * (12 - i)) & 31 for i in range(13)])


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


# Copyright (c) 2023 Ben Westgate
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


def ms32_encode(hrp, data):
    """
    Compute an MS32 string.

    :param hrp: Human-readable part of the ms32 string, usually 'ms'.
    :param data: List of base32 integers representing data to encode.
    :return: MS32 encoded string with the given HRP and data.
    """
    combined = data + ms32_create_checksum(data)
    return hrp + "1" + "".join([CHARSET[d] for d in combined])


def ms32_decode(ms32_str):
    """
    Validate an MS32 string and extract components.

    :param ms32_str: The MS32 encoded string to be validated.
    :return: Tuple: HRP, k, ident, share index, data. If invalid,
             (None, None, None, None, None)
    """
    if ((any(ord(x) < 33 or ord(x) > 126 for x in ms32_str))
            or ms32_str.lower() != ms32_str and ms32_str.upper() != ms32_str):
        return None, None, None, None, None
    ms32_str = ms32_str.lower()
    pos = ms32_str.rfind("1")
    if pos < 1 or pos + 46 > len(ms32_str):
        return None, None, None, None, None
    if not all(x in CHARSET for x in ms32_str[pos + 1:]):
        return None, None, None, None, None
    hrp = ms32_str[:pos]
    k = ms32_str[pos + 1]
    ident = ms32_str[pos + 2: pos + 6]
    share_index = ms32_str[pos + 6]
    if not k.isdigit() or k == "0" and share_index != "s":
        return None, None, None, None, None
    data = [CHARSET.find(x) for x in ms32_str[pos + 1:]]
    checksum_length = 13 if len(data) < 95 else 15
    if not ms32_verify_checksum(data):
        return None, None, None, None, None
    return hrp, k, ident, share_index, data[:-checksum_length]



def convertbits(data, frombits, tobits, pad=True):
    """
    Perform general power-of-2 base conversion.

    :param data: List of integers to be converted.
    :param frombits: Original base's bit size.
    :param tobits: Target base's bit size.
    :param pad: Whether to pad the result, defaults to True.
    :return: List of integers in target base, or None on failure.
    """
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
    elif bits >= frombits:
        return None
    return ret


def decode(hrp, codex_str):
    """
    Decode a codex32 string.

    :param hrp: Human-readable part of the codex32 string usually 'ms'.
    :param codex_str: Codex32 string to be decoded.
    :return: Tuple: k, ident, share index, decoded bytes.
             If decoding fails, (None, None, None, None).
    """
    hrpgot, k, ident, share_index, data = ms32_decode(codex_str)
    if hrpgot != hrp.lower():
        return None, None, None, None
    decoded = convertbits(data[6:], 5, 8, False)
    if decoded is None or len(decoded) < 16 or len(decoded) > 64:
        return None, None, None, None
    return k, ident, share_index, bytes(decoded)


def ecc_padding(data):
    """
    Calculate and return a byte with concatenated parity bits.

    :param data: Bytes of seed_len, hrp, k, ident, index and payload.
    :return: Byte with concatenated parity in most significant bits.
    """
    # Count mod 2 the number of set (1) bits in the byte data
    parity = bin(int.from_bytes(data)).count('1') % 2 << 7
    # Count mod 2 the number of set (1) even bits in the byte data
    parity += bin(int.from_bytes(data))[::2].count('1') % 2 << 6
    # Count mod 2 the number of set (1) odd bits in the byte data
    parity += bin(int.from_bytes(data))[3::2].count('1') % 2 << 5
    # Count mod 2 the number of set (1) third bits in the byte data
    parity += bin(int.from_bytes(data))[::3].count('1') % 2 << 4

    return parity.to_bytes()


def encode(hrp, k, ident, share_index, payload):
    """
    Encode a codex32 string.

    :param hrp: Human-readable part of the codex32 string.
    :param k: Threshold parameter as a string.
    :param ident: Identifier as a string.
    :param share_index: Share index as a string.
    :param payload: Payload data to be encoded.
    :return: Codex32 string or None if validation fails.
    """
    if share_index.lower() == 's':
        checksum = ecc_padding(payload)
    else:
        checksum = ecc_padding(bytes(k + share_index, "utf") + payload)
    data = convertbits(
        payload + checksum, 8, 5, False)[:len(convertbits(payload, 8, 5))]
    ret = ms32_encode(hrp, [CHARSET.find(x.lower()) for x in
                            k + ident + share_index] + data)
    if decode(hrp, ret) == (None, None, None, None):
        return None
    return ret


def validate_codex32_string_list(string_list, k_must_equal_list_length=True):
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

    return [ms32_decode(codex32_string)[4] for codex32_string in string_list]


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


def relabel_codex32_strings(hrp, string_list, new_k="", new_id=""):
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
        k, ident, share_index, decoded = decode(hrp, codex32_string)
        new_k = k if not new_k else new_k
        new_id = ident if not new_id else new_id
        new_strings.append(encode(hrp, new_k, new_id, share_index, decoded))
    return new_strings


def shuffle_indexes(index_seed, indices=CHARSET.replace("s", "")):
    """Shuffle indexes deterministically with seed and HMAC-SHA256."""
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
            value = digest[counter % 32: counter % 32 + 1]  # rand byte
            counter += 1
        assigned_values[char] = value
    return sorted(assigned_values.keys(), key=lambda x: assigned_values[x])


def generate_shares(master_key="", user_entropy="", n=31, k="2", ident="NOID",
                    seed_length=16, existing_codex32_strings=None):
    """
    Generate new codex32 shares from provided or derived entropy.

    :param master_key: BIP32 extended private master key from bitcoind.
    :param user_entropy: User-provided entropy for improved security.
    :param n: Total number of codex32 shares to generate (default: 31).
    :param k: Threshold parameter (default: 2).
    :param ident: Identifier (4 bech32 characters) or 'NOID' (default).
    :param seed_length: Length of seed (16 to 64 bytes, default: 16).
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
        seed_length = len(payload)

    if num_strings == int(k) and not master_seed:
        master_seed = recover_master_seed(existing_codex32_strings)
    if master_seed:
        master_key = BIP32Node.from_rootseed(master_seed, xtype="standard")
    elif master_key:
        master_key = BIP32Node.from_xkey(master_key)
    else:
        return None
    key_identifier = hash_160(master_key.eckey.get_public_key_bytes())
    entropy_header = (seed_length.to_bytes(length=1, byteorder="big")
                      + bytes("ms" + k + ident + "s", "utf") + key_identifier)
    salt = entropy_header + bytes(CHARSET[n] + user_entropy, "utf")
    # This is equivalent to hmac-sha512(b"Bitcoin seed", master_seed).
    password = master_key.eckey.get_secret_bytes() + master_key.chaincode
    # If scrypt absent visit OWASP Password Storage or use pbkdf2_hmac(
    # 'sha512', password, salt, iterations=210_000 * 64, dklen=128)
    derived_key = hashlib.scrypt(
        password, salt=salt, n=2 ** 20, r=8, p=1, maxmem=1025 ** 3, dklen=128)
    index_seed = hmac.digest(derived_key, b"Index seed", "sha512")[:32]
    available_indices.remove("s")
    available_indices = shuffle_indices(index_seed, available_indices)
    tmp_id = "temp" if ident == "NOID" else ident

    # Generate new shares, if necessary, to reach a threshold.
    for i in range(num_strings, int(k)):
        share_index = available_indices.pop()
        info = bytes("Share payload with index: " + share_index, "utf")
        payload = hmac.digest(derived_key, info, "sha512")[:seed_length]
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
    return convertbits(hashlib.scrypt(
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
    salt = len(payload).to_bytes(1, "big") + bytes(codex32_str[:8], "utf")
    derived_key = hashlib.scrypt(password, salt=salt, n=2 ** 20, r=8, p=1,
                                 maxmem=1025 ** 3, dklen=128)
    passphrase_index_seed = hmac.digest(
        derived_key, b"Passphrase share index seed", "sha512")[:32]
    share_index = shuffle_indices(
        passphrase_index_seed, list(CHARSET.replace("s", ""))).pop()
    payload = hmac.digest(derived_key, b"Passphrase share payload with index "
                          + bytes(share_index, "utf"), "sha512")[:len(payload)]
    return encode("ms", k, ident, share_index, payload)


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
    hrp, k, ident, share_index, data = ms32_decode(codex32_str)
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




import time
import itertools
import multiprocessing
import psutil

# TODO try one substitution value per function call by adding a new argument or combining the erasures and errors together.

# when I get back from walk, teach the substitutor how to fill erasures while
# keeping the possible substitution amounts at 0 first for all possible erasure
# values before trying even the first bit of substitions.
# Remember erasures need to check all 32 values each before a single error is tried.
# Tomorrow, check the different patterns of substitution bit-depth and error locations quantity seach space.
# have the search example from 1 1-bit error to the maximum completable from smallest error space to largest.


#@functools.lru_cache(maxsize=None)
def correct_4_errors(candidate):
    data = candidate[:-checksum_length]
    new_checksum = ms32_create_checksum(data)
    correction_left = 4
    for new, old in zip(new_checksum, candidate[-checksum_length:]):
        if old != new and old != -1:
            correction_left -= 1
            if correction_left < 0:
                return False
    return data


#@functools.lru_cache(maxsize=None)
def correct_3_errors(candidate):
    data = candidate[:-checksum_length]
    new_checksum = ms32_create_checksum(data)
    correction_left = 3
    for new, old in zip(new_checksum, candidate[-checksum_length:]):
        if old != new and old != -1:
            correction_left -= 1
            if correction_left < 0:
                return False
    return data


#@functools.lru_cache(maxsize=None)
def correct_2_errors(candidate):
    data = candidate[:-checksum_length]
    new_checksum = ms32_create_checksum(data)
    correction_left = 2
    for new, old in zip(new_checksum, candidate[-checksum_length:]):
        if old != new and old != -1:
            correction_left -= 1
            if correction_left < 0:
                return False
    return data

#@functools.lru_cache(maxsize=None)
def correct_1_errors(candidate):
    data = candidate[:-checksum_length]
    new_checksum = ms32_create_checksum(data)
    correction_left = 1
    for new, old in zip(new_checksum, candidate[-checksum_length:]):
        if old != new and old != -1:
            correction_left -= 1
            if correction_left < 0:
                return False
    return data


@functools.lru_cache(maxsize=None)
def correct_0_errors(candidate):
    data = candidate[:-checksum_length]
    new_checksum = ms32_create_checksum(data)
    for new, old in zip(new_checksum, candidate[-checksum_length:]):
        if old != new and old != -1:
            return False
    return data


def correct(inse, dele, subs, invalid_data):
    threshold_fills = (15, 10, 17, 21, 20, 26, 30, 7, 5)
    print(dele)
    print(inse)
    print(subs)
    print('checksum errors allowed:')
    checksum_errors = (8 - erasures - dele) // 2 - inse - subs
    print(checksum_errors)

    def delete_insert_substitute(dele, inse, subs, candidate):
        #@functools.lru_cache(maxsize=None)
        def delete(candidates):
            delete_set = set()
            for candidate in candidates:
                delete_set.update(candidate[:j]+candidate[j+1:] for j in range(len(candidate)))
            return delete_set
            #for new_candidate in delete_set:
            #    yield new_candidate

        #@functools.lru_cache(maxsize=None)
        def insert(candidates):
            insert_set = set()
            for candidate in candidates:
                insert_set.update(candidate[:j]+(-1,)+candidate[j:] for j in range(len(candidate) + 1))
            return insert_set
            #for new_candidate in insert_set:
            #    yield new_candidate

        #@functools.lru_cache(maxsize=None)
        def substitute(candidates, qty):
            if qty == 0:
                for candidate in candidates:
                    yield candidate
            substitute_set = set()
            for candidate in candidates:
                for substitute_combo in itertools.combinations(range(len(candidate)-checksum_length), qty):
                    modified_candidate = candidate
                    for j in substitute_combo:
                        modified_candidate = modified_candidate[:j]+(-1,)+modified_candidate[j+1:]
                    yield modified_candidate
                    #substitute_set.update((candidate[:j]+(-1,)+candidate[j+1:] for j in substitute_combo))

                    #for j in substitute_combo:
                    #    yield candidate[:j]+(-1,)+candidate[j+1:]
                        # TODO: when I do bit level search create modified_candidate = list(candidate) to not clobber the original
                    #yield modified_candidate
            #return substitute_set
        #def fill_threshold(candidates):




        #@functools.lru_cache(maxsize=None)
        def fill(candidates):
            for candidate in candidates:
                filled_candidates = ()
                if candidate[0] == -1 and not valid_header:
                    fills = itertools.product(threshold_fills, range(32), repeat=filled_candidate[:len(candidate)-checksum_length].count(-1)-1)



                fills = itertools.product(range(32), repeat=filled_candidate[:len(candidate)-checksum_length].count(-1))
                for filled_candidate in filled_candidates:
                    for fill in fills:
                        for value in fill:
                            filled_candidate[filled_candidate.index(-1)] = value
                        yield header + tuple(filled_candidate)

        candidates = (candidate,)
        for i in range(dele):
            candidates = delete(candidates)
        for i in range(inse):
            candidates = insert(candidates)
        candidates = substitute(candidates, subs)
        for filled in fill(candidates):
            yield filled

    new_candidates = delete_insert_substitute(dele, inse, subs, invalid_data)

    if checksum_errors == 4:
        solution = pool.imap_unordered(correct_4_errors, new_candidates)
    elif checksum_errors == 3:
        solution = pool.imap_unordered(correct_3_errors, new_candidates)
    elif checksum_errors == 2:
        solution = pool.imap_unordered(correct_2_errors, new_candidates, chunksize=2**8)    # 1=6009, 2=4779, 3=3982, 4=3702, 5=3036, 6=2943, 7=2682, 8=2664, 9=2672, 10=
        #8=6953, 7=7275,
    elif checksum_errors == 1:
        solution = pool.imap_unordered(correct_1_errors, new_candidates, chunksize=2**10)
    elif checksum_errors == 0:
        solution = pool.imap_unordered(correct_0_errors, new_candidates, chunksize=2**11)

    #for can in new_candidates:
    #    print(can)
    #exit()
    valid_candidate = next((x for x in solution if x), None)
    end_time = time.time()
    execution_time = end_time - start_time
    print(int(execution_time * 1000))
    print()
    if valid_candidate:
        print('correction found!')
        print(ms32_encode(hrp, valid_candidate).upper())
        print(ms32_encode(hrp, valid_candidate).lower())
        return True
    else:
        return False


start_time = time.time()
invalid_str = 'MS1?NAMEA320ZYXWVTSRQPNMLKJHGFEDCXRPP870HKKQRM'.lower()
# wrong: MS12NAMEA320ZYXWVUTSRQPQNMLKJHGFEDCAXRPP870HKQKQRM
# shortest ms10testsxxxxxxxxxxxxxxxxxxxxxx4nzvca9cmczlw
# longest ms10testsxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx4nzvca9cmczlw
# ms10testsxxxxxxxxxxxxxxxxxxxxxxxxxx4nzvca9cmczlw
# MS12NAMEA320ZYXWVUTSRQPNMLKJHGFEDCAXRPP870HKKQRM
valid_header = False
valid_length = 48
pos = invalid_str.rfind("1")
hrp = invalid_str[:pos]
length = len(invalid_str)

if not valid_length:
    if length < 62:
        valid_length = 48
    elif length > 100:
        valid_length = 127
    else:
        valid_length = 74
if valid_length <= 93:
    checksum_length = 13
elif valid_length >= 96:  # See Long codex32 Strings
    checksum_length = 15

length_syn = length - valid_length
invalid_data = tuple([CHARSET.find(x) for x in invalid_str[pos+1:]])
print(invalid_data)
header = ()
if valid_header:
    header = invalid_data[:5]
    invalid_data = invalid_data[5:]
data_length = len(invalid_data)
erasures = invalid_data.count(-1)
deletes = max(length_syn, 0)
inserts = max(-length_syn, 0)
correction_capacity = 8 - erasures - deletes - 2 * inserts
print('correction capacity left')
print(correction_capacity)
pool = multiprocessing.Pool(psutil.cpu_count(logical=False))
for depth in range(correction_capacity + 1):
    print('CORRECTION DEPTH:')
    print(depth)
    print()
    substitutes = depth // 2
    if not depth % 2:
        if correct(inserts, deletes, substitutes, invalid_data):
            break
        if depth > 5:
            if correct(inserts + 2, deletes + 2, substitutes - 3, invalid_data):
                break
    elif depth > 2:
        if correct(inserts + 1, deletes + 1, substitutes - 1, invalid_data):
            break

end_time = time.time()
execution_time = end_time - start_time
print(int(execution_time * 1000))


#for can in solution:
#    print(can)
    #time.sleep(0.1)
#exit()

