import qrcode
import subprocess

def encode_compact_qr(bytes):
    #img = qrcode.make(bytes)
    #type(img)
    #img.save(bytes.hex()+"qr.png")
    ret = subprocess.run([
        "zbarimg", "--raw", byte.hex()+"qr.png"], capture_output=True)
    return ret.stdout

scan_values = []
import zbarlight
from PIL import Image

for i in range(256**2):
    # Load the QR code image
    with open('qr_code.png', 'rb') as image_file:
        image = Image.open(image_file)
        image.load()

    # Decode the QR code
    codes = zbarlight.scan_codes('qrcode', image)

    if codes:
        # codes is a list of byte data found in the QR code(s)
        decoded_data = codes[0]
        print(decoded_data)
    else:
        print("No QR code found.")

print(scan_values)
print(len(scan_values))
print(set(scan_values))
print(len(set(scan_values)))
