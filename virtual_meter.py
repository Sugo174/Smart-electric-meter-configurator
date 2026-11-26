"""Счётчик из выгрузки EMIS. Все операции выполняются в памяти."""

from datetime import datetime, timedelta
from time import monotonic
from types import SimpleNamespace

import minimalmodbus

from constants import (
    BAUD_CODE_FROM_VAL, BAUD_VAL_FROM_CODE, PARITY_MAP, PARITY_STR_TO_VAL, PARITY_VAL_TO_STR,
    REG_BAUD_CODE, REG_CURRENT, REG_CURRENT_CH1, REG_CURRENT_CH2, REG_LOCAL_ADDR, REG_PARITY,
    REG_POWER, REG_POWER_CH1, REG_POWER_CH2, REG_PULSE_CONSTANT_CH1, REG_PULSE_CONSTANT_CH2,
    REG_TARIFF_SCHEDULE_START, REG_TIME_START, REG_VOLTAGE, REG_VOLTAGE_CH1, REG_VOLTAGE_CH2,
    TARIFF_SCHEDULE_RECORD_COUNT,
)


class VirtualMeter:
    def __init__(self, snapshot):
        connection = snapshot["Подключение"]
        settings = snapshot["Настройки прибора"]
        channels = settings["Каналы"]
        count = settings["Число каналов"]
        if type(count) is not int or count not in (1, 2) or set(channels) != set("AB"[:count]):
            raise ValueError("В выгрузке указаны несовместимые данные о каналах.")
        self.device_type = "single" if count == 1 else "dual"
        self.slave = int(connection["Адрес Modbus"])
        self.baud = int(connection["Скорость, бит/с"])
        self.parity = connection["Чётность"]
        if not 1 <= self.slave <= 254 or self.baud not in BAUD_CODE_FROM_VAL or self.parity not in PARITY_MAP:
            raise ValueError("В выгрузке указаны неподдерживаемые параметры Modbus.")

        self._clock = datetime.fromisoformat(snapshot["Дата и время счётчика"])
        if not 2000 <= self._clock.year <= 2099:
            raise ValueError("Год в выгрузке находится вне диапазона счётчика.")
        self._clock_started = monotonic()
        self.serial = SimpleNamespace(close=lambda: None, is_open=True)
        self._words = {
            REG_LOCAL_ADDR: self.slave,
            REG_BAUD_CODE: BAUD_CODE_FROM_VAL[self.baud],
            REG_PARITY: PARITY_STR_TO_VAL[self.parity],
            0xA00D: round(float(settings["Порог чувствительности напряжения, %"]) * 10),
            0xA00E: round(float(settings["Порог чувствительности тока, %"]) * 10),
            0xA011: int(settings["Десятичные знаки энергии на дисплее"]),
            0xA00B: int(snapshot.get("Дополнительные регистры", {})
                        .get("Знак действительных значений", {}).get("Слово регистра", 0)),
        }
        tariff = snapshot["Тарифное расписание"]["Исходные регистры"]
        if not isinstance(tariff, list) or len(tariff) != TARIFF_SCHEDULE_RECORD_COUNT * 2:
            raise ValueError("В выгрузке нет полного тарифного расписания.")
        if any(type(word) is not int or not 0 <= word <= 65535 for word in tariff):
            raise ValueError("В выгрузке есть некорректные регистры тарифного расписания.")
        self._store(REG_TARIFF_SCHEDULE_START, tariff)
        for index, letter in enumerate("AB"[:count]):
            row = channels[letter]
            voltage = round(float(row["Номинальное напряжение, В"]) * 100)
            current = round(float(row["Максимальный ток, А"]) * 100)
            pulse = int(row["Постоянная импульсного выхода, имп/кВт·ч"])
            self._store_u32(0x2048 + 2 * index, voltage)
            self._store_u32(0x204C + 2 * index, current)
            self._store_u32(0xA007 + 2 * index, current)
            self._store_u32((REG_PULSE_CONSTANT_CH1, REG_PULSE_CONSTANT_CH2)[index], pulse)
            if index == 0:
                self._store_u32(0x001A, voltage)
                self._store_u32(0x001C, current)

        for address in (REG_VOLTAGE, REG_CURRENT, REG_POWER, 0x001E, 0x0000, 0x000A,
                        REG_VOLTAGE_CH1, REG_CURRENT_CH1, REG_POWER_CH1, 0x2000, 0x2014, 0x2028,
                        REG_VOLTAGE_CH2, REG_CURRENT_CH2, REG_POWER_CH2, 0x2002, 0x2016, 0x202A):
            self._store_u32(address, 0)

        info = snapshot["Сведения о приборе"]
        service = snapshot.get("Сервисное инфо", {})
        for address, words, data, name in (
            (0xABB0, 8, info, "Серийный номер"),
            (0xABB8, 8, info, "Производитель"),
            (0xABC0, 8, info, "Тип счётчика"),
            (0xABC8, 8, info, "Версия метрологического ПО"),
            (0xABD0, 8, info, "Дата"),
            (0xAB90, 8, service, "Тех. версия ПО"),
            (0xABA0, 8, service, "Дата компиляции тех. ПО"),
            (0xABA8, 8, service, "Тех. версия протокола"),
            (0xABF0, 16, service, "Тег прибора"),
            (0xAB80, 16, service, "Тех. модель счётчика"),
        ):
            text = str(data.get(name) or "").encode("ascii", errors="replace")
            data_bytes = text[:words * 2].ljust(words * 2, b"\x00")
            self._store(address, [int.from_bytes(data_bytes[i:i + 2], "big") for i in range(0, len(data_bytes), 2)])

    def __str__(self):
        return "EMIS Virtual Meter"

    def _store(self, address, words):
        self._words.update((address + index, word) for index, word in enumerate(words))

    def _store_u32(self, address, value):
        if not 0 <= value <= 0xFFFFFFFF:
            raise ValueError("Значение в выгрузке выходит за пределы регистра.")
        self._store(address, [value >> 16, value & 0xFFFF])

    def connect(self, slave, baud, parity_letter):
        speed = BAUD_VAL_FROM_CODE.get(self._words[REG_BAUD_CODE])
        parity = PARITY_VAL_TO_STR.get(self._words[REG_PARITY])
        if (slave, baud, parity_letter) != (self._words[REG_LOCAL_ADDR], speed, PARITY_MAP.get(parity)):
            raise minimalmodbus.NoResponseError("Параметры виртуального подключения не совпадают.")
        return self

    def read_registers(self, address, count, functioncode=3):
        if address == REG_TIME_START and count == 3:
            current_time = self._clock + timedelta(seconds=int(monotonic() - self._clock_started))
            encoded = bytes.fromhex(current_time.strftime("%y%m%d%H%M%S"))
            return [int.from_bytes(encoded[i:i + 2], "big") for i in (0, 2, 4)]
        return [self._words.get(address + index, 0) for index in range(count)]

    def read_register(self, address, number_of_decimals=0, functioncode=3):
        value = self.read_registers(address, 1, functioncode)[0]
        return value / 10 ** number_of_decimals if number_of_decimals else value

    def write_registers(self, address, values):
        if address == REG_TIME_START:
            digits = b"".join(word.to_bytes(2, "big") for word in values).hex()
            self._clock = datetime.strptime("20" + digits, "%Y%m%d%H%M%S")
            self._clock_started = monotonic()
        self._store(address, values)
        if address in (0xA007, 0xA009) and len(values) == 2:
            self._store(0x204C + (address - 0xA007), values)
            if address == 0xA007:
                self._store(0x001C, values)

    def write_register(self, address, value, functioncode=6):
        self.write_registers(address, [value])
