#include "stm32f10x.h"
#include "stm32f10x_gpio.h"
#include "stm32f10x_rcc.h"

// Проста функція затримки
void Delay(uint32_t count) {
    while(count--) {
        __NOP(); // Асемблерна пуста операція, щоб компілятор не оптимізував цикл
    }
}

int main(void) {
    // ?? КРИТИЧНО: Зміщуємо таблицю векторів на 10 КБ (0x2800)
    NVIC_SetVectorTable(NVIC_VectTab_FLASH, 0x2800);
    
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
