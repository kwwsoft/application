#include <stdint.h>

// Вирівнюємо структуру на 64 байти, щоб вона чітко зайняла весь виділений простір
typedef struct __attribute__((packed)) {
    uint32_t magic_number;     // 4 байти: унікальний маркер 
    uint32_t file_size;        // 4 байти: точний розмір бінарника (пропише скрипт на ПК)
    uint32_t firmware_crc32;   // 4 байти: CRC32 всього тіла програми (пропише скрипт на ПК)
    
    // Версія ПЗ (Semantic Versioning)
    uint8_t  ver_major;        // 1 байт
    uint8_t  ver_minor;        // 1 байт
    uint8_t  ver_patch;        // 1 байт
    uint8_t  reserved1;        // 1 байт (вирівнювання)
    uint32_t ver_build;        // 4 байти: номер збірки

    char     hardware_id[16];  // 16 байт: ідентифікатор плати (наприклад, "STM32F103_CBT6")
    
    uint8_t  reserved2[28];    // 24 байти: пусті резервні байти, щоб добити розмір рівно до 64 байт
} FirmwareHeader_t;
