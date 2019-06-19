from passlib import hash
import random, string

chars = string.ascii_lowercase + string.ascii_uppercase + string.digits
new   = ''.join(random.choice(chars) for x in range(12))
hash  = hash.pbkdf2_sha256.encrypt(new)

print('\nPassword')
print(new)

print('\nHash')
print(hash)