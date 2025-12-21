def cal_checksum8(data: bytes) -> int:
    """计算 V1/V2 的简单加和校验"""
    return sum(data) & 0xFF

def cal_xor(data: bytes) -> int:
    """V3 的 XOR 校验"""
    val = 0
    for b in data:
        val ^= b
    return val

def make_v1_frame(cmd: int, channel: int, data: int) -> bytes:
    payload = bytes([cmd, channel, data])
    checksum = cal_checksum8(payload)
    return bytes([0x55, 0x5A]) + payload + bytes([checksum])

def make_v2_frame(cmd: int, channel: int, data0: int, data1: int) -> bytes:
    payload = bytes([cmd, channel, data0, data1])
    checksum = cal_checksum8(payload)
    return bytes([0x55, 0x5A]) + payload + bytes([checksum])

def make_v3_frame(cmd: int, data: bytes) -> bytes:
    length = len(data)
    len_bytes = length.to_bytes(2, byteorder='little')
    payload = bytes([cmd]) + len_bytes + data
    checksum = cal_xor(payload)
    crc_bytes = checksum.to_bytes(2, byteorder='little')
    return bytes([0x55, 0xAB]) + payload + crc_bytes

def print_hex(title: str, frame: bytes):
    print(f"{title} ({len(frame)} bytes):")
    print(' '.join(f"{b:02X}" for b in frame))
    print()

def test_write_serial_number(serial: str):
    """生成写入序列号的 V3 帧（CMD=0xFA）"""
    cmd = 0xFA
    data = serial.encode("utf-8")
    if len(data) < 32:
        data += b'\x00' * (32 - len(data))
    frame = make_v3_frame(cmd, data)
    print_hex(f"V3 Write Serial [{serial}]", frame)

# 示例测试
if __name__ == "__main__":
    # # V1: CMD=0x01, channel=0x01, data=0x01 (打开 ch1)
    # v1 = make_v1_frame(0x01, 0x01, 0x01)
    # print_hex("V1 Frame", v1)

    # # V2: CMD=0x0B, channel=0x01, data=[0x01, 0x01] (设置默认状态启用为ON)
    # v2 = make_v2_frame(0x0B, 0x01, 0x01, 0x01)
    # print_hex("V2 Frame", v2)

    # V3: CMD=0x20, data=b'\x01\x02\x03\x04' (任意数据)
    # v3 = make_v3_frame(0x20, b'\x01\x02\x03\x04')
    # print_hex("V3 Frame", v3)

    # V3: 写入序列号
    test_write_serial_number("12345678")