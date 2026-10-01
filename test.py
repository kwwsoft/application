# -*- coding: utf-8 -*-
import struct
import sys
import os
import shutil
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

# =========================================================================
# КРИТИЧНО: Цей ключ має ТОЧНО збігатися з константою BOOTLOADER_AES_KEY в STM32!
# Розмір суворо 16 байт (128 біт)
STATIC_AES_KEY = b'\x55\xCC\x1A\x83\xF2\x6E\xBB\x04\x9D\x41\x7A\xCE\x8B\x3F\x62\x94'
# =========================================================================

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

    print(f"--- Encrypting firmware with STATIC KEY: {file_path} ---")

    # 1. Записуємо тимчасові нулі на місце clean_crc32 (зміщення 16)
    fw_data[16:20] = b'\x00\x00\x00\x00'

    # 2. Безпека: ЗАБИВАЄМО поле ключа в хедері (зміщення 32..48) байтами 0xFF
    # Тепер ключ ніколи не потрапить у бінарний файл оновлення!
    fw_data[32:48] = b'\xFF' * 16

    # 3. Генеруємо випадкові 16 байт IV (Вектор ініціалізації)
    # Він залишається динамічним для захисту від атаки повторення
    iv = get_random_bytes(16)
    fw_data[48:64] = iv

    # 4. Вирізаємо чисте тіло програми (все, що після 64 байт хедера)
    fw_body_to_encrypt = bytearray(fw_data[64:])

    # 5. ВИРІВНЮВАННЯ AES (Дописуємо пусті байти ДО розрахунку clean_crc32)
    pad_len = 16 - (len(fw_body_to_encrypt) % 16)
    if pad_len != 16:
        fw_body_to_encrypt += b'\xFF' * pad_len

    # 6. РАХУЄМО CLEAN CRC32 від вирівняного чистого тіла
    clean_crc32 = stm32_crc32(bytes(fw_body_to_encrypt))
    print(f"Calculated Clean (Aligned) CRC32: 0x{clean_crc32:08X}")

    # Записуємо фінальний clean_crc32 в структуру хедера (зміщення 16..20)
    fw_data[16:20] = struct.pack('<I', clean_crc32)

    # 7. ШИФРУЄМО ТІЛО ПРОГРАМИ СТАТИЧНИМ КЛЮЧЕМ
    cipher = AES.new(STATIC_AES_KEY, AES.MODE_CBC, iv)
    encrypted_body = cipher.encrypt(bytes(fw_body_to_encrypt))

    # 8. Оновлюємо фінальний розмір файлу (Хедер 64 байти + Зашифроване тіло)
    final_size = 64 + len(encrypted_body)
    fw_data[4:8] = struct.pack('<I', final_size)

    # 9. Рахуємо апаратний CRC32 від вже ЗАШИФРОВАНОГО тіла програми (для XMODEM контролю)
    encrypted_crc32 = stm32_crc32(encrypted_body)
    fw_data[8:12] = struct.pack('<I', encrypted_crc32)
    print(f"New Encrypted Size: {final_size} bytes. Encrypted CRC32: 0x{encrypted_crc32:08X}")

    # Збираємо фінальний файл: Оновлений Хедер (без ключа всередині!) + Зашифроване тіло
    final_fw = fw_data[0:64] + encrypted_body

    with open(file_path, 'wb') as f:
        f.write(final_fw)

    print("Firmware successfully ENCRYPTED via Static Key and dual-CRC patched!")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        patch_and_encrypt_firmware(sys.argv[1])
        # Копіюємо на флешку/папку для Tera Term
        try:
            shutil.copy(sys.argv[1], "g:\\app_firmware.bin")
            print("Copied to G:\\ successfully.")
        except Exception as e:
            print(f"Warning: Could not copy to G:\\ ({e})")
        
    else:
        print("Usage: python test.py <path_to_file.bin>")
