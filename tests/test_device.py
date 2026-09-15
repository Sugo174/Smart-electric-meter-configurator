"""Тесты вспомогательной логики взаимодействия со счётчиком."""

import unittest
from unittest.mock import patch

from constants import (
    BAUD_CODE_FROM_VAL,
    BAUD_VAL_FROM_CODE,
    BAUD_VALUES,
    PARITY_MAP,
    PARITY_STR_TO_VAL,
    PARITY_VAL_TO_STR,
)
from device import (
    bcd_to_int,
    int_to_bcd,
    registers_to_i32,
    write_decimal_places,
    write_max_current,
    write_sensitivity_current,
    write_sensitivity_voltage,
    write_tariff_periods,
)


class BCDConversionTests(unittest.TestCase):
    """Проверяет преобразование чисел в BCD и обратно."""

    def test_int_to_bcd(self) -> None:
        """Десятичные числа должны правильно преобразовываться в BCD."""
        test_cases = {
            0: 0x00,
            9: 0x09,
            10: 0x10,
            25: 0x25,
            59: 0x59,
            99: 0x99,
        }

        for decimal, expected_bcd in test_cases.items():
            with self.subTest(decimal=decimal):
                self.assertEqual(
                    int_to_bcd(decimal),
                    expected_bcd,
                )

    def test_bcd_to_int(self) -> None:
        """Корректные BCD-байты должны преобразовываться в числа."""
        test_cases = {
            0x00: 0,
            0x09: 9,
            0x10: 10,
            0x25: 25,
            0x59: 59,
            0x99: 99,
        }

        for bcd_value, expected_decimal in test_cases.items():
            with self.subTest(bcd_value=bcd_value):
                self.assertEqual(
                    bcd_to_int(bcd_value),
                    expected_decimal,
                )

    def test_all_supported_values_round_trip(self) -> None:
        """Каждое число от 0 до 99 должно восстановиться без изменений."""
        for value in range(100):
            with self.subTest(value=value):
                self.assertEqual(
                    bcd_to_int(int_to_bcd(value)),
                    value,
                )

    def test_int_to_bcd_rejects_out_of_range_values(self) -> None:
        """Числа за пределами диапазона BCD должны вызывать ошибку."""
        for value in (-1, 100):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    int_to_bcd(value)

    def test_bcd_to_int_rejects_invalid_digits(self) -> None:
        """BCD-байты с цифрами A–F должны вызывать ошибку."""
        for value in (0x0A, 0x1A, 0xA0, 0xFF):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    bcd_to_int(value)


class SignedIntegerConversionTests(unittest.TestCase):
    """Проверяет преобразование двух Modbus-регистров в I32."""

    def test_registers_to_i32(self) -> None:
        """Положительные и отрицательные значения должны читаться верно."""
        test_cases = {
            (0x0000, 0x0000): 0,
            (0x0000, 0x0001): 1,
            (0x7FFF, 0xFFFF): 2_147_483_647,
            (0xFFFF, 0xFFFF): -1,
            (0x8000, 0x0000): -2_147_483_648,
        }

        for registers, expected_value in test_cases.items():
            with self.subTest(registers=registers):
                self.assertEqual(
                    registers_to_i32(list(registers)),
                    expected_value,
                )


class CommunicationConstantTests(unittest.TestCase):
    """Проверяет согласованность параметров последовательного интерфейса."""

    def test_baud_rate_mappings_are_reversible(self) -> None:
        """Код скорости должен преобразовываться в исходную скорость."""
        for baud_rate in BAUD_VALUES:
            with self.subTest(baud_rate=baud_rate):
                baud_code = BAUD_CODE_FROM_VAL[baud_rate]

                self.assertEqual(
                    BAUD_VAL_FROM_CODE[baud_code],
                    baud_rate,
                )

    def test_parity_mappings_are_reversible(self) -> None:
        """Числовые значения чётности должны иметь обратное соответствие."""
        for parity_value, parity_name in PARITY_VAL_TO_STR.items():
            with self.subTest(parity_value=parity_value):
                self.assertEqual(
                    PARITY_STR_TO_VAL[parity_name],
                    parity_value,
                )

    def test_minimalmodbus_parity_codes_are_supported(self) -> None:
        """Каждый вариант чётности должен иметь однобуквенный код."""
        self.assertEqual(
            PARITY_MAP,
            {
                "Even": "E",
                "Odd": "O",
                "None": "N",
            },
        )


class DecimalPlacesValidationTests(unittest.TestCase):
    """Проверяет допустимые значения точности отображения энергии."""

    def test_unsupported_decimal_places_are_rejected(self) -> None:
        """Значения 1 и 4 не должны отправляться в прибор."""
        for value in (1, 4):
            with self.subTest(value=value):
                success, message = write_decimal_places(
                    "unused-port",
                    1,
                    9600,
                    "Even",
                    value,
                )

                self.assertFalse(success)
                self.assertIn("Supported values: 2 or 3", message)


class PortCleanupTests(unittest.TestCase):
    """Проверяет освобождение COM-порта после ошибки записи."""

    def test_write_functions_close_port_after_error(self) -> None:
        """Каждая функция записи должна закрывать порт при ошибке связи."""

        class FakeSerial:
            """Минимальная имитация последовательного порта."""

            def __init__(self):
                self.closed = False

            def close(self):
                self.closed = True

        class FailingInstrument:
            """Имитация прибора, который не отвечает на команду."""

            def __init__(self):
                self.serial = FakeSerial()

            def write_register(self, *args, **kwargs):
                raise RuntimeError("Communication error")

            def write_registers(self, *args, **kwargs):
                raise RuntimeError("Communication error")

        test_cases = [
            (
                write_max_current,
                ("unused-port", 1, 9600, "Even", "a", 100.0),
            ),
            (
                write_sensitivity_voltage,
                ("unused-port", 1, 9600, "Even", 10.0),
            ),
            (
                write_sensitivity_current,
                ("unused-port", 1, 9600, "Even", 2.0),
            ),
            (
                write_decimal_places,
                ("unused-port", 1, 9600, "Even", 2),
            ),
            (
                write_tariff_periods,
                ("unused-port", 1, 9600, "Even", 14),
            ),
        ]

        for function, arguments in test_cases:
            with self.subTest(function=function.__name__):
                instrument = FailingInstrument()

                with patch(
                    "device.make_instrument",
                    return_value=instrument,
                ):
                    success, _ = function(*arguments)

                self.assertFalse(success)
                self.assertTrue(instrument.serial.closed)


if __name__ == "__main__":
    unittest.main()