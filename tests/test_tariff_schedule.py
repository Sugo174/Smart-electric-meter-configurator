"""Тесты формирования Modbus-регистров тарифного расписания."""

import unittest

from device import (
    build_tariff_schedule_registers,
    parse_tariff_schedule_registers,
)


class TariffScheduleTests(unittest.TestCase):
    """Проверяет преобразование периодов в регистры счётчика."""

    def test_builds_developer_example(self):
        """Создаёт 14 записей по примеру разработчика."""
        registers = build_tariff_schedule_registers([
            (0, 0, 1),
            (8, 0, 2),
            (20, 0, 1),
        ])

        expected = [
            0x0000, 1,
            0x0800, 2,
            *([0x2000, 1] * 12),
        ]

        self.assertEqual(registers, expected)

    def test_parses_schedule_without_padding(self):
        """Не возвращает повторяющиеся технические записи."""
        registers = build_tariff_schedule_registers([
            (0, 0, 1),
            (8, 0, 2),
            (20, 0, 1),
        ])

        periods = parse_tariff_schedule_registers(registers)

        self.assertEqual(
            periods,
            [
                (0, 0, 1),
                (8, 0, 2),
                (20, 0, 1),
            ],
        )


    def test_requires_first_period_at_midnight(self):
        """Не принимает расписание без начального периода в 00:00."""
        with self.assertRaises(ValueError):
            build_tariff_schedule_registers([
                (1, 0, 1),
            ])

    def test_requires_periods_in_time_order(self):
        """Не принимает периоды с неупорядоченным временем начала."""
        with self.assertRaises(ValueError):
            build_tariff_schedule_registers([
                (0, 0, 1),
                (20, 0, 2),
                (8, 0, 1),
            ])


if __name__ == "__main__":
    unittest.main()