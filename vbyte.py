def encode_vbyte(numbers, delimiter=0x00, hard_delimit=False):
    result = bytearray()
    for num in numbers:
        while True:
            # Encode 7 bits of the number and append to the result
            byte = num & 0x7f
            num >>= 7
            result.append(byte | (0x80 if num != 0 else 0))
            if num == 0:
                break
    result.append(delimiter)
    if hard_delimit:
        result.append(delimiter)
    return result


def decode_vbyte(fpath, chunk_size=1024, delimiter=0x00):
    with open(fpath, 'rb') as f:
        result = []
        buffer = 0
        shift = 0
        term_def = True
        hard_delimit = False
        doc = -1
        positions = []
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break

            for byte in chunk:
                # Delimiter byte found
                if byte == delimiter:
                    if hard_delimit:
                        hard_delimit = False
                        term_def = not term_def
                        continue
                    if term_def:
                        print(f"{''.join(map(chr,result[:-1]))}, {result[-1]}")
                    else:
                        if positions is not None:
                            doc = result[0]
                            positions = None
                        elif positions is None:
                            positions = result
                            print(f"{doc}, {positions}")
                    result = []
                    buffer = 0
                    shift = 0

                    hard_delimit = True
                else:
                    hard_delimit = False
                    if byte < 128:  # MSB is 0
                        buffer |= byte << shift
                        result.append(buffer)
                        buffer = 0
                        shift = 0
                    else:  # MSB is 1
                        buffer |= (byte & 0x7f) << shift
                        shift += 7