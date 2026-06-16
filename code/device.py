"""
Модуль работы с конфигуратором ЭМИС ModBus СКВТ.

Версия: 1.08  
Назначение: Низкоуровневое взаимодействие с устройством по протоколу ModBus RTU.  
Все функции возвращают кортеж (успех: bool, результат_или_ошибка: str/dict).

Примечание:
    Этот модуль не зависит от GUI. Его можно использовать в консольных скриптах,
    тестах или других интерфейсах.
"""

# =============================================================================
# 1. Импорты
# =============================================================================

import minimalmodbus
import serial
import time
import datetime

from constants import (
    REG_EN_PROG,
    REG_LOCAL_ADDR,
    REG_BAUD_CODE,
    REG_TIME_START,
    REG_VOLTAGE,
    REG_CURRENT,
    REG_POWER,
    REG_VOLTAGE_CH1,
    REG_VOLTAGE_CH2,
    REG_CURRENT_CH1,
    REG_CURRENT_CH2,
    REG_POWER_CH1,
    REG_POWER_CH2,
    VOLTAGE_FACTOR,
    CURRENT_FACTOR,
    POWER_FACTOR,
    BAUD_VALUES,
    BAUD_CODE_FROM_VAL,
    BAUD_VAL_FROM_CODE,
    PARITY_MAP,
    REG_PARITY,
    PARITY_VAL_TO_STR,
    PARITY_STR_TO_VAL,
    ENERGY_FACTOR,
    REG_ENERGY_CLEAR
)


# =============================================================================
# 2. Вспомогательные утилиты
# =============================================================================

def list_com_ports():
    """Возвращает только те COM-порты, которые реально можно открыть."""
    import serial.tools.list_ports # Импорт портов на время вызова функции
    available = [] # Создаем пустой список для списка портов
    for p in serial.tools.list_ports.comports(): 
        try:
            with serial.Serial(p.device, timeout=0.1):
                # Открываем порт на 0,1с, что бы проверить работает ли он
                pass
            available.append(p.device)
        except (OSError, serial.SerialException):
            # Порт есть, но не открывается — пропускаем
            pass
    return available # Возвращаем список имён портов, которые удалось открыть


def make_instrument(port, slave, baud, parity_letter):
    """
    Создаёт и настраивает объект minimalmodbus.Instrument для работы с устройством.
    Параметры:
        port (str): Имя COM-порта (например, "COM3")
        slave (int): Адрес устройства ModBus (1–247)
        baud (int): Скорость передачи (1200, 2400, ..., 19200)
        parity_letter (str): Чётность — "E" (Even), "O" (Odd), "N" (None)

    Возвращает:
        minimalmodbus.Instrument: Настроенный объект для обмена данными.
    """
    dev = minimalmodbus.Instrument(port, slave, mode=minimalmodbus.MODE_RTU)
    dev.serial.baudrate = baud
    dev.serial.bytesize = 8
    dev.serial.parity = parity_letter  
    dev.serial.stopbits = 1
    dev.serial.timeout = 1.5
    dev.clear_buffers_before_each_transaction = True
    return dev

# =============================================================================
# 3. Работа с BCD (двоично-десятичный код)
# Устройство хранит дату/время в формате BCD: 1 байт = 2 десятичные цифры.
# =============================================================================

def bcd_to_int(b):
    """Преобразует байт из BCD-формата в целое число.

    Пример: 0x25 → 25 (а не 37 в десятичной системе).

    Args:
        b (int): Байт в BCD-формате.

    Returns:
        int: Преобразованное десятичное число.

    Raises:
        ValueError: Если байт содержит недопустимые цифры (>9).
    """
    hi, lo = (b >> 4) & 0xF, b & 0xF # Распаковка кортежа, пишем сразу две перменные
    if hi > 9 or lo > 9:
        raise ValueError(f"Некорректный BCD-байт: 0x{b:02X}")
    return hi * 10 + lo


def int_to_bcd(x):
    """Преобразует целое число (0–99) в BCD-байт.

    Пример: 25 → 0x25.

    Args:
        x (int): Целое число в диапазоне 0–99.

    Returns:
        int: BCD-байт.

    Raises:
        ValueError: Если число вне диапазона 0–99.
    """
    if not (0 <= x <= 99):
        raise ValueError("BCD поддерживает только числа от 0 до 99")
    return ((x // 10) << 4) | (x % 10) # Склеиваем старший и младший байты и возвращаем BCD


# =============================================================================
# 4. Основные функции взаимодействия с устройством
# Все функции изолированы, не имеют побочных эффектов и безопасны для вызова.
# =============================================================================

def scan_device(port, preferred_slave, preferred_baud, preferred_parity):
    """Сканирует COM-порт. Возвращает РЕАЛЬНЫЕ параметры, читая 0xA004."""    
    if not port or port == "(нет портов)":
        return False, "COM-порт не выбран"

    try:
        test = serial.Serial(port, baudrate=9600, timeout=0.05)
        test.close()
    except (OSError, serial.SerialException, FileNotFoundError, serial.PortNotOpenError):
        return False, f"Порт {port} недоступен. Проверьте подключение."
    except Exception as e:
        return False, f"Ошибка доступа к порту: {e}" 

    try_bauds = [preferred_baud] + [b for b in BAUD_VALUES if b != preferred_baud]
    try_slaves = [preferred_slave] + [s for s in range(1, 11) if s != preferred_slave]
    try_pars = [preferred_parity] + [p for p in PARITY_MAP.keys() if p != preferred_parity]

    start_time = time.time()
    MAX_DURATION = 40.0
    best_match = None
    
    for ptxt in try_pars:
        if time.time() - start_time > MAX_DURATION: break
        parity_mode = PARITY_MAP[ptxt]
        for b in try_bauds:
            if time.time() - start_time > MAX_DURATION: break
            for s in try_slaves:
                if time.time() - start_time > MAX_DURATION: break

                dev = None
                try:
                    dev = make_instrument(port, s, b, parity_mode)
                    dev.serial.timeout = 0.15
                    dev.read_register(REG_LOCAL_ADDR, 0, functioncode=3)
                    time.sleep(0.05)
                    dev.read_register(REG_LOCAL_ADDR, 0, functioncode=3) # Двойная проверка
                    best_match = (b, s, ptxt)
                    break
                except Exception:
                    continue
                finally:
                    if dev is not None:
                        try: dev.serial.close()
                        except: pass
                    time.sleep(0.1)
            if best_match: break
        if best_match: break

    if not best_match:
        return False, "Устройство не отвечает. Проверьте питание и подключение."

    found_baud, found_slave, found_parity_txt = best_match
    actual_slave = found_slave
    actual_baud = found_baud
    actual_parity = found_parity_txt # fallback
    
    try:
        dev = make_instrument(port, found_slave, found_baud, PARITY_MAP[found_parity_txt])
        dev.serial.timeout = 0.2
        
        try: actual_slave = dev.read_register(REG_LOCAL_ADDR, 0, functioncode=3)
        except: pass
        
        try:
            code = dev.read_register(REG_BAUD_CODE, 0, functioncode=3)
            actual_baud = BAUD_VAL_FROM_CODE.get(code, found_baud)
        except: pass

        # Читаем реальную четность 
        try:
            parity_reg_val = dev.read_register(0xA003, 0, functioncode=3)
            actual_parity = PARITY_VAL_TO_STR.get(parity_reg_val, found_parity_txt)
        except Exception:
            pass  # Игнорируем ошибку чтения, используем найденную чётность
            
        dev.serial.close()
    except: pass

    return True, {
        "port": port,
        "slave": actual_slave,
        "baud": actual_baud,
        "parity": actual_parity,
    }


def write_device_settings(port, slave, baud, parity, new_slave, new_baud, new_parity):
    """
    Записывает адрес (0xA001), скорость (0xA002) и четность (0xA003/40963).
    Все параметры связи отправляются ОДНИМ запросом.
    """
    parity_letter = PARITY_MAP.get(new_parity, "E")
    new_code = BAUD_CODE_FROM_VAL.get(new_baud, 3)
    current_parity_letter = PARITY_MAP.get(parity, "E")
    new_parity_val = PARITY_STR_TO_VAL.get(new_parity, 2)

    dev_write = None
    dev_check = None
    
    try:
        # 1. Подключаемся по СТАРЫМ (рабочим) параметрам
        dev_write = make_instrument(port, slave, baud, current_parity_letter)
        dev_write.serial.timeout = 1.0

        # 2. Разблокировка записи
        dev_write.write_register(0xA000, 0x5AA5, functioncode=6)
        time.sleep(0.15)

        # 3. Записываем ВСЕ параметры связи ОДНИМ запросом
        dev_write.write_registers(0xA001, [new_slave, new_code, new_parity_val])
        time.sleep(0.1)

        # 4. Корректное закрытие порта (без двойного close)
        if dev_write and dev_write.serial:
            try:
                if dev_write.serial.is_open:
                    dev_write.serial.close()
            except:
                pass
        dev_write = None  # Явно обнуляем ссылку

        # 5. Ждем переконфигурацию UART прибора
        time.sleep(3.0)

        # 6. Переподключаемся по НОВЫМ параметрам для проверки
        dev_check = make_instrument(port, new_slave, new_baud, parity_letter)
        dev_check.serial.timeout = 1.5

        # Пробуем прочитать (3 попытки)
        for attempt in range(3):
            try:
                verify_slave = dev_check.read_register(0xA001, 0, functioncode=3)
                verify_code = dev_check.read_register(0xA002, 0, functioncode=3)
                verify_baud = BAUD_VAL_FROM_CODE.get(verify_code, new_baud)
                return True, {"slave": verify_slave, "baud": verify_baud, "parity": new_parity}
            except Exception as e:
                if attempt < 2:
                    time.sleep(0.5)
                    continue
                raise e

    except Exception as e:
        return False, f"Ошибка: {str(e)}"
    
    finally:
        # Безопасное закрытие всех портов (защита от hEvent)
        for dev in [dev_write, dev_check]:
            if dev is not None:
                try:
                    if hasattr(dev, 'serial') and dev.serial is not None:
                        if dev.serial.is_open:
                            dev.serial.close()
                except Exception:
                    pass  # Игнорируем ошибки закрытия
        # Гарантированно обнуляем ссылки
        dev_write = None
        dev_check = None


def read_device_time(port, slave, baud, parity):
    """Читает дату и время из регистров 0xB001–0xB003 (формат BCD).

    Структура регистров:
        - 0xB001: [YY][MM] → год (2 цифры), месяц
        - 0xB002: [DD][HH] → день, час
        - 0xB003: [mm][SS] → минуты, секунды

    Args:
        port (str): COM-порт.
        slave (int): Адрес устройства.
        baud (int): Скорость передачи.
        parity (str): Чётность.

    Returns:
        tuple: (успех, результат)
            - bool: True при успехе.
            - dict или str: При успехе — словарь с "formatted" и "data";
              при ошибке — описание.
    """
    try:
        dev = make_instrument(port, slave, baud, PARITY_MAP[parity])
        try:
            regs = dev.read_registers(REG_TIME_START, 3, functioncode=3)
            YY = bcd_to_int((regs[0] >> 8) & 0xFF)
            MM = bcd_to_int(regs[0] & 0xFF)
            DD = bcd_to_int((regs[1] >> 8) & 0xFF)
            HH = bcd_to_int(regs[1] & 0xFF)
            mm = bcd_to_int((regs[2] >> 8) & 0xFF)
            SS = bcd_to_int(regs[2] & 0xFF)
            year_full = 2000 + YY
            formatted = f"{year_full:04}-{MM:02}-{DD:02} {HH:02}:{mm:02}:{SS:02}"
            time_data = {
                "year": year_full,
                "month": MM,
                "day": DD,
                "hour": HH,
                "minute": mm,
                "second": SS,
            }
            return True, {"formatted": formatted, "data": time_data}
        finally:
            dev.serial.close()
    except Exception as e:
        return False, str(e)

    
def write_device_time(port, slave, baud, parity, year, month, day, hour, minute, second):
    """Записывает дату и время в регистры 0xB001–0xB003 (в формате BCD).

    Args:
        port (str): COM-порт.
        slave (int): Адрес устройства.
        baud (int): Скорость передачи.
        parity (str): Чётность.
        year (int): Год (2025–2099).
        month (int): Месяц (1–12).
        day (int): День (1–31).
        hour (int): Час (0–23).
        minute (int): Минута (0–59).
        second (int): Секунда (0–59).

    Returns:
        tuple: (успех, результат)
            - bool: True при успехе.
            - str: "OK" или описание ошибки.
    """
    if not (2025 <= year <= 2099):
        return False, "Год должен быть в диапазоне 2025–2099 (устройство не поддерживает другие значения)"
    if not (1 <= month <= 12):
        return False, "Месяц должен быть от 1 до 12"
    if not (1 <= day <= 31):
        return False, "День должен быть от 1 до 31"
    if not (0 <= hour <= 23):
        return False, "Час должен быть от 0 до 23"
    if not (0 <= minute <= 59):
        return False, "Минута должна быть от 0 до 59"
    try:
        YY = year - 2000
        reg1 = (int_to_bcd(YY) << 8) | int_to_bcd(month)
        reg2 = (int_to_bcd(day) << 8) | int_to_bcd(hour)
        reg3 = (int_to_bcd(minute) << 8) | int_to_bcd(second)
        dev = make_instrument(port, slave, baud, PARITY_MAP[parity])
        try:
            dev.write_register(REG_EN_PROG, 0x5AA5, functioncode=6)
            time.sleep(0.1)
            dev.write_registers(REG_TIME_START, [reg1, reg2, reg3])
            return True, "OK"
        finally:
            dev.serial.close()
    except Exception as e:
        return False, str(e)


def sync_device_with_pc_time(port, slave, baud, parity):
    """Синхронизирует время устройства с текущим временем ПК.

    Returns:
        tuple: (успех, результат)
            - bool: True при успехе.
            - str: Время в формате "ГГГГ-ММ-ДД ЧЧ:ММ:СС" или описание ошибки.
    """
    now = datetime.datetime.now()
    success, msg = write_device_time(
        port, slave, baud, parity,
        now.year, now.month, now.day,
        now.hour, now.minute, now.second,
    )
    if success:
        return True, now.strftime("%Y-%m-%d %H:%M:%S")
    else:
        return False, msg


def read_device_parameters(port, slave, baud, parity):
    """Чтение параметров одноканального счётчика."""
    try:
        dev = make_instrument(port, slave, baud, PARITY_MAP[parity])
        try:
            # Напряжение
            voltage_regs = dev.read_registers(REG_VOLTAGE, 2, functioncode=3)
            voltage_raw = (voltage_regs[0] << 16) | voltage_regs[1]
            voltage = voltage_raw * VOLTAGE_FACTOR

            # Ток
            current_regs = dev.read_registers(REG_CURRENT, 2, functioncode=3)
            current_raw = (current_regs[0] << 16) | current_regs[1]
            current = current_raw * CURRENT_FACTOR

            # Мощность
            power_regs = dev.read_registers(REG_POWER, 2, functioncode=3)
            power_raw = (power_regs[0] << 16) | power_regs[1]
            power = power_raw * POWER_FACTOR

            # Абсолютная активная энергия (0x001E)
            en_abs_regs = dev.read_registers(0x001E, 2, functioncode=3)
            en_abs_raw = (en_abs_regs[0] << 16) | en_abs_regs[1]
            if en_abs_raw >= 0x80000000:
                en_abs_raw -= 0x100000000
            en_abs = en_abs_raw * 0.01

            # Суммарная положительная активная энергия (0x0000)
            en_pos_regs = dev.read_registers(0x0000, 2, functioncode=3)
            en_pos_raw = (en_pos_regs[0] << 16) | en_pos_regs[1]
            en_pos = en_pos_raw * 0.01

            # Суммарная обратная активная энергия (0x000A)
            en_neg_regs = dev.read_registers(0x000A, 2, functioncode=3)
            en_neg_raw = (en_neg_regs[0] << 16) | en_neg_regs[1]
            en_neg = en_neg_raw * 0.01

            # Номинальное напряжение (0x001A)
            nom_v_regs = dev.read_registers(0x001A, 2, functioncode=3)
            nom_v_raw = (nom_v_regs[0] << 16) | nom_v_regs[1]
            nom_voltage = nom_v_raw * 0.01

            # Номинальный ток (0x001C)
            nom_i_regs = dev.read_registers(0x001C, 2, functioncode=3)
            nom_i_raw = (nom_i_regs[0] << 16) | nom_i_regs[1]
            nom_current = nom_i_raw * 0.01

            return True, {
                "voltage": voltage,
                "current": current,
                "power": power,
                "energy_abs": en_abs,
                "energy_pos": en_pos,
                "energy_neg": en_neg,
                "nom_voltage": nom_voltage,
                "nom_current": nom_current
            }
        finally:
            dev.serial.close()
    except Exception as e:
        return False, str(e)


def read_device_parameters_dual(port, slave, baud, parity):
    """Чтение параметров двухканального счётчика.

    Returns:
        tuple: (успех, результат)
            - bool: True при успехе.
            - dict или str: При успехе — словарь с данными по ch1 и ch2;
              при ошибке — описание.
    """
    try:
        dev = make_instrument(port, slave, baud, PARITY_MAP[parity])
        try:
            # Вспомогательная функция для чтения 32-битного значения с коэф. 0.01
            def _read_32(addr):
                regs = dev.read_registers(addr, 2, functioncode=3)
                return ((regs[0] << 16) | regs[1]) * 0.01

            # --- КАНАЛ 1 ---
            # Энергия
            ch1_abs = _read_32(0x2000)
            ch1_pos = _read_32(0x2014)
            ch1_neg = _read_32(0x2028)

            # Текущие параметры (как было)
            v1_regs = dev.read_registers(REG_VOLTAGE_CH1, 2, functioncode=3)
            v1 = ((v1_regs[0] << 16) | v1_regs[1]) * VOLTAGE_FACTOR

            i1_regs = dev.read_registers(REG_CURRENT_CH1, 2, functioncode=3)
            i1 = ((i1_regs[0] << 16) | i1_regs[1]) * CURRENT_FACTOR

            p1_regs = dev.read_registers(REG_POWER_CH1, 2, functioncode=3)
            p1 = ((p1_regs[0] << 16) | p1_regs[1]) * POWER_FACTOR

            # Номиналы
            ch1_nom_v = _read_32(0x2048)
            ch1_nom_i = _read_32(0x204C)

            # --- КАНАЛ 2 ---
            # Энергия
            ch2_abs = _read_32(0x2002)
            ch2_pos = _read_32(0x2016)
            ch2_neg = _read_32(0x202A)

            # Текущие параметры (как было)
            v2_regs = dev.read_registers(REG_VOLTAGE_CH2, 2, functioncode=3)
            v2 = ((v2_regs[0] << 16) | v2_regs[1]) * VOLTAGE_FACTOR

            i2_regs = dev.read_registers(REG_CURRENT_CH2, 2, functioncode=3)
            i2 = ((i2_regs[0] << 16) | i2_regs[1]) * CURRENT_FACTOR

            p2_regs = dev.read_registers(REG_POWER_CH2, 2, functioncode=3)
            p2 = ((p2_regs[0] << 16) | p2_regs[1]) * POWER_FACTOR

            # Номиналы
            ch2_nom_v = _read_32(0x204A)
            ch2_nom_i = _read_32(0x204E)

            return True, {
                "ch1": {
                    "voltage": v1, "current": i1, "power": p1,
                    "energy_abs": ch1_abs, "energy_pos": ch1_pos, "energy_neg": ch1_neg,
                    "nom_voltage": ch1_nom_v, "nom_current": ch1_nom_i
                },
                "ch2": {
                    "voltage": v2, "current": i2, "power": p2,
                    "energy_abs": ch2_abs, "energy_pos": ch2_pos, "energy_neg": ch2_neg,
                    "nom_voltage": ch2_nom_v, "nom_current": ch2_nom_i
                }
            }
        finally:
            dev.serial.close()
    except Exception as e:
        return False, str(e)


def clear_device_energy(port, slave, baud, parity):
    """
    Очищает значения накопленной электроэнергии (Табл. 5.2 и 5.3).
    Записывает 23041 (0x5A01) в регистр 0xB000.
    """
    try:
        dev = make_instrument(port, slave, baud, PARITY_MAP[parity])
        try:
            # Шаг 1: Запись ключа разрешения программирования
            dev.write_register(REG_EN_PROG, 0x5AA5, functioncode=6)
            time.sleep(0.1)

            # Шаг 2: Запись значения сброса в регистр B000
            dev.write_register(REG_ENERGY_CLEAR, 23041, functioncode=6)
            time.sleep(0.2)

            return True, "OK"
        finally:
            dev.serial.close()
    except Exception as e:
        return False, str(e)


def read_device_settings_params(port, slave, baud, parity, device_type):
    """Чтение параметров настроек прибора."""
    try:
        dev = make_instrument(port, slave, baud, PARITY_MAP[parity])
        try:
            # Максимальный ток канала А (0xA007)
            max_i_a_regs = dev.read_registers(0xA007, 2, functioncode=3)
            max_i_a_raw = (max_i_a_regs[0] << 16) | max_i_a_regs[1]
            max_i_a = max_i_a_raw * 0.01

            # Максимальный ток канала B (0xA009)
            max_i_b = None
            if device_type == "dual":
                max_i_b_regs = dev.read_registers(0xA009, 2, functioncode=3)
                max_i_b_raw = (max_i_b_regs[0] << 16) | max_i_b_regs[1]
                max_i_b = max_i_b_raw * 0.01

            # Порог чувствительности напряжения (0xA00D)
            sens_v_reg = dev.read_register(0xA00D, functioncode=3)
            sens_v = sens_v_reg * 0.1

            # Порог чувствительности тока (0xA00E)
            sens_i_reg = dev.read_register(0xA00E, functioncode=3)
            sens_i = sens_i_reg * 0.1

            # Отображение десятичных знаков (0xA011)
            decimal_places = dev.read_register(0xA011, functioncode=3)

            # Количество тарифных отрезков (0xA012)
            tariff_periods = dev.read_register(0xA012, functioncode=3)

            result = {
                "max_current_a": max_i_a,
                "sens_voltage": sens_v,
                "sens_current": sens_i,
                "decimal_places": decimal_places,
                "tariff_periods": tariff_periods
            }
            
            if device_type == "dual":
                result["max_current_b"] = max_i_b

            return True, result
        finally:
            dev.serial.close()
    except Exception as e:
        return False, str(e)


def read_device_info(port, slave, baud, parity):
    """Чтение информации о приборе."""
    try:
        dev = make_instrument(port, slave, baud, PARITY_MAP[parity])
        try:
            def _read_string(start_addr, max_bytes=16):
                """Читает строку до первого нуля или max_bytes."""
                num_regs = (max_bytes + 1) // 2  # Округляем вверх
                regs = dev.read_registers(start_addr, num_regs, functioncode=3)
                
                # Собираем все байты
                all_bytes = []
                for reg in regs:
                    all_bytes.append((reg >> 8) & 0xFF)
                    all_bytes.append(reg & 0xFF)
                
                # Ищем конец строки (первый ноль)
                end_idx = 0
                for i, b in enumerate(all_bytes):
                    if b == 0:
                        end_idx = i
                        break
                else:
                    end_idx = len(all_bytes)
                
                # Преобразуем в строку, оставляя только печатаемые символы
                text = []
                for b in all_bytes[:end_idx]:
                    if 32 <= b < 127:  # Печатаемые ASCII
                        text.append(chr(b))
                
                return ''.join(text).rstrip()

            # Читаем до 16 байт для каждого поля
            serial_number = _read_string(0xABB0, 16)
            manufacturer = _read_string(0xABB8, 16)
            meter_type = _read_string(0xABC0, 16)
            sw_version = _read_string(0xABC8, 16)
            release_date = _read_string(0xABD0, 16)
            
            return True, {
                "serial_number": serial_number,
                "manufacturer": manufacturer,
                "meter_type": meter_type,
                "sw_version": sw_version,
                "release_date": release_date
            }
        finally:
            dev.serial.close()
    except Exception as e:
        return False, str(e)


def write_max_current(port, slave, baud, parity, channel, value):
    """Запись максимального тока."""
    try:
        addr = 0xA007 if channel == 'a' else 0xA009
        raw_value = int(value / 0.01)
        
        dev = make_instrument(port, slave, baud, PARITY_MAP[parity])
        dev.write_register(0xA000, 0x5AA5, functioncode=6)
        time.sleep(0.2)
        dev.write_registers(addr, [(raw_value >> 16) & 0xFFFF, raw_value & 0xFFFF])
        time.sleep(0.2)
        dev.serial.close()
        return True, "OK"
    except Exception as e:
        return False, str(e)

def write_sensitivity_voltage(port, slave, baud, parity, value):
    """Запись порога чувствительности напряжения."""
    try:
        raw_value = int(value / 0.1)
        dev = make_instrument(port, slave, baud, PARITY_MAP[parity])
        dev.write_register(0xA000, 0x5AA5, functioncode=6)
        time.sleep(0.2)
        dev.write_register(0xA00D, raw_value, functioncode=6)
        time.sleep(0.2)
        dev.serial.close()
        return True, "OK"
    except Exception as e:
        return False, str(e)

def write_sensitivity_current(port, slave, baud, parity, value):
    """Запись порога чувствительности тока."""
    try:
        raw_value = int(value / 0.1)
        dev = make_instrument(port, slave, baud, PARITY_MAP[parity])
        dev.write_register(0xA000, 0x5AA5, functioncode=6)
        time.sleep(0.2)
        dev.write_register(0xA00E, raw_value, functioncode=6)
        time.sleep(0.2)
        dev.serial.close()
        return True, "OK"
    except Exception as e:
        return False, str(e)

def write_decimal_places(port, slave, baud, parity, value):
    """Запись количества десятичных знаков."""
    try:
        dev = make_instrument(port, slave, baud, PARITY_MAP[parity])
        dev.write_register(0xA000, 0x5AA5, functioncode=6)
        time.sleep(0.2)
        dev.write_register(0xA011, value, functioncode=6)
        time.sleep(0.2)
        dev.serial.close()
        return True, "OK"
    except Exception as e:
        return False, str(e)

def write_tariff_periods(port, slave, baud, parity, value):
    """Запись количества тарифных отрезков."""
    try:
        dev = make_instrument(port, slave, baud, PARITY_MAP[parity])
        dev.write_register(0xA000, 0x5AA5, functioncode=6)
        time.sleep(0.2)
        dev.write_register(0xA012, value, functioncode=6)
        time.sleep(0.2)
        dev.serial.close()
        return True, "OK"
    except Exception as e:
        return False, str(e)
