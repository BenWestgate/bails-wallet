from codex32 import convertbits, CHARSET
from random import randbytes
from enum import Enum
from subprocess import run

BASE45_CHARSET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:"


class Encoding(Enum):
    """Enumeration type to list the various supported encodings."""
    MS10_SECRET = 1
    MS12_SHARE = 2
    MS13_SHARE = 3


def bin_polymod(values):
    """Internal function that computes the codexQR checksum."""
    # Define the CRC-9 polynomial for 128-bit data
    # 0x13c = x^9 +x^6 +x^5 +x^4 +x^3 +1 (0x13c; 0x279) <=> (0x13c; 0x279)
    polynomial = 0b1001111001
    crc = 0
    for bit in values:
        crc = (crc << 1) | int(bit) # Shift in the next bit
        # If the leftmost bit (MSB) is 1, XOR with the polynomial
        if crc & (0b1 << 9):
            crc ^= polynomial
    # Return the last 9 bits as the CRC
    return crc & (2 ** 9 - 1)

def bin_hrp_expand(hrp):
    """Expand the HRP into values for checksum computation."""
    return convertbits(bytes(hrp, 'utf'), 8, 1)

def bin_verify_checksum(hrp, data):
    """Verify a checksum given HRP and converted data characters."""
    const = bin_polymod(bin_hrp_expand(hrp) + data)
        
    if const == 0:
        return Encoding.MS10_SECRET
    else:
        return const
    return None

def bin_create_checksum(hrp,data, header):
    values = bin_hrp_expand(hrp) + data
    if header[0] == '0':
        const = 0b111111111
    return convertbits([const],9,1)



# After the data 9.296327408 remain, there is 
# Different thresholds have a different encoding because they have 
# different data most urgently needed. The secret needs nothing. t=2
# shares need the fingerprint.
# use the rest of the space for the ID.
# Since the Index is known, we can assign to each share a different
# symbol from the ID.
# For threshold 2, just use the first symbol for all shares.
# This is the symbol that should be tweaked when resharing.
# For threshold 3:
# when we have scanned 2, we know 15-bits about the ID, we could use
# par2 style parity coding to display what we can at each step.
# 5 bits of char 1
# 2.5 bits of char 2
# 1.667 bits of char 3
# 1.25 bits of char 4
# 10.416666667 bits total, won't work.
# 5 bits of char 1
# 2.5 bits of char 2
# 1.667 bits of char 3
# 0.129327 bits remain, we discourage t>3 so lets just do char 1 & char 2
# 5 bits of char 1
# 2.5 bits of char 2
# Leaves 1.796327 bits remaining
# Which supports 3.473348087 thresholds.
# Lets interleave the 4 id symbols across different shares
# index = 0 is id[0], index = 1 is id[1] and so forth. This way we
# always get at least 1 char of the string and when scanning more we
# have 3/4 chance of learning another.
# 2nd share, two possibilities: We know 2 char of id or 1.
# say it's 1, with 3 bits left, we'd need to have encoded 7.5 bits
# to always fill them after 2 scans.
# say it's 2, with 2 char left, we can fill this in 2 scans if we
# encoded 5 bits per secret. But theres no room for that either.


def bin_create_checksum(hrp, data, spec):
    """Compute the checksum values given HRP and data."""
    values = bin_hrp_expand(hrp) + data
    const = 1 if spec == Encoding.MS12_SHARE else 0
    polymod = bin_polymod(values + [0, 0, 0, 0, 0, 0, 0, 0, 0]) ^ const
    return convertbits([polymod], 9, 1)

qr_data = b'\x00' * 16 # run(['zbarimg','--raw','--oneshot','-Sbinary','qr.png'], capture_output=True).stdout
def decode(qr_data):
    if len(qr_data) == 16: # CompactSeedQR BIP39
        from mnemonic import Mnemonic
        bip39 = Mnemonic()
        mnemonic = bip39.to_mnemonic(qr_data)
        seed = bip39.to_seed(mnemonic)
    
    elif len(qr_data) == 17:
        # CompactCodexQR - bytes mode 8 bits, 256 codes
        payload = qr_data[:16]
    elif len(qr_data) == 41 and all(char.isdigit() for char in str(qr_data)):
        # CompactCodexQR - numeric mode 8.2 bits, 293 codes
        payload = int(qr_data).to_bytes(18,'big')[:16]
    elif len(qr_data) == 25 and all(char in BASE45_CHARSET for char in str(qr_data)):
        # CompactCodexQR - alphanumeric mode 9.3 bits, 628 codes
        data = [BASE45_CHARSET.find(x) for x in str(qr_data)]
        data_int = sum(value ** (exp + 1) for exp, value in enumerate(data))
        payload = int.to_bytes(data_int, 18, 'big')[:16]
    else:
        codex32string = qr_data
    master_key = bip39.to_hd_master_key(seed)
    return payload

# Total code space is 256 + 293 + 628 = 1177 or 10.2 bits

import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers.pil import CircleModuleDrawer, GappedSquareModuleDrawer

biggest_byte = b'\xFF' * 16 + b'\x00'
biggest_alphanum = biggest_byte + b'\x00'
biggest_numeric = biggest_byte + b'\x00'

def numberToBase(n, b, fixed_length=0):
    if not fixed_length and n == 0:
        return [0]
    digits = []
    while n or len(digits) < fixed_length:
        digits.append(int(n % b))
        n //= b
    return digits[::-1]

def b45encode(data, length=25):
    """Convert bytes to base45-encoded string"""
    b45_encoded = ''
    for index in numberToBase(int.from_bytes(data, 'big'), 45, length):
        b45_encoded += BASE45_CHARSET[index]
    return b45_encoded

"""img = qrcode.make(b45encode(biggest_alphanum), 1, 0)
img.save('alphanum.png')
img = qrcode.make(str(int.from_bytes(biggest_numeric)))
img.save('numeric.png')"""

big_num = int.from_bytes(bytes.fromhex('00' * 2 + 'ff' * 16))
print(big_num)
print(len(str(big_num)))

from qrcode.image.styles.moduledrawers.pil import StyledPilQRModuleDrawer, ANTIALIASING_FACTOR
from qrcode.compat.pil import Image, ImageDraw

class GappedCircleModuleDrawer(StyledPilQRModuleDrawer):
    """
    Draws the modules as circles that are not contiguous.

    The size_ratio determines how wide the circles are relative to the width of
    the space they are printed in
    """

    circle = None

    def __init__(self, size_ratio=0.9):
        self.size_ratio = size_ratio

    def initialize(self, *args, **kwargs):
        super().initialize(*args, **kwargs)
        box_size = self.img.box_size
        fake_size = box_size * ANTIALIASING_FACTOR
        self.circle = Image.new(
            self.img.mode,
            (fake_size, fake_size),
            self.img.color_mask.back_color,
        )
        ImageDraw.Draw(self.circle).ellipse(
            (0, 0, fake_size, fake_size), fill=self.img.paint_color
        )
        smaller_size = int(self.size_ratio * box_size)
        self.circle = self.circle.resize((smaller_size, smaller_size), Image.Resampling.LANCZOS)

    def drawrect(self, box, is_active: bool):
        if is_active:
            self.img._img.paste(self.circle, (box[0][0], box[0][1]))
            
qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=28, border=3)
qr.add_data('')
qr.make(fit=False)
qr.make_image(image_factory=StyledPilImage, module_drawer=GappedCircleModuleDrawer(size_ratio=26/28)).show()


"""seed = randbytes(16)
bin_seed = convertbits(seed, 8, 1)
print(bin_seed)
chk = bin_create_checksum('ms', bin_seed, Encoding.MS10_SECRET)
code = bin_seed + chk
print(code)
print(bin_verify_checksum('ms', code))


data = bin_seed
#chk = bin_create_checksum('ms',  + data, Encoding.MS12_SHARE)
code = data + chk
print(code)
print(bin_verify_checksum('ms', code))"""

#for i in range(32): # example the full id is 1,2,3,4
#    print(ms32_interpolate([[10,0,0,0,0,16,1],[10,0,0,0,0,17,2],[10,0,0,0,0,18,3],[10,0,0,0,0,19,4]],i))

import qrcode
import subprocess

def encode_compact_qr(bytes):
    img = qrcode.make(bytes)
    type(img)
    img.save(bytes.hex()+"qr.png")
    ret = subprocess.run(["zbarimg", byte.hex()+"qr.png"], capture_output=True)
    return ret.stdout