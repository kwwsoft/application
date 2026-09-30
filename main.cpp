#include "stm32f10x.h"
#include "stm32f10x_gpio.h"
#include "stm32f10x_rcc.h"
#include "firmware_header.h"

// ?? Надійна абсолютна адресація для Compiler V6 в C++. 
// Линкер сам зрозуміє адресу, і Scatter-файл її прийме без жодних попереджень.
extern "C" const FirmwareHeader_t my_fw_header __attribute__((section(".ARM.__at_0x08002800"))) = {
    // Завдяки Little Endian у бінарнику фізично запишеться: 53 54 4D 33 -> строго "STM3"
    .magic_number = 0x334D5453,        // "STM3"
    .file_size = 0x00000000,           // Заповнить скрипт на ПК
    .firmware_crc32 = 0x00000000,      // Заповнить скрипт на ПК
    .ver_major = 1,
    .ver_minor = 0,
    .ver_patch = 0,
    .reserved1 = 0,
    .ver_build = 01,                   // Номер білду
    .hardware_id = "STM32F103CB",   // Прив'язка до заліза
    .aes_key = {0},
		.aes_iv = {0}
};

// Проста функція затримки
void Delay(uint32_t count) {
    while(count--) {
        __NOP(); // Асемблерна пуста операція, щоб компілятор не оптимізував цикл
    }
}

int main(void) {

// ?? КРИТИЧНО: Зміщуємо таблицю векторів на 10 КБ (0x2800) + 64 bytes header
    NVIC_SetVectorTable(NVIC_VectTab_FLASH, 0x2840);
    
    // Ініціалізація периферії (на прикладі LED на PC13)
    GPIO_InitTypeDef GPIO_InitStructure;
    
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOC, ENABLE);
    
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_13;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOC, &GPIO_InitStructure);
    
    while(1) {
        // Миготимо у два рази швидше або повільніше, ніж зазвичай, 
        // щоб візуально відрізнити роботу Application від Bootloader
        GPIO_WriteBit(GPIOC, GPIO_Pin_13, (BitAction)(1 - GPIO_ReadOutputDataBit(GPIOC, GPIO_Pin_13)));
        Delay(500000); 
    }
}
