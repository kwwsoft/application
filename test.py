# -*- coding: utf-8 -*-
import struct
import sys
import os
import shutil
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

def stm32_crc32(data: bytes) -> int:
    crc = 0xFFFFFFFF
    poly = 0x04C11DB7
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

    file_size = len(fw_data)
    print(f"--- Encrypting firmware: {file_path} ---")

    if fw_data[0:4] != b'STM3':
        print("Error: Invalid Magic Number!")
        return False

    # 1. Генеруємо випадкові 16 байт ключа та 16 байт IV
    key = get_random_bytes(16)
    iv = get_random_bytes(16)

    # Записуємо їх у хедер прошивки (Ключ з 32-го байта, IV з 48-го байта)
    fw_data[32:48] = key
    fw_data[48:64] = iv

    # 2. Вирізаємо чисте тіло програми (все, що після 64 байт хедера)
    fw_body = bytes(fw_data[64:])

    # AES вимагає, щоб дані були кратні 16 байтам (Pad за стандартом PKCS7)
    pad_len = 16 - (len(fw_body) % 16)
    if pad_len != 16:
        fw_body += b'\xFF' * pad_len # Добиваємо пустими байтами заліза

    # 3. ШИФРУЄМО ТІЛО ПРОГРАМИ
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted_body = cipher.encrypt(fw_body)

    # 4. Оновлюємо фінальний розмір файлу (Хедер 64 + зашифроване тіло)
    final_size = 64 + len(encrypted_body)
    fw_data[4:8] = struct.pack('<I', final_size)

    # 5. Рахуємо CRC32 від ЗАШИФРОВАНОГО тіла програми
    calculated_crc = stm32_crc32(encrypted_body)
    fw_data[8:12] = struct.pack('<I', calculated_crc)
    print(f"New Encrypted Size: {final_size} bytes. Encrypted CRC32: 0x{calculated_crc:08X}")

    # Збираємо фінальний файл: Хедер (де вже лежать Ключ та IV) + Зашифроване тіло
    final_fw = fw_data[0:64] + encrypted_body

    with open(file_path, 'wb') as f:
        f.write(final_fw)

    print("Firmware successfully ENCRYPTED and header patched!")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        patch_and_encrypt_firmware(sys.argv[1])
        shutil.copy(sys.argv[1], "g:\\app_firmware.bin")
        
    else:
        print("Usage: python test.py <path_to_file.bin>")
