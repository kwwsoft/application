# -*- coding: utf-8 -*-
import struct
import sys
import os
import shutil

def stm32_crc32(data: bytes) -> int:
    """Calculate hardware CRC32 aligned with STM32 MCU algorithm"""
    crc = 0xFFFFFFFF
    poly = 0x04C11DB7
    
    # STM32 calculates CRC32 strictly by 32-bit words (4 bytes)
    remainder = len(data) % 4
    if remainder != 0:
        data += b'\xFF' * (4 - remainder)
        
    for i in range(0, len(data), 4):
        # Unpack 4 bytes as one 32-bit unsigned int (Big Endian for CRC math)
        word = struct.unpack('>I', data[i:i+4])[0]
        crc ^= word
        
        for _ in range(32):
            if crc & 0x80000000:
                crc = ((crc << 1) ^ poly) & 0xFFFFFFFF
            else:
                crc = (crc << 1) & 0xFFFFFFFF
    return crc

def patch_firmware(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found!")
        return False

    with open(file_path, 'rb') as f:
        fw_data = bytearray(f.read())

    file_size = len(fw_data)
    print(f"--- Processing firmware: {file_path} ---")
    print(f"Current file size: {file_size} bytes.")

    # Check Magic Number at the beginning (must be 'STM3')
    if fw_data[0:4] != b'STM3':
        print("Error: Invalid Magic Number 'STM3' at file start!")
        return False

    # 1. Write file size at address 0x04 (Little Endian, 4 bytes)
    fw_data[4:8] = struct.pack('<I', file_size)

    # 2. Cut firmware body for CRC (everything AFTER 64 bytes of header)
    fw_body = fw_data[64:]
    
    # 3. Calculate hardware CRC32 for STM32
    calculated_crc = stm32_crc32(fw_body)
    print(f"Calculated hardware CRC32: 0x{calculated_crc:08X}")

    # 4. Write CRC32 at address 0x08 (Little Endian, 4 bytes)
    fw_data[8:12] = struct.pack('<I', calculated_crc)

    with open(file_path, 'wb') as f:
        f.write(fw_data)

    print("Firmware header successfully patched with size and CRC32!")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # sys.argv[1] is the file path passed from Keil macro
        patch_firmware(sys.argv[1])
        shutil.copy(sys.argv[1], "g:\\app_firmware.bin")
        
    else:
        print("Usage: python test.py <path_to_file.bin>")
