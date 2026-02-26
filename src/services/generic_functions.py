from src.config import PASS_KEY

def rotate_right(value):
    for _ in range(2):
        if value % 2 == 1:
            value = (value // 2) + 128
        else:
            value = value // 2
    return value % 256

def rotate_left(value):
    for _ in range(2):
        new_val = (value * 2) % 256
        if value >= 128:
            new_val += 1
        value = new_val % 256
    return value

def encrypt(value):
    val_bytes = value.encode('latin-1')
    key_bytes = PASS_KEY.encode('latin-1')
    result = bytearray()

    for i in range(len(val_bytes)):
        ch1 = val_bytes[i]
        ch2_index = ((i + 1) % len(key_bytes))
        ch2 = key_bytes[ch2_index]
        combined = (ch1 + ch2) % 256
        rotated = rotate_right(combined)
        result.append(rotated)

    return result.decode('latin-1')

def decrypt(value):
    val_bytes = value.encode('latin-1')
    key_bytes = PASS_KEY.encode('latin-1')
    result = bytearray()

    for i in range(len(val_bytes)):
        ch = val_bytes[i]
        rotated = rotate_left(ch)
        key_ch = key_bytes[(i + 1) % len(key_bytes)]
        decoded = (rotated - key_ch) % 256
        if decoded == 'Ü':
            decoded = '2'
        result.append(decoded)

    return result.decode('latin-1').replace('Ü', '2')