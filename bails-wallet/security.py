from hashlib import sha1
import hmac
from random import randbytes

dklen = 2
seedlen = 3
k = 3

dk = randbytes(dklen)
print(dk)

def gen_shares(dk):
    return [hmac.digest(dk, i.to_bytes(1), "sha1")[:seedlen] for i in range(k)]

shares = gen_shares(dk)[:-1]

for i in range(256**dklen):
    maybe_dk = i.to_bytes(dklen)
    if all(x in gen_shares(maybe_dk) for x in shares):
        print(maybe_dk)
        break

# The above code demonstrates that if you generate more share entropy
# than the derived key has, dk can be discovered with < T shares and
# the secret itself. 