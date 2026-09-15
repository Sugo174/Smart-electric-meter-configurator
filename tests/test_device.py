"""Тесты вспомогательной логики взаимодействия со счётчиком."""

import unittest

from constants import (
    BAUD_CODE_FROM_VAL,
    BAUD_VAL_FROM_CODE,
    BAUD_VALUES,
    PARITY_MAP,
    PARITY_STR_TO_VAL,
    PARITY_VAL_TO_STR,
)
from device import bcd_to_int, int_to_bcd


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


if __name__ == "__main__":
    unittest.main()