#include <stdint.h>

// Вирівнюємо структуру на 64 байти, щоб вона чітко зайняла весь виділений простір
typedef struct __attribute__((packed)) {
    uint32_t magic_number;     // 4 байти (0x334D5453 -> "STM3")
    uint32_t file_size;        // 4 байти (розмір файлу)
    uint32_t firmware_crc32;   // 4 байти (CRC32 зашифрованого (!) тіла)
    
    // Версія ПЗ
    uint8_t  ver_major;        // 1 байт
    uint8_t  ver_minor;        // 1 байт
    uint8_t  ver_patch;        // 1 байт
    uint8_t  reserved1;        // 1 байт
    uint32_t clean_crc32;      // ?? 4 байти (Тут тепер живе CRC32 чистого коду!)

    char     hardware_id[12];  // 12 байт (трохи урізали рядок, щоб звільнити місце)
    
    // ?? КРИПТО-ПАСПОРТ (Разом 32 байти)
    uint8_t  aes_key[16];      // 16 байт ключа (тимчасово заповнить Python)
    uint8_t  aes_iv[16];       // 16 байт вектора IV (тимчасово заповнить Python)
} FirmwareHeader_t;
//#pragma pack(pop)
