# -*- coding: utf-8 -*-
import struct
import sys
import os
import shutil
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

def stm32_crc32(data: bytes) -> int:
    """Calculate hardware CRC32 aligned strictly with STM32 Little Endian memory"""
    crc = 0xFFFFFFFF
    poly = 0x04C11DB7
    
    # Fill remaining bytes with 0xFF if not aligned to 4 bytes
    remainder = len(data) % 4
    if remainder != 0:
        data += b'\xFF' * (4 - remainder)
        
    for i in range(0, len(data), 4):
        word = struct.unpack('<I', data[i:i+4])[0]
        crc ^= word
        for _ in range(32):
            if crc & 0x80000000:
                crc = ((crc << 1) ^ poly) & 0xFFFFFFFF
            else:
                crc = (crc << 1) & 0xFFFFFFFF
    return crc

def patch_and_encrypt_firmware(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found!")
        return False

    with open(file_path, 'rb') as f:
        fw_data = bytearray(f.read())

    if fw_data[0:4] != b'STM3':
        print("Error: Invalid Magic Number!")
        return False

    print(f"--- Encrypting firmware: {file_path} ---")

    # 1. Рахуємо CRC32 від ЧИСТОГО (незашифрованого) тіла програми
    # Тіло програми починається після 64 байт хедера
    clean_body = bytes(fw_data[64:])
    clean_crc32 = stm32_crc32(clean_body)
    print(f"Calculated Clean (Decrypted) CRC32: 0x{clean_crc32:08X}")

    # ?? ТОЧНА АДРЕСА: Записуємо clean_crc32 строго за зміщенням 16..20 (замість колишнього ver_build)
    fw_data[16:20] = struct.pack('<I', clean_crc32)

    # 2. Генеруємо випадкові 16 байт ключа та 16 байт IV
    key = get_random_bytes(16)
    iv = get_random_bytes(16)

    # Записуємо їх у хедер (Ключ з 32-го байта, IV з 48-го байта)
    fw_data[32:48] = key
    fw_data[48:64] = iv

    # 3. Готуємо тіло програми до шифрування (вирівнювання AES під 16 байт)
    fw_body_to_encrypt = bytes(fw_data[64:])
    pad_len = 16 - (len(fw_body_to_encrypt) % 16)
    if pad_len != 16:
        fw_body_to_encrypt += b'\xFF' * pad_len

    # 4. ШИФРУЄМО ТІЛО ПРОГРАМИ
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted_body = cipher.encrypt(fw_body_to_encrypt)

    # 5. Оновлюємо фінальний розмір файлу
    final_size = 64 + len(encrypted_body)
    fw_data[4:8] = struct.pack('<I', final_size)

    # 6. Рахуємо CRC32 від вже ЗАШИФРОВАНОГО тіла програми
    encrypted_crc32 = stm32_crc32(encrypted_body)
    fw_data[8:12] = struct.pack('<I', encrypted_crc32)
    print(f"New Encrypted Size: {final_size} bytes. Encrypted CRC32: 0x{encrypted_crc32:08X}")

    # Збираємо фінальний файл: Оновлений Хедер + Зашифроване тіло
    final_fw = fw_data[0:64] + encrypted_body

    with open(file_path, 'wb') as f:
        f.write(final_fw)

    print("Firmware successfully ENCRYPTED and dual-CRC patched!")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        patch_and_encrypt_firmware(sys.argv[1])
        shutil.copy(sys.argv[1], "g:\\app_firmware.bin")
        
    else:
        print("Usage: python test.py <path_to_file.bin>")
