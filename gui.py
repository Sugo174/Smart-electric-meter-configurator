"""
Конфигуратор счётчика постоянной энергии СКВТ ЭМИС-ЭЛЕКТРА 977

Назначение: Контроль и настройка параметров счётчика постоянной энергии
СКВТ ЭМИС-ЭЛЕКТРА 977 по протоколу ModBus RTU через COM-порт.
Автор: Boris Svistunov

Примечание: Все операции с COM-портом выполняются в фоновом потоке,
чтобы не блокировать GUI.
"""

# =============================================================================
# 1. Импорты
# =============================================================================

import tkinter as tk
from tkinter import ttk, messagebox
import re
import time
import datetime
import queue
import threading
import serial
import sys
import json
import os
import webbrowser

# Сторонние библиотеки
import sv_ttk  # Современная тема для tkinter
from tkcalendar import Calendar

# Локальные модули
from constants import (
    APP_VERSION,
    BAUD_VALUES,
    PARITY_LIST,
    PULSE_CONSTANT_VALUES,
    DEVICE_INFO_REGISTER_COUNT,
    ENERGY_DECIMAL_PLACES,
)

from update_checker import (
    get_latest_release,
    is_version_newer,
)

from device import (
    list_com_ports,
    scan_device,
    detect_device_type,
    write_device_settings,
    read_device_time,
    write_device_time,
    sync_device_with_pc_time,
    read_device_parameters,
    read_device_parameters_dual,
    clear_device_energy,
    read_device_settings_params,
    write_max_current,
    write_pulse_constant,
    write_sensitivity_voltage,
    write_sensitivity_current,
    write_decimal_places,
    read_tariff_schedule,
    write_tariff_schedule,
    read_device_info,
    write_device_info_field,
    validate_meter_serial_number,
    validate_scanned_serial_number,
    autofill_device_info,
    decode_meter_serial_number,
    get_tariff_at_time,
)

from measurement_stats import MeasurementRun
from power_supply import (
    read_power_supply,
    set_power_supply_output,
    set_power_supply_voltage,
    voltage_to_register,
)

# Словарь для хранения ссылок на иконки (чтобы не удалялись сборщиком мусора)
ICONS = {}


# =============================================================================
# 2. Система локализации
# =============================================================================

# Текущий язык
current_language = "ru"

# Словарь переводов
TRANSLATIONS = {
    "ru": {
        # Меню
        "app_name": "ЭМИС-Интегратор MODBUS",
        "invalid_modbus_address": "Введите адрес Modbus от 1 до 254.",
        "menu_settings": "☰ Настройки программы",
        "menu_help": "Справка",
        "menu_power_supply": "Источник питания",
        "power_supply_read": "Прочитать",
        "power_supply_reading": "Обмен с источником…",
        "power_supply_refresh": "Обновить порты",
        "power_supply_setpoint": "U, В",
        "power_supply_apply": "Задать",
        "power_supply_enable": "Включить выход",
        "power_supply_disable": "Выключить выход",
        "power_supply_on": "Включён",
        "power_supply_off": "Выключен",
        "power_supply_status": "Напряжение: {voltage:.1f} В · Выход: {output}",
        "power_supply_read_first": "Выберите COM-порт источника.",
        "power_supply_invalid_voltage": "Введите напряжение от 0 до 999,9 В с шагом 0,1 В.",
        "power_supply_confirm_enable": "Включить выход источника на порту {port}?",
        "power_supply_busy": "Порт {port} занят другой операцией.",
        "menu_exit": "Выход",
        "menu_language": "Язык",
        "lang_ru": "Русский",
        "lang_en": "English",
        "lang_zh": "简体中文",

        # Вкладки
        "tab_connection": "Соединение",
        "tab_info": "Инфо о приборе",
        "tab_datetime": "Дата и время",
        "tab_params": "Текущие значения",
        "tab_settings": "Настройки прибора",
        "tab_tariff": "Тарифное расписание",
        "tab_archives": "Архивы",
        "lbl_current_tariff": "Текущий тариф",

        # Вкладка "Соединение"
        "lbl_com_port": "COM-порт:",
        "lbl_status": "Статус соединения:",
        "btn_refresh": "Обновить",
        "btn_connect": "Подключиться",
        "btn_disconnect": "Отключиться",
        "lbl_modbus_params": "Параметры ModBus соединения:",
        "lbl_address": "Адрес:",
        "lbl_baud": "Скорость:",
        "lbl_parity": "Чётность:",
        "btn_write": "Записать",
        "lbl_device_type": "Тип подключаемого счётчика:",
        "dlg_detect_type_error": "Не удалось определить исполнение счётчика.",
        "btn_change_type": "Изменить тип счётчика",
        "device_name": "СКВТ ЭМИС-ЭЛЕКТРА 977",
        "device_single": "(одноканальный)",
        "device_dual": "(двухканальный)",
        "dlg_port_not_initialized": "Порт не инициализирован. Переподключите устройство.",
        "dlg_available_ports": "Доступные COM-порты",
        "dlg_ports_found": "Найдены порты:\n\n{}",
        "dlg_yes": "Да",
        "dlg_no": "Нет",
        "dlg_poll_stop_pending": "Опрос ещё завершается. Подождите немного и повторите отключение.",
        "btn_writing": "Применение...",

        # Вкладка "Дата и время"
        "lbl_current_time": "Время и дата счётчика:",
        "lbl_meter_time_unavailable": "—",
        "btn_time_settings": "Настроить вручную",
        "btn_sync_pc": "Синхронизировать с ПК",
        "dlg_time_writing": "Идет запись времени...\nПожалуйста, подождите.",

        # Вкладка "Текущие значения" - одноканальный
        "lbl_energy": "Электроэнергия:",
        "lbl_energy_abs": "Абсолютная активная:",
        "lbl_energy_pos": "Суммарная прямая:",
        "lbl_energy_neg": "Суммарная обратная:",
        "lbl_current_params": "Текущие параметры:",
        "lbl_voltage": "Напряжение:",
        "lbl_current": "Ток:",
        "lbl_power": "Мощность:",
        "lbl_nominal": "Номинальные параметры:",
        "lbl_nom_voltage": "Номинальное напряжение:",
        "lbl_nom_current": "Номинальный ток:",
        "measurement_label": "Измерение текущих параметров:",
        "measurement_start": "Измерить",
        "measurement_stop": "Остановить",
        "measurement_protocol": "Заполнить протокол",
        "measurement_progress": "Подготовка к усреднению · {count} из {minimum} замеров",
        "measurement_running": "Усреднение идёт · замеров: {count}",


        # Вкладка "Текущие значения" - двухканальный
        "lbl_channel_a": "Канал A",
        "lbl_channel_b": "Канал B",
        "lbl_abs": "Абсолютная:",
        "lbl_abs_hint": "(|прямая| + |обратная|)",
        "lbl_pos": "Прямая:",
        "lbl_neg": "Обратная:",
        "lbl_nom_v": "Номинальное напр.:",
        "lbl_nom_i": "Номинальный ток:",

        # Вкладка "Настройки прибора"
        "lbl_max_current": "Максимальный ток:",
        "lbl_max_current_a": "Максимальный ток канала A:",
        "lbl_max_current_b": "Максимальный ток канала B:",
        "lbl_sens_voltage": "Порог чувствительности напряжения:",
        "lbl_sens_current": "Порог чувствительности тока:",
        "lbl_pulse_constant_ch1": "Постоянная имп. выхода, канал A:",
        "lbl_pulse_constant_ch2": "Постоянная имп. выхода, канал B:",
        "unit_imp_kwh": "имп/кВт·ч",
        "lbl_decimal": "Десятичных знаков энергии:",
        "lbl_tariff": "Тарифных отрезков:",
        "btn_change": "Изменить",
        "btn_clear_energy": "Очистить значения энергии",

        # Тарифное расписание
        "lbl_active_tariff": "Тариф по расписанию:",
        "lbl_tariff_schedule": "Тарифное расписание:",
        "btn_tariff_schedule": "Настроить расписание",
        "dlg_tariff_schedule": "Настройка тарифного расписания",
        "lbl_tariff_start_time": "Время начала",
        "lbl_tariff_number": "Тариф",
        "btn_add_period": "Добавить период",
        "btn_remove_period": "Удалить",
        "btn_save_schedule": "Записать расписание",
        "dlg_schedule_saved": "Тарифное расписание успешно записано.",
        "err_schedule_time": "Время периода {row} должно иметь формат ЧЧ:ММ.",
        "err_schedule_empty": "Добавьте хотя бы один тарифный период.",
        "err_schedule_limit": "Можно добавить не более 14 тарифных периодов.",
        "lbl_schedule_important": "Важно:",
        "hint_schedule_order": "Начало каждого периода должно быть позже предыдущего.",
        "err_schedule_order": "Период {row}: укажите время позже {previous}.",

        # Вкладка "Информация о приборе"
        "lbl_serial": "Серийный номер:",
        "lbl_manufacturer": "Производитель:",
        "lbl_meter_type": "Тип счетчика:",
        "lbl_sw_version": "Версия метрологического ПО:",
        "lbl_info_heading": "Сведения о приборе",
        "lbl_info_sw_version": "Версия\nметрологического ПО",
        "lbl_info_channels": "Измерительные\nканалы",
        "lbl_status_sw_version": "Версия ПО:",
        "lbl_release_date": "Дата:",
        "info_serial_prompt": "Введите ровно 12 цифр (0–9).",
        "info_ascii_prompt": "Введите от 1 до 16 печатных символов ASCII: латиница, цифры и знаки.",
        "btn_info_autofill": "Автозаполнение",
        "info_autofill_prompt": (
            "Используйте сканер штрихкодов, чтобы считать серийный номер "
            "с заводской наклейки или гравировки прибора."
        ),
        "info_autofill_invalid": (
            "Номер не соответствует формату 977 C P YY MM SSS. "
            "Нужны 12 цифр, серия 977, допустимые коды каналов "
            "и питания, месяц от 01 до 12."
        ),
        "info_autofill_busy": "Заполнение данных прибора…",

        # Расшифровка серийного номера
        "lbl_serial_decoding": "Расшифровка серийного номера:",
        "lbl_meter_series": "Серия:",
        "lbl_channel_configuration": "Измерительные каналы:",
        "lbl_power_supply": "Питание:",
        "lbl_manufacture_date": "Дата выпуска:",
        "lbl_sequence_number": "Номер в серии:",
        "serial_single_channel": "1 канал",
        "serial_dual_channel": "2 канала",
        "serial_power_dc": "DC",
        "serial_power_ac": "AC (85–265 В)",

        # Диалоги
        "dlg_select_type": "Выбор типа счётчика",
        "dlg_select_type_prompt": "Выберите тип подключаемого счётчика:",
        "dlg_single": "Одноканальный",
        "dlg_dual": "Двухканальный",
        "dlg_search": "Поиск устройства",
        "dlg_searching": "Поиск устройства",
        "dlg_connected": "Подключено",
        "dlg_connected_msg": "Подключено: СКВТ ЭЭ-977 {}\nАдрес: {}\nСкорость: {}\nЧётность: {}",
        "dlg_write_params_warning": "Изменение параметров связи приведет к разрыву соединения. Продолжить?",
        "dlg_error": "Ошибка",
        "dlg_no_port": "COM-порт не выбран",
        "dlg_port_unavailable": "Ошибка подключения",
        "dlg_port_unavailable_msg": "Порт {} недоступен.\n\nВозможные причины:\n• Кабель RS485 (A/B) отключён\n• USB-RS485 адаптер не подключён\n• Драйвер адаптера не отвечает\n\nРекомендуется:\n1. Проверить физическое подключение кабелей\n2. Переподключить USB-адаптер\n3. Нажать кнопку «Обновить»",
        "dlg_warning": "Внимание",
        "dlg_connect_first": "Сначала подключитесь к прибору.",
        "dlg_write_success": "Готово",
        "dlg_write_success_msg": "Параметры записаны:\nАдрес: {}\nСкорость: {}\nЧётность: {}",
        "dlg_write_error": "Ошибка записи",
        "dlg_no_connection": "Нет подключения",
        "dlg_time_settings": "Настройка даты и времени",
        "dlg_select_date": "Выберите дату:",
        "dlg_optional_time": "Опционально, введите часы и/или минуты:",
        "dlg_hours": "ЧЧ",
        "dlg_minutes": "ММ",
        "dlg_apply": "Применить",
        "dlg_cancel": "Отмена",
        "dlg_time_written": "Дата и время записаны.",
        "dlg_time_write_error": "Ошибка записи времени",
        "dlg_sync_success": "Время синхронизировано с ПК:\n{}",
        "dlg_sync_error": "Ошибка синхронизации",
        "dlg_clear_confirm": "Подтверждение",
        "dlg_clear_confirm_msg": "Вы уверены, что хотите сбросить все накопленные значения электроэнергии?\nЭто действие нельзя отменить.",
        "dlg_clear_success": "Значения электроэнергии успешно сброшены.",
        "dlg_clear_error": "Ошибка сброса",
        "dlg_password": "Требуется пароль",
        "dlg_password_prompt": "Введите пароль для сброса энергии:",
        "dlg_wrong_password": "Неверный пароль.",
        "dlg_help": "Справка о программе",
        "dlg_change_type_warning": "Изменение типа счётчика требует переподключения.\nСейчас будет выполнено отключение.",
        "dlg_disconnected": "Устройство отключено. Проверьте питание и подключение.",

        # Диалоги изменения настроек
        "dlg_max_current_a": "Максимальный ток канала А",
        "dlg_max_current_a_prompt": "Введите максимальный ток канала А (А):",
        "dlg_max_current_b": "Максимальный ток канала B",
        "dlg_max_current_b_prompt": "Введите максимальный ток канала B (А):",
        "dlg_sens_voltage": "Порог чувствительности напряжения",
        "dlg_sens_voltage_prompt": "Введите порог чувствительности напряжения (%):",
        "dlg_sens_current": "Порог чувствительности тока",
        "dlg_sens_current_prompt": "Введите порог чувствительности тока (%):",
        "dlg_value_written": "Значение записано",
        "dlg_write_failed": "Ошибка записи",
        "dlg_input_error": "Ошибка",
        "dlg_invalid_number": "Введите корректное число",

        # Единицы измерения
        "unit_v": "В",
        "unit_a": "А",
        "unit_kw": "кВт",
        "unit_kwh": "кВт·ч",
        "unit_percent": "%",

        # Статусы
        "status_disconnected": "—",
        "status_no_ports": "(нет портов)",

        # Обновление
        "menu_check_updates": "Проверить обновления",
        "dlg_update_check": "Проверка обновлений",
        "msg_update_current": "Установлена актуальная версия {current_version}.",
        "msg_update_available": (
            "Доступна новая версия {latest_version}.\n"
            "Установлена версия: {current_version}.\n\n"
        ),
        "msg_update_network_error": (
            "Не удалось проверить обновления. Проверьте подключение "
            "к интернету и повторите попытку."
        ),
        "msg_update_invalid_data": (
        "GitHub вернул некорректные данные о последнем релизе."
        ),
        "btn_download_update": "Скачать",
        "btn_close": "Закрыть",
    },

    "en": {
        # Menu
        "app_name": "EMIS-Integrator MODBUS",
        "invalid_modbus_address": "Enter a Modbus address from 1 to 254.",
        "menu_settings": "☰ Program Settings",
        "menu_help": "Help",
        "menu_power_supply": "Power Supply",
        "power_supply_read": "Read",
        "power_supply_reading": "Communicating with power supply…",
        "power_supply_refresh": "Refresh ports",
        "power_supply_setpoint": "U, V",
        "power_supply_apply": "Apply",
        "power_supply_enable": "Enable output",
        "power_supply_disable": "Disable output",
        "power_supply_on": "On",
        "power_supply_off": "Off",
        "power_supply_status": "Voltage: {voltage:.1f} V · Output: {output}",
        "power_supply_read_first": "Select the power supply COM port.",
        "power_supply_invalid_voltage": "Enter a voltage from 0 to 999.9 V in 0.1 V increments.",
        "power_supply_confirm_enable": "Enable power supply output on {port}?",
        "power_supply_busy": "Port {port} is busy with another operation.",
        "menu_exit": "Exit",
        "menu_language": "Language",
        "lang_ru": "Русский",
        "lang_en": "English",
        "lang_zh": "简体中文",

        # Tabs
        "tab_connection": "Connection",
        "tab_info": "Device Info",
        "tab_datetime": "Date & Time",
        "tab_params": "Current Values",
        "tab_settings": "Device Settings",
        "tab_tariff": "Tariff Schedule",
        "tab_archives": "Archives",
        "lbl_current_tariff": "Current tariff",

        # Connection tab
        "lbl_com_port": "COM Port",
        "lbl_status": "Connection Status:",
        "btn_refresh": "Refresh",
        "btn_connect": "Connect",
        "btn_disconnect": "Disconnect",
        "lbl_modbus_params": "ModBus Connection Parameters:",
        "lbl_address": "Address:",
        "lbl_baud": "Baud Rate:",
        "lbl_parity": "Parity:",
        "btn_write": "Write",
        "lbl_device_type": "Meter Type:",
        "dlg_detect_type_error": "Could not determine the meter type.",
        "btn_change_type": "Change Meter Type",
        "device_name": "SKVT EMIS-ELECTRA 977",
        "device_single": "(single-channel)",
        "device_dual": "(dual-channel)",
        "dlg_port_not_initialized": "Port not initialized. Reconnect the device.",
        "dlg_available_ports": "Available COM Ports",
        "dlg_ports_found": "Ports found:\n\n{}",
        "dlg_yes": "Yes",
        "dlg_no": "No",
        "btn_writing": "Applying...",
        "dlg_poll_stop_pending": "Polling is still stopping. Please wait a moment and disconnect again.",

        # Date & Time tab
        "lbl_current_time": "Meter time and date:",
        "lbl_meter_time_unavailable": "—",
        "btn_time_settings": "Set manually",
        "btn_sync_pc": "Sync with PC",
        "dlg_time_writing": "Writing time...\nPlease wait.",

        # Current Values - single channel
        "lbl_energy": "Energy:",
        "lbl_energy_abs": "Absolute Active:",
        "lbl_energy_pos": "Total Forward:",
        "lbl_energy_neg": "Total Negative:",
        "lbl_current_params": "Current Parameters:",
        "lbl_voltage": "Voltage:",
        "lbl_current": "Current:",
        "lbl_power": "Power:",
        "lbl_nominal": "Nominal Parameters:",
        "lbl_nom_voltage": "Nominal Voltage:",
        "lbl_nom_current": "Nominal Current:",
        "measurement_label": "Measure live readings:",
        "measurement_start": "Measure",
        "measurement_stop": "Stop",
        "measurement_protocol": "Fill in protocol",
        "measurement_progress": "Preparing to average · {count} of {minimum} readings",
        "measurement_running": "Averaging · readings: {count}",

        # Current Values - dual channel
        "lbl_channel_a": "Channel A",
        "lbl_channel_b": "Channel B",
        "lbl_abs": "Absolute:",
        "lbl_abs_hint": "(|forward| + |reverse|)",
        "lbl_pos": "Forward:",
        "lbl_neg": "Negative:",
        "lbl_nom_v": "Nom. Voltage:",
        "lbl_nom_i": "Nom. Current:",

        # Device Settings tab
        "lbl_max_current": "Max Current:",
        "lbl_max_current_a": "Max Current Channel A:",
        "lbl_max_current_b": "Max Current Channel B:",
        "lbl_sens_voltage": "Voltage Sensitivity Threshold:",
        "lbl_sens_current": "Current Sensitivity Threshold:",
        "lbl_pulse_constant_ch1": "Pulse constant, channel A:",
        "lbl_pulse_constant_ch2": "Pulse constant, channel B:",
        "unit_imp_kwh": "imp/kWh",
        "lbl_decimal": "Energy Decimal Places:",
        "lbl_tariff": "Tariff Periods:",
        "btn_change": "Change",
        "btn_clear_energy": "Clear Energy Values",

        # Tariff schedule
        "lbl_active_tariff": "Tariff by schedule:",
        "lbl_tariff_schedule": "Tariff schedule:",
        "btn_tariff_schedule": "Configure schedule",
        "dlg_tariff_schedule": "Tariff Schedule",
        "lbl_tariff_start_time": "Start time",
        "lbl_tariff_number": "Tariff",
        "btn_add_period": "Add period",
        "btn_remove_period": "Remove",
        "btn_save_schedule": "Write schedule",
        "dlg_schedule_saved": "Tariff schedule was written successfully.",
        "err_schedule_time": "Period {row} time must use the HH:MM format.",
        "err_schedule_empty": "Add at least one tariff period.",
        "err_schedule_limit": "A maximum of 14 tariff periods is allowed.",
        "lbl_schedule_important": "Important:",
        "hint_schedule_order": "Each period must start after the previous one.",
        "err_schedule_order": "Period {row}: enter a time later than {previous}.",

        # Device Info tab
        "lbl_serial": "Serial Number:",
        "lbl_manufacturer": "Manufacturer:",
        "lbl_meter_type": "Meter Type:",
        "lbl_sw_version": "Metrological SW Version:",
        "lbl_info_heading": "Device information",
        "lbl_info_sw_version": "Metrological\nsoftware version",
        "lbl_info_channels": "Measurement\nchannels",
        "lbl_status_sw_version": "SW Version:",
        "lbl_release_date": "Date:",
        "info_serial_prompt": "Enter exactly 12 digits (0–9).",
        "info_ascii_prompt": "Enter 1–16 printable ASCII characters: Latin letters, digits and symbols.",
        "btn_info_autofill": "Auto-fill",
        "info_autofill_prompt": (
            "Use a barcode scanner to read the serial number "
            "from the meter's factory label or engraving."
        ),
        "info_autofill_invalid": (
            "The number must match 977 C P YY MM SSS: "
            "12 digits, series 977, valid channel and power codes, "
            "and a month from 01 to 12."
        ),
        "info_autofill_busy": "Filling in meter information…",

        # Serial number decoding
        "lbl_serial_decoding": "Serial Number Decoding:",
        "lbl_meter_series": "Series:",
        "lbl_channel_configuration": "Measurement Channels:",
        "lbl_power_supply": "Power Supply:",
        "lbl_manufacture_date": "Manufacturing Date:",
        "lbl_sequence_number": "Number in Series:",
        "serial_single_channel": "1 channel",
        "serial_dual_channel": "2 channels",
        "serial_power_dc": "DC",
        "serial_power_ac": "AC (85–265 V)",
        
        # Dialogs
        "dlg_select_type": "Select Meter Type",
        "dlg_select_type_prompt": "Select meter type to connect:",
        "dlg_single": "Single-Channel",
        "dlg_dual": "Dual-Channel",
        "dlg_search": "Searching Device",
        "dlg_searching": "Searching for device",
        "dlg_connected": "Connected",
        "dlg_write_params_warning": "Changing connection parameters will disconnect the device. Continue?",
        "dlg_connected_msg": "Connected: SKVT EE-977 {}\nAddress: {}\nBaud: {}\nParity: {}",
        "dlg_error": "Error",
        "dlg_no_port": "COM port not selected",
        "dlg_port_unavailable": "Connection Error",
        "dlg_port_unavailable_msg": "Port {} unavailable.\n\nPossible causes:\n• RS485 (A/B) cable disconnected\n• USB-RS485 adapter not connected\n• Adapter driver not responding\n\nRecommended:\n1. Check physical cable connections\n2. Reconnect USB adapter\n3. Click 'Refresh'",
        "dlg_change_type_warning": "Changing the meter type requires reconnecting.\nThe meter will now be disconnected.",
        "dlg_warning": "Warning",
        "dlg_connect_first": "Please connect to device first.",
        "dlg_write_success": "Success",
        "dlg_write_success_msg": "Parameters written:\nAddress: {}\nBaud: {}\nParity: {}",
        "dlg_write_error": "Write Error",
        "dlg_no_connection": "No connection",
        "dlg_time_settings": "Date & Time Settings",
        "dlg_select_date": "Select date:",
        "dlg_optional_time": "Optional: enter hours and/or minutes:",
        "dlg_hours": "HH",
        "dlg_minutes": "MM",
        "dlg_apply": "Apply",
        "dlg_cancel": "Cancel",
        "dlg_time_written": "Date and time written.",
        "dlg_time_write_error": "Time Write Error",
        "dlg_sync_success": "Time synced with PC:\n{}",
        "dlg_sync_error": "Sync Error",
        "dlg_clear_confirm": "Confirm",
        "dlg_clear_confirm_msg": "Are you sure you want to clear all accumulated energy values?\nThis action cannot be undone.",
        "dlg_clear_success": "Energy values cleared successfully.",
        "dlg_clear_error": "Clear Error",
        "dlg_password": "Password Required",
        "dlg_password_prompt": "Enter password to clear energy:",
        "dlg_wrong_password": "Wrong password.",
        "dlg_help": "Program Help",
        "dlg_disconnected": "Device disconnected. Check power and connection.",

        # Settings change dialogs
        "dlg_max_current_a": "Max Current Channel A",
        "dlg_max_current_a_prompt": "Enter max current for channel A (A):",
        "dlg_max_current_b": "Max Current Channel B",
        "dlg_max_current_b_prompt": "Enter max current for channel B (A):",
        "dlg_sens_voltage": "Voltage Sensitivity",
        "dlg_sens_voltage_prompt": "Enter voltage sensitivity threshold (%):",
        "dlg_sens_current": "Current Sensitivity",
        "dlg_sens_current_prompt": "Enter current sensitivity threshold (%):",
        "dlg_value_written": "Value written",
        "dlg_write_failed": "Write failed",
        "dlg_input_error": "Error",
        "dlg_invalid_number": "Please enter a valid number",

        # Units
        "unit_v": "V",
        "unit_a": "A",
        "unit_kw": "kW",
        "unit_kwh": "kWh",
        "unit_percent": "%",

        # Status
        "status_disconnected": "—",
        "status_no_ports": "(no ports)",

        # Update
        "menu_check_updates": "Check for Updates",
        "dlg_update_check": "Update Check",
        "msg_update_current": "Version {current_version} is up to date.",
        "msg_update_available": (
            "A new version {latest_version} is available.\n"
            "Installed version: {current_version}.\n\n"
        ),
        "msg_update_network_error": (
            "Could not check for updates. Check your internet connection "
            "and try again."
        ),
        "msg_update_invalid_data": (
            "GitHub returned invalid data for the latest release."
        ),
        "btn_download_update": "Download",
        "btn_close": "Close",
    },

    "zh": {
        # 菜单
        "app_name": "EMIS-Integrator MODBUS",
        "invalid_modbus_address": "请输入 1 至 254 的 Modbus 地址。",
        "menu_settings": "☰ 程序设置",
        "menu_help": "帮助",
        "menu_power_supply": "电源",
        "power_supply_read": "读取",
        "power_supply_reading": "正在与电源通信…",
        "power_supply_refresh": "刷新端口",
        "power_supply_setpoint": "U，V",
        "power_supply_apply": "设置",
        "power_supply_enable": "开启输出",
        "power_supply_disable": "关闭输出",
        "power_supply_on": "开启",
        "power_supply_off": "关闭",
        "power_supply_status": "电压：{voltage:.1f} V · 输出：{output}",
        "power_supply_read_first": "请选择电源的 COM 端口。",
        "power_supply_invalid_voltage": "请输入 0 至 999.9 V 的电压，步进为 0.1 V。",
        "power_supply_confirm_enable": "开启 {port} 上的电源输出？",
        "power_supply_busy": "端口 {port} 正忙。",
        "menu_exit": "退出",
        "menu_language": "语言",
        "lang_ru": "Русский",
        "lang_en": "English",
        "lang_zh": "简体中文",

        # 选项卡
        "tab_connection": "连接",
        "tab_info": "设备信息",
        "tab_datetime": "日期和时间",
        "tab_params": "当前值",
        "tab_settings": "设备设置",
        "tab_tariff": "费率时段表",
        "tab_archives": "档案",
        "lbl_current_tariff": "当前费率",

        # 连接选项卡
        "lbl_com_port": "COM端口",
        "lbl_status": "连接状态:",
        "btn_refresh": "刷新",
        "btn_connect": "连接",
        "btn_disconnect": "断开",
        "lbl_modbus_params": "ModBus连接参数:",
        "lbl_address": "地址:",
        "lbl_baud": "波特率:",
        "lbl_parity": "奇偶校验:",
        "btn_write": "写入",
        "lbl_device_type": "电表类型:",
        "dlg_detect_type_error": "无法识别电表类型。",
        "btn_change_type": "更改电表类型",
        "device_name": "SKVT EMIS-ELECTRA 977",
        "device_single": "(单通道)",
        "device_dual": "(双通道)",
        "dlg_port_not_initialized": "端口未初始化。请重新连接设备。",
        "dlg_available_ports": "可用COM端口",
        "dlg_ports_found": "找到的端口:\n\n{}",
        "dlg_yes": "是",
        "dlg_no": "否",
        "btn_writing": "正在应用...",
        "dlg_poll_stop_pending": "正在停止轮询。请稍候，然后再次断开连接。",

        # 日期时间选项卡
        "lbl_current_time": "电表时间和日期：",
        "lbl_meter_time_unavailable": "—",
        "btn_time_settings": "手动设置",
        "btn_sync_pc": "与电脑同步",
        "dlg_time_writing": "正在写入时间...\n请稍候。",

        # 当前值 - 单通道
        "lbl_energy": "电能:",
        "lbl_energy_abs": "绝对有功:",
        "lbl_energy_pos": "正向累计:",
        "lbl_energy_neg": "反向累计:",
        "lbl_current_params": "当前参数:",
        "lbl_voltage": "电压:",
        "lbl_current": "电流:",
        "lbl_power": "功率:",
        "lbl_nominal": "额定参数:",
        "lbl_nom_voltage": "额定电压:",
        "lbl_nom_current": "额定电流:",
        "measurement_label": "当前参数测量：",
        "measurement_start": "测量",
        "measurement_stop": "停止",
        "measurement_protocol": "填写检定记录",
        "measurement_progress": "准备计算平均值 · 已采集 {count}/{minimum} 个读数",
        "measurement_running": "正在计算平均值 · 读数：{count}",

        # 当前值 - 双通道
        "lbl_channel_a": "通道A",
        "lbl_channel_b": "通道B",
        "lbl_abs": "绝对值:",
        "lbl_abs_hint": "（|正向| + |反向|）",
        "lbl_pos": "正向:",
        "lbl_neg": "反向:",
        "lbl_nom_v": "额定电压:",
        "lbl_nom_i": "额定电流:",

        # 设备设置选项卡
        "lbl_max_current": "最大电流:",
        "lbl_max_current_a": "通道A最大电流:",
        "lbl_max_current_b": "通道B最大电流:",
        "lbl_sens_voltage": "电压灵敏度阈值:",
        "lbl_sens_current": "电流灵敏度阈值:",
        "lbl_pulse_constant_ch1": "通道A脉冲常数:",
        "lbl_pulse_constant_ch2": "通道B脉冲常数:",
        "unit_imp_kwh": "imp/kWh",
        "lbl_decimal": "电能小数位数:",
        "lbl_tariff": "费率时段数:",
        "btn_change": "更改",
        "btn_clear_energy": "清除电能值",

        # 费率时段表
        "lbl_active_tariff": "按时段表计算的费率：",
        "lbl_tariff_schedule": "费率时段表：",
        "btn_tariff_schedule": "设置费率时段",
        "dlg_tariff_schedule": "费率时段设置",
        "lbl_tariff_start_time": "开始时间",
        "lbl_tariff_number": "费率",
        "btn_add_period": "添加时段",
        "btn_remove_period": "删除",
        "btn_save_schedule": "写入时段表",
        "dlg_schedule_saved": "费率时段表已成功写入。",
        "err_schedule_time": "第 {row} 个时段的时间必须使用 HH:MM 格式。",
        "err_schedule_empty": "请至少添加一个费率时段。",
        "err_schedule_limit": "最多允许 14 个费率时段。",
        "lbl_schedule_important": "重要：",
        "hint_schedule_order": "每个时段的开始时间必须晚于上一个时段。",
        "err_schedule_order": "第 {row} 个时段：请输入晚于 {previous} 的时间。",

        # 设备信息选项卡
        "lbl_serial": "序列号:",
        "lbl_manufacturer": "制造商:",
        "lbl_meter_type": "电表类型:",
        "lbl_sw_version": "计量软件版本:",
        "lbl_info_heading": "设备信息",
        "lbl_info_sw_version": "计量软件版本",
        "lbl_info_channels": "测量通道",
        "lbl_status_sw_version": "软件版本:",
        "lbl_release_date": "日期:",
        "info_serial_prompt": "请输入恰好12位数字（0–9）。",
        "info_ascii_prompt": "请输入1至16个可打印ASCII字符：拉丁字母、数字或符号。",
        "btn_info_autofill": "自动填写",
        "info_autofill_prompt": "请使用条码扫描器读取电表出厂标签或刻印上的序列号。",
        "info_autofill_invalid": (
            "序列号须符合977 C P YY MM SSS格式：共12位数字，"
            "系列为977，通道和电源代码有效，月份为01至12。"
        ),
        "info_autofill_busy": "正在填写电表信息…",

        # 序列号解析
        "lbl_serial_decoding": "序列号解析：",
        "lbl_meter_series": "系列：",
        "lbl_channel_configuration": "测量通道：",
        "lbl_power_supply": "供电：",
        "lbl_manufacture_date": "生产日期：",
        "lbl_sequence_number": "系列编号：",
        "serial_single_channel": "1 个通道",
        "serial_dual_channel": "2 个通道",
        "serial_power_dc": "直流电源",
        "serial_power_ac": "交流电源 (85–265 V)",       

        # 对话框
        "dlg_select_type": "选择电表类型",
        "dlg_select_type_prompt": "选择要连接的电表类型:",
        "dlg_single": "单通道",
        "dlg_dual": "双通道",
        "dlg_search": "搜索设备",
        "dlg_searching": "正在搜索设备",
        "dlg_connected": "已连接",
        "dlg_write_params_warning": "更改连接参数将断开设备连接。继续?",
        "dlg_connected_msg": "已连接：SKVT EE-977 {}\n地址: {}\n波特率: {}\n奇偶校验: {}",
        "dlg_error": "错误",
        "dlg_no_port": "未选择COM端口",
        "dlg_port_unavailable": "连接错误",
        "dlg_port_unavailable_msg": "端口 {} 不可用。\n\n可能原因:\n• RS485 (A/B) 电缆未连接\n• USB-RS485 适配器未连接\n• 适配器驱动程序无响应\n\n建议:\n1. 检查电缆物理连接\n2. 重新连接USB适配器\n3. 点击'刷新'",
        "dlg_warning": "警告",
        "dlg_connect_first": "请先连接到设备。",
        "dlg_write_success": "成功",
        "dlg_write_success_msg": "参数已写入:\n地址: {}\n波特率: {}\n奇偶校验: {}",
        "dlg_write_error": "写入错误",
        "dlg_no_connection": "无连接",
        "dlg_time_settings": "日期和时间设置",
        "dlg_select_date": "选择日期:",
        "dlg_optional_time": "可选:输入小时和/或分钟:",
        "dlg_hours": "时",
        "dlg_minutes": "分",
        "dlg_apply": "应用",
        "dlg_cancel": "取消",
        "dlg_time_written": "日期和时间已写入。",
        "dlg_time_write_error": "时间写入错误",
        "dlg_sync_success": "时间已与电脑同步:\n{}",
        "dlg_sync_error": "同步错误",
        "dlg_clear_confirm": "确认",
        "dlg_clear_confirm_msg": "确定要清除所有累计电能值吗?\n此操作无法撤销。",
        "dlg_clear_success": "电能值已成功清除。",
        "dlg_clear_error": "清除错误",
        "dlg_password": "需要密码",
        "dlg_password_prompt": "输入清除电能的密码:",
        "dlg_wrong_password": "密码错误。",
        "dlg_help": "程序帮助",
        "dlg_change_type_warning": "更改电表类型需要重新连接。\n正在断开连接。",
        "dlg_disconnected": "设备已断开。请检查电源和连接。",

        # 设置更改对话框
        "dlg_max_current_a": "通道A最大电流",
        "dlg_max_current_a_prompt": "输入通道A最大电流 (А):",
        "dlg_max_current_b": "通道B最大电流",
        "dlg_max_current_b_prompt": "输入通道B最大电流 (А):",
        "dlg_sens_voltage": "电压灵敏度",
        "dlg_sens_voltage_prompt": "输入电压灵敏度阈值 (%):",
        "dlg_sens_current": "电流灵敏度",
        "dlg_sens_current_prompt": "输入电流灵敏度阈值 (%):",
        "dlg_value_written": "值已写入",
        "dlg_write_failed": "写入失败",
        "dlg_input_error": "错误",
        "dlg_invalid_number": "请输入有效数字",

        # 单位
        "unit_v": "V",
        "unit_a": "A",
        "unit_kw": "kW",
        "unit_kwh": "kWh",
        "unit_percent": "%",

        # 状态
        "status_disconnected": "—",
        "status_no_ports": "(无端口)",

        # 更新
        "menu_check_updates": "检查更新",
        "dlg_update_check": "检查更新",
        "msg_update_current": "当前已安装最新版本 {current_version}。",
        "msg_update_available": (
            "有新版本 {latest_version} 可用。\n"
            "当前安装版本：{current_version}。\n\n"
        ),
        "msg_update_network_error": (
            "无法检查更新。请检查网络连接后重试。"
        ),
        "msg_update_invalid_data": (
            "GitHub 返回了无效的最新发布版本数据。"
        ),
        "btn_download_update": "下载",
        "btn_close": "关闭",
    }
}


# Вспомогательная функция для получения перевода
def tr(key):
    """Возвращает перевод для текущего языка."""
    return TRANSLATIONS.get(current_language, TRANSLATIONS["ru"]).get(key, key)


def toggle_power_supply_panel():
    global power_supply_visible

    power_supply_visible = not power_supply_visible
    create_parameters_tab()
    if power_supply_visible:
        root.update_idletasks()
        height = min(root.winfo_reqheight(), int(root.winfo_screenheight() * 0.9))
        if height > root.winfo_height():
            root.geometry(f"{root.winfo_width()}x{height}")


def _numeric_input(parent, *, integer=False, signed=False):
    pattern = r"[0-9]*" if integer else r"[0-9]*(?:[.,][0-9]*)?"
    if signed:
        pattern = "-?" + pattern
    return {
        "validate": "key",
        "validatecommand": (parent.register(
            lambda value: re.fullmatch(pattern, value) is not None
        ), "%P"),
    }


def _create_power_supply_panel(parent, *, anchor="center"):
    global power_supply_port_var
    if power_supply_port_var is None:
        power_supply_port_var = tk.StringVar(master=root)

    card = ttk.Frame(parent, style="Emis.Card.TFrame", padding=(12, 8))
    card.pack(side="bottom", anchor=anchor, pady=(8, 6))
    ttk.Label(card, text=tr("menu_power_supply"), style="Emis.Heading.TLabel").pack(
        anchor="w", pady=(0, 5)
    )
    frame = ttk.Frame(card)
    frame.pack(fill="x")

    ttk.Label(frame, text="COM").grid(row=0, column=0, padx=(0, 6))
    port_combo = ttk.Combobox(frame, textvariable=power_supply_port_var, state="readonly", width=10)
    port_combo.grid(row=0, column=1, sticky="w")
    ttk.Label(frame, text=tr("power_supply_setpoint")).grid(
        row=1, column=0, sticky="w", pady=(5, 0),
    )
    voltage_entry = ttk.Entry(frame, width=12, **_numeric_input(frame))
    voltage_entry.grid(row=1, column=1, sticky="w", pady=(5, 0))
    status = ttk.Label(frame, wraplength=430)
    status.grid(row=2, column=0, columnspan=4, sticky="w", pady=(5, 0))

    verified_port = None
    output_raw = None
    displayed_voltage = None

    def can_write():
        return verified_port is not None and verified_port == port_combo.get()

    def update_controls():
        write_state = "normal" if can_write() else "disabled"
        port_combo.config(state="readonly")
        refresh_button.config(state="normal")
        voltage_entry.config(state=write_state)
        voltage_button.config(state=write_state)
        output_button.config(
            text=tr("power_supply_disable" if output_raw == 1 else "power_supply_enable"),
            state=write_state if output_raw in (0, 1) else "disabled",
        )

    def reset_selection(event=None):
        nonlocal verified_port, output_raw, displayed_voltage
        verified_port = None
        output_raw = None
        displayed_voltage = None
        status.config(text=tr("power_supply_read_first"))
        update_controls()
        voltage_entry.config(state="normal")
        voltage_entry.delete(0, "end")
        voltage_entry.config(state="disabled")

    def refresh_list():
        meter_port = conn["port"].upper() if conn else None
        ports = [port for port in list_com_ports() if port.upper() != meter_port]
        previous = port_combo.get()
        port_combo.config(values=ports)
        if previous and previous not in ports:
            power_supply_port_var.set("")

    def start_request(operation, *args):
        global power_supply_pending_port
        port = port_combo.get()
        if not port:
            return
        if (
            power_supply_pending_port is not None
            or search_window_ref is not None
            or (conn and port.upper() == conn["port"].upper())
        ):
            status.config(text=tr("power_supply_busy").format(port=port))
            return

        power_supply_pending_port = port
        polling = operation is read_power_supply
        if not polling:
            for control in (port_combo, refresh_button, voltage_entry, voltage_button, output_button):
                control.config(state="disabled")
        if not polling or not can_write():
            status.config(text=tr("power_supply_reading"))
        results = queue.Queue()

        def worker():
            try:
                results.put((operation(port, 1, *args), None))
            except Exception as error:
                results.put((None, str(error)))

        def finish():
            global power_supply_pending_port
            nonlocal verified_port, output_raw, displayed_voltage
            try:
                data, error = results.get_nowait()
            except queue.Empty:
                root.after(100, finish)
                return

            power_supply_pending_port = None
            if not frame.winfo_exists() or port_combo.get() != port or (conn and port.upper() == conn["port"].upper()):
                return
            if error is not None:
                verified_port = None
                output_raw = None
                update_controls()
                status.config(text=f"{tr('dlg_error')}: {error}")
                return

            verified_port = port
            output_raw = data["output_raw"]
            update_controls()
            voltage = f"{data['voltage_v']:.1f}"
            editing_voltage = voltage_entry.focus_get() is voltage_entry
            if operation is set_power_supply_voltage or (
                not editing_voltage
                and voltage_entry.get() in ("", displayed_voltage)
            ):
                voltage_entry.delete(0, "end")
                voltage_entry.insert(0, voltage)
                displayed_voltage = voltage
            output = {
                0: tr("power_supply_off"),
                1: tr("power_supply_on"),
            }.get(output_raw, str(output_raw))
            status.config(text=tr("power_supply_status").format(
                voltage=data["voltage_v"], output=output,
            ))

        threading.Thread(target=worker, daemon=True).start()
        root.after(100, finish)

    def apply_voltage():
        if not can_write():
            return
        from decimal import Decimal, InvalidOperation

        voltage = voltage_entry.get()
        try:
            requested = Decimal(voltage.strip().replace(",", "."))
            if requested.is_finite() and requested >= 1000:
                voltage = "999.9"
            voltage_to_register(voltage)
        except (InvalidOperation, ValueError):
            status.config(text=tr("power_supply_invalid_voltage"))
            return
        start_request(set_power_supply_voltage, voltage)

    def toggle_output():
        if not can_write() or output_raw not in (0, 1):
            return
        enable = output_raw == 0
        if enable and not messagebox.askyesno(
            tr("menu_power_supply"),
            tr("power_supply_confirm_enable").format(port=port_combo.get()),
            parent=root,
        ):
            return
        start_request(set_power_supply_output, enable)

    refresh_button = ttk.Button(
        frame, text=tr("power_supply_refresh"), command=refresh_list,
    )
    refresh_button.grid(row=0, column=3, padx=(6, 0), sticky="ew")
    voltage_button = ttk.Button(
        frame, text=tr("power_supply_apply"), command=apply_voltage,
    )
    voltage_button.grid(row=1, column=2, padx=(6, 0), pady=(5, 0), sticky="ew")
    output_button = ttk.Button(frame, command=toggle_output, style="Emis.Primary.TButton")
    output_button.grid(row=1, column=3, padx=(6, 0), pady=(5, 0), sticky="ew")
    def select_port(_event):
        reset_selection()
        start_request(read_power_supply)

    def poll_source():
        if not frame.winfo_exists():
            return
        port = port_combo.get()
        if port and power_supply_pending_port is None and search_window_ref is None:
            if conn and port.upper() == conn["port"].upper():
                reset_selection()
                status.config(text=tr("power_supply_busy").format(port=port))
            else:
                start_request(read_power_supply)
        frame.after(1000, poll_source)

    selection_trace = power_supply_port_var.trace_add("write", lambda *_args: reset_selection())

    def remove_selection_trace(event):
        if event.widget is frame:
            power_supply_port_var.trace_remove("write", selection_trace)

    frame.bind("<Destroy>", remove_selection_trace)
    port_combo.bind("<<ComboboxSelected>>", select_port)
    refresh_list()
    reset_selection()
    frame.after_idle(poll_source)


def set_language(lang_code):
    global current_language
    if lang_code not in TRANSLATIONS:
        return
    current_language = lang_code

    # Меняем заголовок главного окна
    _set_app_title(latest_verification_info if conn else None)
    app_header_title.configure(text=tr("app_name"))

    # Загружаем иконки если ещё не загружены
    if not ICONS:
        load_icons()

    # 1. Пересоздаём меню с иконками
    menubar = tk.Menu(root)

    # Меню настроек
    settings_m = tk.Menu(menubar, tearoff=0)

    # Подменю языка с флагами
    lang_menu = tk.Menu(settings_m, tearoff=0)
    lang_menu.add_command(
        label=tr("lang_ru"),
        command=lambda: set_language("ru"),
        image=ICONS.get("flag_ru"),
        compound="left"
    )
    lang_menu.add_command(
        label=tr("lang_en"),
        command=lambda: set_language("en"),
        image=ICONS.get("flag_en"),
        compound="left"
    )
    lang_menu.add_command(
        label=tr("lang_zh"),
        command=lambda: set_language("zh"),
        image=ICONS.get("flag_zh"),
        compound="left"
    )

    settings_m.add_cascade(
        label=tr("menu_language"),
        menu=lang_menu,
        image=ICONS.get("language"),
        compound="left"
    )

    settings_m.add_command(
        label=tr("menu_check_updates"),
        command=check_for_updates,
        image=ICONS.get("update"),
        compound="left",
    )

    settings_m.add_separator()

    settings_m.add_command(
        label=tr("menu_power_supply"),
        command=toggle_power_supply_panel,
        image=ICONS.get("power_supply"),
        compound="left",
    )

    settings_m.add_command(
        label=tr("menu_help"),
        command=show_help,
        image=ICONS.get("help"),
        compound="left"
    )
    settings_m.add_command(
        label=tr("menu_exit"),
        command=lambda: on_closing(),
        image=ICONS.get("exit"),
        compound="left"
    )

    menubar.add_cascade(
        label=tr("menu_settings"),
        menu=settings_m
    )

    root.config(menu=menubar)

    # 2. Обновляем названия вкладок
    notebook.tab(tab_conn, text=tr("tab_connection"))
    notebook.tab(tab_info, text=tr("tab_info"))
    notebook.tab(tab_time, text=tr("tab_datetime"))
    notebook.tab(tab_params, text=tr("tab_params"))
    notebook.tab(tab_settings, text=tr("tab_settings"))
    notebook.tab(tab_tariff, text=tr("tab_tariff"))
    notebook.tab(tab_archives, text=tr("tab_archives"))
    tariff_title.configure(text=tr("lbl_current_tariff"))
    tariff_schedule_label.configure(text=tr("lbl_tariff_schedule"))
    tariff_schedule_button.configure(text=tr("btn_tariff_schedule"))

    # 3. Пересоздаём динамические вкладки
    global ui_rebuild_in_progress
    ui_rebuild_in_progress = True  # Приостанавливаем фоновый опрос

    create_parameters_tab()
    create_settings_tab()
    create_info_tab()

    ui_rebuild_in_progress = False  # Разрешаем опрос снова

    # 4. Безопасно обновляем статичные элементы
    try:
        lbl_modbus_title.config(text=tr("lbl_modbus_params"))
        lbl_time_title.config(text=tr("lbl_current_time"))
        if not conn:
            _show_meter_time("")
        lbl_com_port.config(text=tr("lbl_com_port"))
        lbl_status.config(text=tr("lbl_status"))
        for key, label in meter_status_captions.items():
            label.config(text=tr(key))
        lbl_address.config(text=tr("lbl_address"))
        lbl_baud.config(text=tr("lbl_baud"))
        lbl_parity.config(text=tr("lbl_parity"))
        write_btn.config(text=tr("btn_write"))
        refresh_btn.config(text=tr("btn_refresh"))
        connect_btn.config(text=tr("btn_connect"))
        disconnect_btn.config(text=tr("btn_disconnect"))
        type_label_title.config(text=tr("lbl_device_type"))
        settings_btn.config(text=tr("btn_time_settings"))
        sync_pc_btn.config(text=tr("btn_sync_pc"))
        update_device_type_display()
    except Exception:
        pass

    # Автосохранение языка
    save_config()

    # Авто-ресайз окна под новый язык
    resize_window_to_content()


def _update_widget_text(widget):
    """Рекурсивно обновляет текст у поддерживаемых виджетов."""
    # Кнопки
    if isinstance(widget, (ttk.Button, tk.Button)) and widget.cget("text"):
        text = widget.cget("text")
        for key, val in TRANSLATIONS[current_language].items():
            if key.startswith("btn_") and val == text:
                widget.config(text=tr(key))
                break

    # Метки
    elif isinstance(widget, tk.Label) and widget.cget("text"):
        text = widget.cget("text")
        for key, val in TRANSLATIONS[current_language].items():
            if key.startswith("lbl_") and val in text:
                widget.config(text=tr(key))
                break

    # Рекурсивно обрабатываем контейнеры
    elif isinstance(widget, (tk.Frame, ttk.Frame, tk.LabelFrame)):
        for child in widget.winfo_children():
            _update_widget_text(child)


# =============================================================================
# 3. Глобальные переменные состояния
# =============================================================================

# Подключение
conn = None
connect_btn = None
disconnect_btn = None
refresh_btn = None
status_canvas = None
status_indicator = None
is_device_ready = False  # Флаг: данные с прибора загружены и стабильны

# Метки параметров одноканального режима
param_voltage_label = None
param_current_label = None
param_power_label = None
param_energy_abs_label = None
param_energy_pos_label = None
param_energy_neg_label = None
param_nom_voltage_label = None
param_nom_current_label = None

# Метки параметров двухканального режима
param_v1_label = None
param_i1_label = None
param_p1_label = None
param_v2_label = None
param_i2_label = None
param_p2_label = None
param_ch1_energy_abs_label = None
param_ch1_energy_pos_label = None
param_ch1_energy_neg_label = None
param_ch1_nom_v_label = None
param_ch1_nom_i_label = None
param_ch2_energy_abs_label = None
param_ch2_energy_pos_label = None
param_ch2_energy_neg_label = None
param_ch2_nom_v_label = None
param_ch2_nom_i_label = None

# Метки настроек прибора
settings_max_i_a_label = None
settings_max_i_b_label = None
settings_sens_v_label = None
settings_sens_i_label = None
settings_decimal_combo = None
settings_action_buttons = []
info_action_buttons = []
active_tariff_label = None
latest_tariff_periods = None

# Выпадающие списки постоянной импульсного выхода по каналам.
settings_pulse_combos = {}

# Метки информации о приборе
info_serial_label = None
info_manufacturer_label = None
info_meter_type_label = None
info_sw_version_label = None
info_release_date_label = None

# Метки расшифровки серийного номера
info_series_label = None
info_channels_label = None
info_power_supply_label = None
info_manufacture_date_label = None
info_sequence_number_label = None

# Очереди
time_update_queue = queue.Queue()
param_update_queue = queue.Queue()
settings_update_queue = queue.Queue()
info_update_queue = queue.Queue()
power_supply_visible = False
power_supply_port_var = None
power_supply_pending_port = None

measurement_run = None
measurement_started_at = None
latest_parameters = None
measurement_button = None
measurement_protocol_button = None
measurement_status = None


# Флаги фонового потока
time_reader_active = False
time_reader_thread = None
disconnect_flag = False  # Флаг обрыва связи для безопасной передачи в GUI

# Состояние устройства и GUI
device_type = None
was_ever_connected = False
writing_in_progress = False
post_write_cooldown_until = 0
operation_in_progress = False
manual_write_in_progress = False
settings_dialog_open = False

# Глобальные ссылки на модальные окна (для корректного закрытия)
search_window_ref = None
search_check_id = None

# Метка для картинки типа счётчика во вкладке "Соединение"
type_image_label = None

# Флаг: идёт перестройка интерфейса (смена языка/типа)
ui_rebuild_in_progress = False

# Не допускает одновременный запуск нескольких проверок обновлений.
update_check_in_progress = False

# =============================================================================
# 4. Вспомогательные функции
# =============================================================================

# Путь к файлу настроек
CONFIG_FILE = "config.json"
verification_defaults = {}
# Словарь для хранения картинок счётчиков
DEVICE_IMAGES = {}

def resource_path(relative_path):
    """Возвращает абсолютный путь к ресурсу. Работает и в разработке, и в EXE."""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def load_icons():
    icon_files = {
        "language": resource_path("icons/language.png"),
        "update": resource_path("icons/update.png"),
        "help": resource_path("icons/help.png"),
        "power_supply": resource_path("icons/power_supply.png"),
        "exit": resource_path("icons/exit.png"),
        "flag_ru": resource_path("icons/flag_ru.png"),
        "flag_en": resource_path("icons/flag_en.png"),
        "flag_zh": resource_path("icons/flag_zh.png"),
    }
    for name, path in icon_files.items():
        try:
            if os.path.exists(path):
                ICONS[name] = tk.PhotoImage(file=path)
        except Exception:
            pass


def load_device_images():
    paths = {
        "single": resource_path("images/meter_single.png"),
        "dual": resource_path("images/meter_dual.png")
    }
    for key, path in paths.items():
        try:
            if os.path.exists(path):
                DEVICE_IMAGES[key] = tk.PhotoImage(file=path)
        except Exception:
            pass


def load_device_images():
    """Загружает изображения типов счётчиков из папки images/"""
    import os
    base_path = os.path.dirname(os.path.abspath(__file__))

    paths = {
        "single": os.path.join(base_path, "images", "meter_single.png"),
        "dual": os.path.join(base_path, "images", "meter_dual.png")
    }

    for key, path in paths.items():
        try:
            if os.path.exists(path):
                DEVICE_IMAGES[key] = tk.PhotoImage(file=path)
        except Exception:
            pass  # Если картинка не загрузилась — просто не отображаем


def load_config():
    """Загружает настройки из файла config.json"""
    global current_language
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                defaults = config.get("verification_defaults")
                if isinstance(defaults, dict):
                    verification_defaults.update({
                        key: value for key, value in defaults.items() if isinstance(value, str)
                    })
                saved_lang = config.get("language", "ru")
                if saved_lang in TRANSLATIONS:
                    current_language = saved_lang
    except Exception as e:
        print(f"[CONFIG] Ошибка загрузки: {e}")
        current_language = "ru"


def save_config():
    """Сохраняет текущие настройки в файл config.json"""
    try:
        config = {
            "language": current_language,
            "verification_defaults": verification_defaults,
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[CONFIG] Ошибка сохранения: {e}")


def set_buttons_state(state):
    """Включает или отключает кнопки настройки.

    Args:
        state (str): Состояние кнопок ("normal" или "disabled").
    """
    write_btn.config(state=state)
    settings_btn.config(state=state)
    sync_pc_btn.config(state=state)
    tariff_schedule_button.config(state=state)
    for button in (*info_action_buttons, *settings_action_buttons):
        button.config(state=state)
    if settings_decimal_combo is not None:
        settings_decimal_combo.config(state="readonly" if state == "normal" else "disabled")
    if state == "disabled":
        for combo in settings_pulse_combos.values():
            combo.config(state="disabled")


def start_time_reader() -> bool:
    """Запускает опрос только после завершения предыдущего потока."""
    global time_reader_active, time_reader_thread, disconnect_flag

    if not stop_time_reader():
        return False

    if not conn:
        return False

    disconnect_flag = False
    time_reader_active = True
    time_reader_thread = threading.Thread(
        target=_time_reader_worker,
        daemon=True,
    )
    time_reader_thread.start()
    return True


def stop_time_reader() -> bool:
    """Останавливает фоновое чтение перед операцией с COM-портом.

    Функция сначала запрещает потоку начинать новые операции, а затем
    ожидает завершения уже выполняющегося обращения к устройству.

    Returns:
        bool: ``True``, если поток завершился. ``False``, если поток
        не удалось остановить за отведённое время.
    """
    global time_reader_active, time_reader_thread

    time_reader_active = False

    thread = time_reader_thread

    if thread is None:
        return True

    # Поток не может ждать собственного завершения.
    # Сигнал остановки уже установлен, но завершение ещё не подтверждено.
    if thread is threading.current_thread():
        return False

    thread.join(timeout=5.0)

    if thread.is_alive():
        return False

    time_reader_thread = None
    return True


def _time_reader_worker():
    """Фоновый поток: читает время, параметры и настройки с устройства."""
    global time_reader_active, conn, disconnect_flag

    next_time_read = time.time() + 1
    next_param_read = time.time() + 1
    next_settings_read = time.time() + 2
    next_tariff_read = 0
    next_info_read = time.time() + 2
    consecutive_read_errors = 0
    max_consecutive_read_errors = 3

    while time_reader_active:
        if not conn:
            break

        if ui_rebuild_in_progress:
            time.sleep(0.1)
            continue

        # Блокировка: если идет ручная запись - вообще ничего не делаем
        if manual_write_in_progress:
            time.sleep(0.5)
            continue

        now = time.time()

        # Пропускаем чтение, если идёт запись или действует защитный период
        if writing_in_progress or operation_in_progress or now < post_write_cooldown_until:
            time.sleep(0.1)
            continue

        try:
            # 1. Время (каждую секунду)
            if time_reader_active and now >= next_time_read:
                success, result = read_device_time(conn["port"], conn["slave"], conn["baud"], conn["parity"])
                if success:
                    time_update_queue.put(result["formatted"])
                else:
                    raise Exception("Потеряна связь с устройством")
                next_time_read = now + 1

            # 2. Параметры (каждую секунду)
            if time_reader_active and now >= next_param_read:
                reading_started_at = time.monotonic()
                if device_type == "single":
                    success, params = read_device_parameters(conn["port"], conn["slave"], conn["baud"], conn["parity"])
                else:
                    success, params = read_device_parameters_dual(conn["port"], conn["slave"], conn["baud"], conn["parity"])
                if success:
                    param_update_queue.put((reading_started_at, params))
                else:
                    raise Exception("Потеряна связь при чтении параметров")
                next_param_read = now + 1

            # 3. Настройки прибора (каждые 2 секунды)
            if time_reader_active and now >= next_settings_read:
                success, settings = read_device_settings_params(
                    conn["port"], conn["slave"], conn["baud"], conn["parity"], device_type
                )
                if success:
                    if now >= next_tariff_read:
                        tariff_ok, periods = read_tariff_schedule(
                            conn["port"], conn["slave"], conn["baud"], conn["parity"]
                        )
                        settings["tariff_periods"] = periods if tariff_ok else None
                        next_tariff_read = now + 30
                    settings_update_queue.put(settings)
                else:
                    raise Exception("Потеряна связь при чтении настроек")
                next_settings_read = now + 2

            # 4. Инфо о приборе (каждые 2 секунды)
            if time_reader_active and now >= next_info_read:
                success, info = read_device_info(
                    conn["port"], conn["slave"], conn["baud"], conn["parity"]
                )
                if success:
                    info_update_queue.put(info)
                else:
                    raise Exception("Потеряна связь при чтении информации")
                next_info_read = now + 2
                # Полный цикл чтения прошёл успешно.
                consecutive_read_errors = 0

        except Exception:
            consecutive_read_errors += 1

            # Кратковременная помеха на RS-485 не должна сразу
            # превращаться в отключение устройства.
            if consecutive_read_errors < max_consecutive_read_errors:
                time.sleep(0.5)
                continue

            # Несколько последовательных ошибок означают потерю связи.
            time_reader_active = False
            disconnect_flag = True

            try:
                param_update_queue.put(None)
                settings_update_queue.put(None)
                time_update_queue.put(tr("status_disconnected"))
                info_update_queue.put(None)
            except Exception:
                pass

            return

        time.sleep(0.1)


def _clock_date_text(iso_date):
    if current_language == "ru":
        return ".".join(reversed(iso_date.split("-")))
    return iso_date

latest_meter_time_text = None

def _refresh_active_tariff():
    from datetime import datetime

    if not widget_exists(active_tariff_label):
        return
    try:
        meter_time = datetime.strptime(latest_meter_time_text, "%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError):
        meter_time = None
    tariff = get_tariff_at_time(latest_tariff_periods, meter_time) if conn else None
    active_tariff_label.configure(text="—" if tariff is None else str(tariff))


def _show_meter_time(value):
    global latest_meter_time_text
    latest_meter_time_text = value
    _refresh_active_tariff()
    date, _, clock = value.partition(" ")
    text = f"{clock}  {_clock_date_text(date)}" if clock else tr("lbl_meter_time_unavailable")
    current_time_value.config(text=text)


def _check_time_queue():
    """Обрабатывает очередь обновления времени."""
    global disconnect_flag
    if disconnect_flag:
        disconnect_flag = False
        trigger_disconnect()
        return

    try:
        while True:
            time_str = time_update_queue.get_nowait()
            _show_meter_time(time_str)
    except queue.Empty:
        pass
    root.after(100, _check_time_queue)


def _can_start_measurement():
    return bool(
        conn and is_device_ready and time_reader_active
        and device_type in ("single", "dual")
    )


def _start_measurement():
    """Начинает новую серию для всех величин подключённого прибора."""
    global measurement_run, measurement_started_at

    if not _can_start_measurement():
        return

    from collections import deque

    measurement_run = MeasurementRun(device_type)
    measurement_run.verification_samples = {
        key: deque(maxlen=MeasurementRun.MIN_SAMPLES)
        for key in measurement_run.series
    }
    measurement_started_at = time.monotonic()


def _stop_measurement():
    """Завершает серию и возвращает текущие показания."""
    global measurement_run, measurement_started_at

    was_measuring = measurement_run is not None
    measurement_started_at = None
    measurement_run = None

    if was_measuring and conn and latest_parameters is not None:
        _refresh_electrical_values(latest_parameters)


def _toggle_measurement():
    if measurement_started_at is None:
        _start_measurement()
    else:
        _stop_measurement()

    _refresh_measurement_controls()

PROTOCOL_MEASUREMENT_ROWS = {
    "voltage": (
        ("0,05 Uном", 6),
        ("0,25 Uном", 7),
        ("0,5 Uном", 8),
        ("0,75 Uном", 9),
        ("Uном", 10),
    ),
    "current": (
        ("0,1 Iном", 16),
        ("0,3 Iном", 17),
        ("0,5 Iном", 18),
        ("Iном", 19),
    ),
    "power": (
        ("0,1 Iном", 25),
        ("0,3 Iном", 26),
        ("0,5 Iном", 27),
        ("Iном", 28),
    ),
}


VERIFICATION_CHECKS = (
    ("visual_check", "Внешний осмотр"),
    ("functional_check", "Опробование"),
    ("dielectric_check", "Электрическая прочность изоляции"),
    ("insulation_check", "Электрическое сопротивление изоляции"),
)


def _verification_limits(accuracy_class):
    limit = {"0,5": 0.5, "1": 1.0}[accuracy_class]
    return (2 * limit,) * 2 + (limit,) * 15


def _create_verification_workbook(template_path, output_path, header, nominals, pulse_constant):
    from pathlib import Path

    from openpyxl import load_workbook

    template_path = Path(template_path)
    output_path = Path(output_path)
    if output_path.resolve() == template_path.resolve():
        raise ValueError("Выберите другое имя для протокола.")

    workbook = load_workbook(template_path)
    try:
        summary = workbook["Лист1"]
        readings = workbook["Лист2"]

        single = "ch2" not in nominals
        results_row = 29 if single else 28
        header_cells = {
            "F2": header["protocol_number"],
            "M2": header["verification_date"],
            "E6": header["meter_variant"],
            "AA6": header["production_year"],
            "E7": header["accuracy_class"],
            "O7": pulse_constant,
            "O8": nominals["ch1"][1],
            "O9": nominals["ch1"][0],
            "AA11": header["temperature"],
            "AA12": header["humidity"],
            "AA13": header["pressure"],
            f"B{results_row}": header["serial_number"],
            f"G{results_row}": header["firmware_version"],
            ("F40" if single else "F39"): header["verifier"],
        }
        for column, (key, _) in zip("CDEF", VERIFICATION_CHECKS):
            header_cells[f"{column}{results_row}"] = header[key]
        for address, value in header_cells.items():
            summary[address] = value
            if isinstance(value, str):
                summary[address].data_type = "s"

        readings["J2"] = pulse_constant
        for row in (24, 34):
            readings[f"D{row}"] = "Uэт (В)"
            if not single:
                readings[f"H{row}"] = "Uэт (В)"


        for channel, (nominal_voltage, nominal_current) in nominals.items():
            first_column = 9 if channel == "ch1" else 26
            points = [
                f"{nominal_voltage * factor:g} В"
                for factor in (0.05, 0.25, 0.5, 0.75, 1.0)
            ]
            points.extend(
                f"{nominal_current * factor:g} А"
                for _ in range(3)
                for factor in (0.1, 0.3, 0.5, 1.0)
            )

            for offset, (label, limit) in enumerate(
                zip(points, _verification_limits(header["accuracy_class"]))
            ):
                column = first_column + offset
                summary.cell(row=results_row - 4, column=column, value=label)
                cell = summary.cell(row=results_row - 1, column=column, value=limit)
                cell.number_format = '"± "0.0' 

            readings["B19" if channel == "ch1" else "E19"] = nominal_current

        # Excel does not calculate column widths when openpyxl saves a workbook.
        summary.column_dimensions.group("I", "Y", hidden=False)
        summary.column_dimensions["I"].width = 8
        if not single:
            summary.column_dimensions.group("Z", "AP", hidden=False)
            summary.column_dimensions["Z"].width = 8

        for address in ("AA6", "O7", "O8", "O9"):
            summary[address].number_format = "General"

        workbook.save(output_path)
    finally:
        workbook.close()


def _save_verification_step(path, channel, stage, index, reference, readings, confirm, period=None, final_channels=(), reference_voltage=None):
    import os
    from pathlib import Path
    from tempfile import NamedTemporaryFile

    from openpyxl import load_workbook

    reference_col = {"ch1": "B", "ch2": "E"}[channel]
    measured_col = {"ch1": "C", "ch2": "F"}[channel]

    if stage == "voltage":
        label, row = PROTOCOL_MEASUREMENT_ROWS["voltage"][index]
        values = {
            f"{reference_col}{row}": reference,
            f"{measured_col}{row}": readings["voltage"],
        }
        expected_rows = {row: label}
    elif stage == "current":
        label, row = PROTOCOL_MEASUREMENT_ROWS["current"][index]
        _, power_row = PROTOCOL_MEASUREMENT_ROWS["power"][index]
        period_row = 35 + index
        result_col, voltage_col = ("C", "D") if channel == "ch1" else ("G", "H")
        if period is None or period <= 0:
            raise ValueError("Введите положительный период с частотомера.")
        values = {
            f"{reference_col}{row}": reference,
            f"{measured_col}{row}": readings["current"],
            f"{result_col}{power_row}": readings["power"],
            f"{voltage_col}{power_row}": reference_voltage,
            f"{result_col}{period_row}": period,
            f"{voltage_col}{period_row}": reference_voltage,
        }
        expected_rows = {row: label, power_row: label, period_row: label}
    else:
        raise ValueError(f"Неизвестный этап поверки: {stage}")

    path = Path(path)
    workbook = load_workbook(path)
    temporary_path = None

    try:
        if "Лист2" not in workbook.sheetnames:
            raise ValueError("В протоколе отсутствует «Лист2».")

        sheet = workbook["Лист2"]
        for row, label in expected_rows.items():
            if str(sheet[f"A{row}"].value).strip() != label:
                raise ValueError(f"Строка {row} не совпадает с шаблоном протокола.")

        for address in values:
            if sheet[address].data_type == "f":
                raise ValueError(f"В ячейке {address} находится формула.")

        occupied = [address for address, value in values.items()
                    if sheet[address].value is not None and sheet[address].value != value]
        if occupied and not confirm(occupied):
            return False

        for address, value in values.items():
            sheet[address] = value

        if final_channels:
            summary = workbook["Лист1"]
            row = 29 if len(final_channels) == 1 else 28
            last_col = "Y" if len(final_channels) == 1 else "AP"
            errors = f"I{row}:{last_col}{row}"
            limits = f"I{row - 1}:{last_col}{row - 1}"
            summary[f"H{row}"] = (
                f'=IF(IFERROR(AND(COUNTIF(C{row}:F{row},"P")=4,'
                f'COUNT({errors})={17 * len(final_channels)},'
                f'SUMPRODUCT(--(ABS({errors})>{limits}))=0),FALSE),"P","F")'
            )

        with NamedTemporaryFile(
            dir=path.parent, suffix=".xlsx", delete=False
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)

        workbook.save(temporary_path)
        os.replace(temporary_path, path)
        return True
    finally:
        workbook.close()
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()



verification_window = None
latest_verification_settings = None
latest_verification_info = None


def _ask_verification_header(parent, info, nominals):
    import re
    from datetime import date
    from tkinter import messagebox

    result = None
    serial_number = str(info.get("serial_number") or "").strip()
    firmware_version = str(info.get("sw_version") or "").strip()
    release_date = str(info.get("release_date") or "").strip()
    year_match = re.match(r"([0-9]{4})(?![0-9])", release_date)
    serial_details = decode_meter_serial_number(serial_number)
    if serial_details is None or serial_details["channel_code"] != str(len(nominals)):
        messagebox.showerror(
            "Данные протокола",
            "Проверьте серийный номер и выбранное количество каналов.",
            parent=parent,
        )
        return None

    power_supply = "DC" if serial_details["power_code"] == "1" else "AC"
    nominal_current = nominals["ch1"][1]

    def format_variant(accuracy_class):
        return (
            f"СКВТ ЭЭ-977-{accuracy_class}-1.{nominal_current:g}."
            f"{power_supply}.{serial_details['channel_code']}"
        )

    window = tk.Toplevel(parent)
    window.title("Данные протокола")
    window.transient(parent)
    window.resizable(False, False)

    content = ttk.Frame(window, padding=14)
    content.pack()

    for row, (label, value) in enumerate((
        ("Серийный номер", serial_number),
        ("Версия ПО", firmware_version),
    )):
        ttk.Label(content, text=label).grid(row=row, column=0, sticky="w")
        ttk.Label(content, text=value or "—").grid(row=row, column=1, sticky="w")

    fields = (
        ("protocol_number", "Номер протокола", ""),
        ("verification_date", "Дата поверки (ГГГГ-ММ-ДД)", date.today().isoformat()),
        ("production_year", "Год выпуска", year_match.group(1) if year_match else ""),
        ("accuracy_class", "Класс точности", ""),
        ("verifier", "ФИО поверителя", ""),
        ("temperature", "Температура, °C", ""),
        ("humidity", "Влажность, %", ""),
        ("pressure", "Давление, кПа", ""),
    )
    remembered = ("protocol_number", "verifier", "temperature", "humidity", "pressure")
    check_keys = {key for key, _ in VERIFICATION_CHECKS}
    fields += tuple((key, label, "") for key, label in VERIFICATION_CHECKS)
    entries = {}

    for row, (key, label, default) in enumerate(fields, start=2):
        ttk.Label(content, text=label).grid(
            row=row, column=0, sticky="w", padx=(0, 10), pady=3
        )
        if key == "accuracy_class":
            entry = ttk.Combobox(content, values=("0,5", "1"), state="readonly", width=28)
        elif key in check_keys:
            entry = ttk.Combobox(content, values=("P", "F"), state="readonly", width=28)
        else:
            options = {}
            if key in ("temperature", "humidity", "pressure", "production_year"):
                options = _numeric_input(
                    window, integer=key == "production_year", signed=key == "temperature"
                )
            entry = ttk.Entry(content, width=30, **options)
        entry.grid(row=row, column=1, sticky="ew", pady=3)
        if key != "accuracy_class" and key not in check_keys:
            entry.insert(0, verification_defaults.get(key, default) if key in remembered else default)
        entries[key] = entry

    variant_row = len(fields) + 2
    ttk.Label(content, text="Исполнение счётчика").grid(
        row=variant_row, column=0, sticky="w", padx=(0, 10), pady=3
    )
    variant_text = tk.StringVar(master=window, value=format_variant("…"))
    ttk.Label(content, textvariable=variant_text).grid(
        row=variant_row, column=1, sticky="w", pady=3
    )
    accuracy_field = entries["accuracy_class"]

    def update_variant(_event):
        accuracy = accuracy_field.get().strip().replace(".", ",")
        variant_text.set(format_variant(accuracy or "…"))

    accuracy_field.bind("<<ComboboxSelected>>", update_variant)


    def accept():
        nonlocal result

        values = {key: entry.get().strip() for key, entry in entries.items()}
        for key, label, _ in fields:
            if not values[key]:
                messagebox.showerror("Данные протокола", f"Заполните поле «{label}».", parent=window)
                entries[key].focus_set()
                return

        try:
            values["verification_date"] = date.fromisoformat(values["verification_date"])
        except ValueError:
            messagebox.showerror(
                "Данные протокола", "Введите дату в формате ГГГГ-ММ-ДД.", parent=window
            )
            entries["verification_date"].focus_set()
            return

        year = values["production_year"]
        if not re.fullmatch(r"[0-9]{4}", year) or not 1 <= int(year) <= 9999:
            messagebox.showerror(
                "Данные протокола", "Введите год выпуска четырьмя цифрами.", parent=window
            )
            entries["production_year"].focus_set()
            return

        accuracy = values["accuracy_class"].replace(".", ",")
        if accuracy not in ("0,5", "1"):
            messagebox.showerror(
                "Данные протокола", "Введите класс точности, например 0,5.", parent=window
            )
            accuracy_field.focus_set()
            return

        values["accuracy_class"] = accuracy
        values["meter_variant"] = format_variant(accuracy)

        values["production_year"] = int(year)
        values["serial_number"] = serial_number
        values["firmware_version"] = firmware_version
        verification_defaults.update({key: values[key] for key in remembered})
        save_config()
        result = values
        window.destroy()

    buttons = ttk.Frame(content)
    buttons.grid(row=variant_row + 1, column=0, columnspan=2, pady=(10, 0))
    next_button = ttk.Button(
        buttons, text="Далее", command=accept,
        style="Emis.Primary.TButton", state="disabled",
    )
    next_button.pack(side="left", padx=(0, 8))

    def refresh_next_button(*_args):
        complete = all(entry.get().strip() for entry in entries.values())
        next_button.configure(state="normal" if complete else "disabled")

    field_variables = []
    for entry in entries.values():
        variable = tk.StringVar(master=window, value=entry.get())
        entry.configure(textvariable=variable)
        variable.trace_add("write", refresh_next_button)
        field_variables.append(variable)
    refresh_next_button()
    ttk.Button(buttons, text="Отмена", command=window.destroy).pack(side="left")
    window.bind("<Escape>", lambda _event: window.destroy())

    window.update_idletasks()
    x = parent.winfo_rootx() + (parent.winfo_width() - window.winfo_width()) // 2
    y = parent.winfo_rooty() + (parent.winfo_height() - window.winfo_height()) // 2
    window.geometry(f"+{x}+{y}")
    window.grab_set()
    entries["protocol_number"].focus_set()
    parent.wait_window(window)
    return result


def _confirm_protocol_export(
    parent, heading="Сформировать протокол",
    message="Все данные проверены. Сформировать протокол?",
):
    dialog = tk.Toplevel(parent, background=emis_background)
    dialog.withdraw()
    dialog.title("Поверка")
    dialog.transient(parent)
    dialog.resizable(False, False)

    confirmed = False

    def accept():
        nonlocal confirmed
        confirmed = True
        dialog.destroy()

    card = ttk.Frame(dialog, style="Emis.Card.TFrame", padding=(18, 14))
    card.pack(padx=12, pady=12)
    ttk.Label(card, text=heading, style="Emis.Heading.TLabel").pack(anchor="w")
    ttk.Label(card, text=message,
              wraplength=360, justify="left").pack(anchor="w", pady=(8, 12))

    buttons = ttk.Frame(card)
    buttons.pack(anchor="e")
    ttk.Button(buttons, text=tr("dlg_yes"), command=accept,
               style="Emis.Primary.TButton").pack(side="left", padx=(0, 8))
    cancel = ttk.Button(buttons, text=tr("dlg_no"), command=dialog.destroy)
    cancel.pack(side="left")
    dialog.bind("<Escape>", lambda _event: dialog.destroy())
    dialog.bind("<Return>", lambda event: event.widget.invoke()
                if isinstance(event.widget, ttk.Button) else None)

    dialog.update_idletasks()
    x = parent.winfo_rootx() + (parent.winfo_width() - dialog.winfo_reqwidth()) // 2
    y = parent.winfo_rooty() + (parent.winfo_height() - dialog.winfo_reqheight()) // 2
    dialog.geometry(f"{x:+d}{y:+d}")
    dialog.deiconify()
    dialog.wait_visibility()
    dialog.grab_set()
    cancel.focus_set()
    parent.wait_window(dialog)
    return confirmed


def _period_unit(value, expected_seconds):
    """Choose the interpretation closest to the expected period in scale."""
    if value / expected_seconds <= 1000 ** 0.5:
        return "с", value
    return "мс", value / 1000


def _open_verification():
    import math
    from statistics import mean, stdev
    from pathlib import Path
    from tkinter import filedialog, messagebox

    global verification_window

    if verification_window is not None and verification_window.winfo_exists():
        verification_window.lift()
        return

    connection = conn
    if not conn or not is_device_ready:
        return

    channels = ("ch1",) if device_type == "single" else ("ch1", "ch2")
    params = {"ch1": latest_parameters} if device_type == "single" else latest_parameters
    settings = latest_verification_settings
    try:
        nominals = {
            channel: (float(params[channel]["nom_voltage"]), float(params[channel]["nom_current"]))
            for channel in channels
        }
        constants = [
            int(settings[f"pulse_constant_{channel}"]) for channel in channels
        ]
        if any(not math.isfinite(value) or value <= 0 for pair in nominals.values() for value in pair):
            raise ValueError
        if any(value <= 0 for value in constants):
            raise ValueError
    except (KeyError, TypeError, ValueError):
        messagebox.showerror("Поверка", "Дождитесь чтения номиналов и импульсной постоянной.", parent=root)
        return

    if len(set(constants)) != 1:
        messagebox.showerror(
            "Поверка",
            "В шаблоне одна импульсная постоянная для обоих каналов, а у прибора они различаются.",
            parent=root,
        )
        return

    info = latest_verification_info
    if not info or not info.get("serial_number") or not info.get("sw_version"):
        messagebox.showinfo(
            "Поверка",
            "Дождитесь чтения серийного номера и версии ПО счётчика.",
            parent=root,
        )
        return

    template_name = (
        "verification_template_single.xlsx" if len(channels) == 1 else "verification_template.xlsx"
    )
    template_path = Path(__file__).resolve().with_name(template_name)
    if not template_path.is_file():
        messagebox.showerror(
            "Поверка", f"Не найден шаблон {template_name}.", parent=root
        )
        return

    header = _ask_verification_header(root, info, nominals)
    if header is None or conn is not connection:
        return

    serial = header["serial_number"]
    safe_serial = "".join(char for char in serial if char in "0123456789")
    filename = (
        f"Протокол поверки СКВТ {safe_serial}.xlsx"
        if safe_serial else "Протокол поверки СКВТ.xlsx"
    )
    from tempfile import TemporaryDirectory

    window = tk.Toplevel(root)
    verification_window = window
    window.title("Поверка СКВТ ЭЭ-977")
    window.transient(root)
    window.minsize(980, 560)

    accent = "#009975"
    content = ttk.Frame(window, padding=14)
    content.pack(fill="both", expand=True)
    navigation = ttk.Treeview(content, show="tree", selectmode="browse", height=15)
    navigation.column("#0", width=245, stretch=False)
    column_gap = 16
    navigation.pack(side="left", fill="y", padx=(0, column_gap))
    details = ttk.Frame(content)
    details.pack(side="left", fill="y")
    tk.Frame(content, width=1, bg="gray").pack(side="left", fill="y", padx=column_gap)
    results_panel = ttk.Frame(content)
    results_panel.pack(side="left", fill="both", expand=True)
    title = ttk.Label(details, font=("TkDefaultFont", 13, "bold"), foreground="#00664D")
    title.pack(anchor="w")
    instruction = ttk.Label(details, wraplength=320, justify="left")
    instruction.pack(anchor="w", pady=(6, 12))
    controls = ttk.Frame(details)
    controls.pack(anchor="w")
    display = ttk.Frame(controls)
    display.grid(row=0, column=0, sticky="nw", padx=(0, 8))
    reading_labels = []
    for row in range(2):
        label = ttk.Label(display, foreground=accent, font=("TkDefaultFont", 13, "bold"))
        value = ttk.Label(display, foreground=accent, font=("TkDefaultFont", 13, "bold"))
        label.grid(row=row, column=0, sticky="w", padx=(0, 4))
        value.grid(row=row, column=1, sticky="w")
        reading_labels.append((label, value))
    measurement_actions = ttk.Frame(controls)
    measurement_actions.grid(row=0, column=1, sticky="nw")
    count_label = ttk.Label(measurement_actions)
    voltage_text = tk.StringVar(master=window)
    period_text = tk.StringVar(master=window)
    inputs = ttk.Frame(details)
    inputs.pack(anchor="w", pady=12)
    ttk.Label(inputs, text="Uэт, В:", foreground=accent, font=("TkDefaultFont", 13, "bold")).grid(row=0, column=0, sticky="w")
    voltage_field = ttk.Entry(inputs, textvariable=voltage_text, width=16, **_numeric_input(window))
    voltage_field.grid(row=0, column=1, padx=8)
    period_label = ttk.Label(inputs, text="Tизм:", foreground=accent, font=("TkDefaultFont", 13, "bold"))
    period_label.grid(row=1, column=0, sticky="w", pady=6)
    period_field = ttk.Entry(inputs, textvariable=period_text, width=16, **_numeric_input(window))
    period_field.grid(row=1, column=1, padx=8, pady=6)
    period_unit_label = ttk.Label(inputs, width=4)
    period_unit_label.grid(row=1, column=2, sticky="w")


    if window.tk.call("tk", "windowingsystem") == "win32":
        def handle_clipboard_shortcut(event):
            # Windows virtual-key codes stay the same across keyboard layouts.
            action = {0x43: "<<Copy>>", 0x56: "<<Paste>>"}.get(event.keycode)
            if action:
                event.widget.event_generate(action)
                return "break"

        for field in (voltage_field, period_field):
            field.bind("<Control-KeyPress>", handle_clipboard_shortcut)


    steps = {}
    for channel in channels:
        name = tr("lbl_channel_a" if channel == "ch1" else "lbl_channel_b")
        navigation.insert("", "end", iid=channel, text=name, open=channel == channels[0])
        for stage, heading, factors in (
            ("voltage", "Напряжение", (0.05, 0.25, 0.5, 0.75, 1.0)),
            ("current", "Ток, мощность и период", (1.0, 0.5, 0.3, 0.1)),
        ):
            group = f"{channel}-{stage}"
            navigation.insert(channel, "end", iid=group, text=heading, open=True)
            for offset, factor in enumerate(factors):
                index = offset if stage == "voltage" else 3 - offset
                label = (f"{nominals[channel][0] * factor:g} В" if stage == "voltage"
                         else f"{75 * factor:g} мВ".replace(".", ","))
                key = f"{group}-{index}"
                navigation.insert(group, "end", iid=key, text=label)
                steps[key] = channel, stage, index, factor, label

    saved = {}
    saved_inputs = {}
    drafts = {}
    selected = None
    point_run = None
    captured = None
    timer = None
    stable = False
    timed_out = False
    stable_checks = 0
    last_checked = 0
    deadline = 0.0
    window_size = 5
    stability_limit = 0.0005  # Trial threshold: 0.05% of the reading.
    stability_timeout = 45.0

    def number(variable):
        try:
            value = float(variable.get().strip().replace(",", "."))
        except ValueError:
            return None
        return value if math.isfinite(value) and value > 0 else None

    def connected():
        return conn is connection and is_device_ready

    def active():
        return point_run is not None and point_run is measurement_run

    def interpreted_period():
        voltage = number(voltage_text)
        value = number(period_text)
        channel, stage, _, factor, _ = steps[selected]
        if stage != "current" or voltage is None or value is None:
            return "", None
        expected = 3600000 / (constants[0] * voltage * nominals[channel][1] * factor)
        return _period_unit(value, expected)

    def values():
        voltage = number(voltage_text)
        _, period = interpreted_period()
        if captured is None or voltage is None or (steps[selected][1] == "current" and period is None):
            return None
        return voltage, period, captured

    def sample_window(channel, quantity):
        return tuple(point_run.verification_samples[channel, quantity])[-window_size:]

    def evaluate_stability():
        nonlocal stable, timed_out, stable_checks, last_checked
        if not active():
            return
        channel, stage, _, _, _ = steps[selected]
        quantities = ("voltage",) if stage == "voltage" else ("voltage", "current", "power")
        if point_run.count >= window_size and point_run.count != last_checked:
            last_checked = point_run.count

            def steady(quantity):
                samples = sample_window(channel, quantity)
                half = len(samples) // 2
                limit = abs(mean(samples)) * stability_limit
                return max(stdev(samples), abs(mean(samples[:half]) - mean(samples[half:]))) <= limit

            has_voltage = all(value > 0 for value in sample_window(channel, "voltage"))
            stable_checks = stable_checks + 1 if has_voltage and all(steady(q) for q in quantities) else 0
            stable = stable_checks >= 3
        if stable or time.monotonic() >= deadline:
            timed_out = not stable
            _stop_measurement()

    def refresh():
        if selected is None:
            return
        unit, _ = interpreted_period()
        period_unit_label.configure(text=unit)
        channel, stage, _, _, _ = steps[selected]
        live = latest_parameters or {}
        readings = live if len(channels) == 1 else live.get(channel, {})
        if not connected():
            readings = {}
        if captured is not None:
            readings = captured
        elif point_run is not None and point_run.count:
            readings = {q: mean(sample_window(channel, q)) for q in MeasurementRun.QUANTITIES}
        quantities = (("voltage", "В"),) if stage == "voltage" else (("current", "А"), ("power", "кВт"))
        symbols = {"voltage": "Uсквт", "current": "Iсквт", "power": "Pсквт"}
        for row, (label_widget, value_widget) in enumerate(reading_labels):
            if row >= len(quantities):
                label_widget.grid_remove()
                value_widget.grid_remove()
                continue
            quantity, unit = quantities[row]
            label_widget.configure(text=f"{symbols[quantity]}:")
            value_widget.configure(
                text=f"{readings[quantity]:.4f} {unit}" if quantity in readings else "—"
            )
            label_widget.grid()
            value_widget.grid()
        count_label.configure(text=f"Отсчётов: {point_run.count if point_run else 0}")
        stability_status.configure(text=(
            "Показания стабильны" if stable else
            "Нет напряжения на канале" if point_run and point_run.count
            and sample_window(channel, "voltage")[-1] <= 0 else
            "Показания нестабильны" if timed_out else ""
        ))
        measure.configure(text="Остановить" if active() else (
                              "Повторить измерение" if timed_out else "Измерить"),

                          state="normal" if connected() else "disabled",
                          style="TButton" if active() else "Emis.Primary.TButton")
        capture.configure(state="normal" if connected() and captured is None and stable else "disabled")
        save_button.configure(state="normal" if not active() and values() is not None else "disabled")
        finish.configure(text=f"Сформировать протокол ({len(saved)}/{len(steps)})")
        current_inputs = voltage_text.get(), period_text.get(), captured
        ready = len(saved) == len(steps) and not active() and all(
            (current_inputs if key == selected else drafts.get(key)) == saved_inputs[key]
            for key in steps
        )
        finish.configure(state="normal" if ready else "disabled")

    def tick():
        nonlocal timer
        evaluate_stability()
        refresh()
        timer = window.after(150, tick)

    def toggle():
        nonlocal point_run, captured, stable, timed_out, stable_checks, last_checked, deadline
        if active():
            _stop_measurement()
        elif connected():
            _start_measurement()
            point_run = measurement_run
            if point_run is not None:
                captured = None
                stable = timed_out = False
                stable_checks = last_checked = 0
                deadline = time.monotonic() + stability_timeout
        refresh()

    def freeze():
        nonlocal captured
        if not connected() or captured is not None or not stable or point_run is None:
            return
        channel = steps[selected][0]
        captured = {q: mean(sample_window(channel, q)) for q in MeasurementRun.QUANTITIES}
        if active():
            _stop_measurement()
        refresh()

    def select_point(_event=None):
        nonlocal selected, point_run, captured, stable, timed_out
        selection = navigation.selection()
        if not selection or selection[0] not in steps or selection[0] == selected:
            return
        if selected is not None:
            drafts[selected] = voltage_text.get(), period_text.get(), captured
        if active():
            _stop_measurement()
        point_run = None
        stable = timed_out = False
        selected = selection[0]
        channel, stage, _, _, label = steps[selected]
        voltage, period, captured = drafts.get(selected, ("", "", None))
        voltage_text.set(voltage)
        period_text.set(period)
        name = tr("lbl_channel_a" if channel == "ch1" else "lbl_channel_b")
        prefix = f"{name} · " if len(channels) == 2 else ""
        if stage == "voltage":
            title.configure(text=f"{prefix}Напряжение · {label}")
            instruction.configure(text=f"Выставьте {label} на источнике напряжения и введите показание вольтметра в поле Uэт.")
            period_label.grid_remove()
            period_field.grid_remove()
            period_unit_label.grid_remove()
            save_button.grid_configure(row=0)
        else:
            title.configure(text=f"{prefix}Ток, мощность и период · {label}")
            instruction.configure(text=f"Оставьте напряжение на Uном. Выставьте на калибраторе ЭнИ значение напряжения {label}.")
            period_label.grid()
            period_field.grid()
            period_unit_label.grid()
            save_button.grid_configure(row=1)
        update_preview()
        refresh()

    def save_point():
        data = values()
        if data is None or active():
            return
        saved[selected] = data
        saved_inputs[selected] = voltage_text.get(), period_text.get(), captured
        navigation.item(selected, text=f"✓ {steps[selected][-1]}")
        update_preview()
        keys = list(steps)
        following = keys.index(selected) + 1
        if following < len(keys):
            next_key = keys[following]
            navigation.item(steps[next_key][0], open=True)
            navigation.selection_set(next_key)
            navigation.see(next_key)
            select_point()
        refresh()

    def update_preview():
        channel, stage, _, _, _ = steps[selected]
        tables = ("voltage",) if stage == "voltage" else ("current", "power", "period")
        for quantity, (panel, _) in previews.items():
            panel.pack_forget()
            if quantity in tables:
                panel.pack(fill="x", pady=(0, 6))

        limits = _verification_limits(header["accuracy_class"])
        offsets = {"voltage": 0, "current": 5, "power": 9, "period": 13}
        row_number = 0
        for key, (point_channel, point_stage, index, factor, label) in steps.items():
            if (point_channel, point_stage) != (channel, stage):
                continue
            row_number += 1
            if key not in saved:
                for quantity in tables:
                    set_preview_row(quantity, row_number, ("", "", ""))
                continue

            voltage, period, readings = saved[key]
            if stage == "voltage":
                measured = readings["voltage"]
                rows = (("voltage", voltage, measured, (measured - voltage) / voltage),)
            else:
                current = nominals[channel][1] * factor
                power = voltage * current / 1000
                expected_period = 3600 / (constants[0] * power)
                rows = (
                    ("current", current, readings["current"], (readings["current"] - current) / current),
                    ("power", power, readings["power"], (readings["power"] - power) / power),
                    ("period", expected_period, period, (expected_period - period) / period),
                )
            for quantity, reference, measured, error in rows:
                percent = error * 100
                limit = limits[offsets[quantity] + index]
                color = "#00664D" if abs(percent) <= limit else "#B42318"
                set_preview_row(
                    quantity, row_number,
                    (f"{reference:.8g}", f"{measured:.8g}", f"{percent:+.4f}"),
                    color,
                )

    def set_preview_row(quantity, row_number, values, color="#24332F"):
        for column, (cell, value) in enumerate(zip(previews[quantity][1][row_number - 1], values)):
            cell.configure(text=value, foreground=color if column == 2 else "#24332F")

    def export():
        missing = next((key for key in steps if key not in saved), None)
        if missing is not None:
            messagebox.showinfo("Поверка", f"Запишите все точки. Готово {len(saved)} из {len(steps)}.", parent=window)
            navigation.selection_set(missing)
            navigation.see(missing)
            select_point()
            return
        drafts[selected] = voltage_text.get(), period_text.get(), captured
        dirty = next((key for key in steps if drafts.get(key) != saved_inputs[key]), None)
        if dirty is not None or active():
            messagebox.showinfo("Поверка", "Запишите изменённые точки перед формированием протокола.", parent=window)
            if dirty is not None and not active():
                navigation.selection_set(dirty)
                navigation.see(dirty)
                select_point()
            return
        if not _confirm_protocol_export(window):
            return
        path = filedialog.asksaveasfilename(
            parent=window,
            title="Сохранить новый протокол",
            initialfile=filename,
            defaultextension=".xlsx",
            filetypes=[("Протокол Excel", "*.xlsx")],
        )
        if not path:
            return
        destination = Path(path)
        try:
            if destination.resolve() == template_path.resolve():
                raise ValueError("Выберите другое имя для протокола.")
            with TemporaryDirectory(dir=destination.parent) as folder:
                draft = Path(folder) / "protocol.xlsx"
                _create_verification_workbook(template_path, draft, header, nominals, constants[0])
                for position, (key, (channel, stage, index, factor, _)) in enumerate(steps.items()):
                    voltage, period, readings = saved[key]
                    reference = voltage if stage == "voltage" else nominals[channel][1] * factor
                    _save_verification_step(
                        draft, channel, stage, index, reference, readings, lambda _: True,
                        period=period,
                        final_channels=channels if position == len(steps) - 1 else (),
                        reference_voltage=voltage,
                    )
                os.replace(draft, destination)
        except PermissionError:
            messagebox.showerror("Поверка", "Закройте протокол в Excel и повторите сохранение.", parent=window)
            return
        except Exception as error:
            messagebox.showerror("Поверка", str(error), parent=window)
            return
        def open_report(dialog):
            try:
                os.startfile(str(destination))
            except OSError as error:
                messagebox.showerror("Поверка", str(error), parent=dialog)
                return
            dialog.destroy()
            dispose_window()

        _show_emis_notice(
            "Поверка", "Протокол сформирован.", parent=window, wait=True,
            action=("Открыть протокол", open_report),
        )

    def close_window():
        if (saved or captured is not None) and not _confirm_protocol_export(
            window, "Закрытие поверки", "Закрыть окно поверки?"
        ):
            return
        dispose_window()

    def dispose_window():
        if active():
            _stop_measurement()
        window.after_cancel(timer)
        window.destroy()

    measure = ttk.Button(measurement_actions, command=toggle)
    measure.grid(row=0, column=0, sticky="ew")
    capture = ttk.Button(measurement_actions, text="Замер", command=freeze, style="Emis.Primary.TButton")
    capture.grid(row=0, column=1, padx=(8, 0), sticky="ew")

    def wrap_instruction(_event=None):
        width = capture.winfo_rootx() + capture.winfo_width() - instruction.winfo_rootx()
        if width > 1 and int(instruction.cget("wraplength")) != width:
            instruction.configure(wraplength=width)

    capture.bind("<Configure>", wrap_instruction, add="+")

    measurement_actions.bind("<Configure>", wrap_instruction, add="+")
    count_label.grid(row=1, column=0, sticky="w", pady=(3, 0))
    stability_status = ttk.Label(details)
    stability_status.pack(anchor="w")
    save_button = ttk.Button(
        inputs, text="Записать точку", command=save_point, style="Emis.Primary.TButton",
    )
    save_button.grid(row=0, column=3, padx=(6, 0))
    finish = ttk.Button(details, command=export, style="Emis.Primary.TButton", state="disabled")
    finish.pack(side="bottom", pady=(8, 0))
    _create_power_supply_panel(details, anchor="w")
    previews = {}
    for quantity, heading, height in (
        ("voltage", "Напряжение, В", 5),
        ("current", "Ток, А", 4),
        ("power", "Мощность, кВт", 4),
        ("period", "Период, с", 4),
    ):
        panel = ttk.Frame(results_panel)
        ttk.Label(panel, text=heading, style="Emis.Heading.TLabel").grid(row=0, column=0, columnspan=3, sticky="w")
        columns = (("Эталон", 10), ("Измерено", 11), ("Погрешность, %", 16))
        grid = tk.Frame(panel, background="#D4DEDE", padx=1, pady=1)
        grid.grid(row=1, column=0, sticky="ew", pady=(3, 0))
        panel.columnconfigure(0, weight=1)
        for column, (label, width) in enumerate(columns):
            grid.columnconfigure(column, weight=1)
            ttk.Label(grid, text=label, width=width, anchor="center", padding=(0, 2)).grid(
                row=0, column=column, sticky="ew", padx=(0, int(column < 2)), pady=(0, 1)
            )
        cells = []
        for row in range(height):
            row_cells = []
            for column, (_, width) in enumerate(columns):
                cell = ttk.Label(grid, width=width, anchor="center", padding=(0, 2))
                cell.grid(row=row + 1, column=column, sticky="ew", padx=(0, int(column < 2)),
                          pady=(0, int(row < height - 1)))
                row_cells.append(cell)
            cells.append(row_cells)
        previews[quantity] = panel, cells
    navigation.bind("<<TreeviewSelect>>", select_point)
    navigation.selection_set(next(iter(steps)))
    select_point()
    window.protocol("WM_DELETE_WINDOW", close_window)
    window.update_idletasks()
    width = max(window.winfo_reqwidth(), window.minsize()[0])
    height = max(window.winfo_reqheight(), window.minsize()[1])
    x = max(0, (window.winfo_screenwidth() - width) // 2)
    y = max(0, (window.winfo_screenheight() - height) // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")
    tick()


def _refresh_measurement_controls():
    if measurement_protocol_button is not None and measurement_protocol_button.winfo_exists():
        measurement_protocol_button.configure(state="normal" if conn and is_device_ready else "disabled")


def _refresh_electrical_values(params):
    """Обновляет напряжение, ток и мощность в существующих полях."""
    if device_type == "single":
        readings = {"ch1": params}
        channel_labels = {
            "ch1": (param_voltage_label, param_current_label, param_power_label),
        }
    else:
        readings = params
        channel_labels = {
            "ch1": (param_v1_label, param_i1_label, param_p1_label),
            "ch2": (param_v2_label, param_i2_label, param_p2_label),
        }

    run = measurement_run
    show_average = run is not None and run.ready and run.device_type == device_type
    units = ("unit_v", "unit_a", "unit_kw")
    precision = (4, 4, 4)
    for channel, labels in channel_labels.items():
        for label, quantity, unit, decimals in zip(
            labels, MeasurementRun.QUANTITIES, units, precision
        ):
            if label is None or not label.winfo_exists():
                continue
            value = (
                run.series[(channel, quantity)].mean
                if show_average else readings[channel][quantity]
            )
            label.config(text=f"{value:.{decimals}f} {tr(unit)}")


def _check_param_queue():
    """Обрабатывает очередь обновления параметров. Гарантирует непрерывный цикл."""
    global latest_parameters
    energy_decimals = (latest_verification_settings or {}).get("decimal_places")
    if energy_decimals not in ENERGY_DECIMAL_PLACES:
        energy_decimals = 2
    try:
        while True:
            queued_reading = param_update_queue.get_nowait()
            if queued_reading is None:
                reading_started_at, params = None, None
            else:
                reading_started_at, params = queued_reading
            if params is None:
                latest_parameters = None
                _stop_measurement()
            elif not conn:
                continue
            elif (
                is_device_ready
                and measurement_run is not None
                and measurement_run.device_type == device_type
                and measurement_started_at is not None
                and reading_started_at >= measurement_started_at
            ):
                measurement_run.add_reading(params)
                readings = {"ch1": params} if device_type == "single" else params
                for (channel, quantity), samples in measurement_run.verification_samples.items():
                    samples.append(readings[channel][quantity])
            status_txt = tr("status_disconnected")

            if params is None:
                # Сброс
                for lbl in [param_energy_abs_label, param_energy_pos_label, param_energy_neg_label,
                            param_voltage_label, param_current_label, param_power_label,
                            param_nom_voltage_label, param_nom_current_label,
                            param_v1_label, param_i1_label, param_p1_label,
                            param_ch1_energy_abs_label, param_ch1_energy_pos_label, param_ch1_energy_neg_label,
                            param_ch1_nom_v_label, param_ch1_nom_i_label,
                            param_v2_label, param_i2_label, param_p2_label,
                            param_ch2_energy_abs_label, param_ch2_energy_pos_label, param_ch2_energy_neg_label,
                            param_ch2_nom_v_label, param_ch2_nom_i_label]:
                    if lbl and lbl.winfo_exists():
                        lbl.config(text=status_txt)
            else:
                latest_parameters = params
                _refresh_electrical_values(params)
                if device_type == "single":
                    if param_energy_abs_label and param_energy_abs_label.winfo_exists():
                        param_energy_abs_label.config(text=f"{params.get('energy_abs', 0):.{energy_decimals}f} {tr('unit_kwh')}")
                    if param_energy_pos_label and param_energy_pos_label.winfo_exists():
                        param_energy_pos_label.config(text=f"{params.get('energy_pos', 0):.{energy_decimals}f} {tr('unit_kwh')}")
                    if param_energy_neg_label and param_energy_neg_label.winfo_exists():
                        param_energy_neg_label.config(text=f"{params.get('energy_neg', 0):.{energy_decimals}f} {tr('unit_kwh')}")
                    if param_nom_voltage_label and param_nom_voltage_label.winfo_exists():
                        param_nom_voltage_label.config(text=f"{params.get('nom_voltage', 0):.0f} {tr('unit_v')}")
                    if param_nom_current_label and param_nom_current_label.winfo_exists():
                        param_nom_current_label.config(text=f"{params.get('nom_current', 0):.0f} {tr('unit_a')}")
                else:
                    # Канал 1
                    if param_ch1_energy_abs_label and param_ch1_energy_abs_label.winfo_exists():
                        param_ch1_energy_abs_label.config(text=f"{params['ch1']['energy_abs']:.{energy_decimals}f} {tr('unit_kwh')}")
                    if param_ch1_energy_pos_label and param_ch1_energy_pos_label.winfo_exists():
                        param_ch1_energy_pos_label.config(text=f"{params['ch1']['energy_pos']:.{energy_decimals}f} {tr('unit_kwh')}")
                    if param_ch1_energy_neg_label and param_ch1_energy_neg_label.winfo_exists():
                        param_ch1_energy_neg_label.config(text=f"{params['ch1']['energy_neg']:.{energy_decimals}f} {tr('unit_kwh')}")
                    if param_ch1_nom_v_label and param_ch1_nom_v_label.winfo_exists():
                        param_ch1_nom_v_label.config(text=f"{params['ch1']['nom_voltage']:.0f} {tr('unit_v')}")
                    if param_ch1_nom_i_label and param_ch1_nom_i_label.winfo_exists():
                        param_ch1_nom_i_label.config(text=f"{params['ch1']['nom_current']:.0f} {tr('unit_a')}")
                    # Канал 2
                    if param_ch2_energy_abs_label and param_ch2_energy_abs_label.winfo_exists():
                        param_ch2_energy_abs_label.config(text=f"{params['ch2']['energy_abs']:.{energy_decimals}f} {tr('unit_kwh')}")
                    if param_ch2_energy_pos_label and param_ch2_energy_pos_label.winfo_exists():
                        param_ch2_energy_pos_label.config(text=f"{params['ch2']['energy_pos']:.{energy_decimals}f} {tr('unit_kwh')}")
                    if param_ch2_energy_neg_label and param_ch2_energy_neg_label.winfo_exists():
                        param_ch2_energy_neg_label.config(text=f"{params['ch2']['energy_neg']:.{energy_decimals}f} {tr('unit_kwh')}")
                    if param_ch2_nom_v_label and param_ch2_nom_v_label.winfo_exists():
                        param_ch2_nom_v_label.config(text=f"{params['ch2']['nom_voltage']:.0f} {tr('unit_v')}")
                    if param_ch2_nom_i_label and param_ch2_nom_i_label.winfo_exists():
                        param_ch2_nom_i_label.config(text=f"{params['ch2']['nom_current']:.0f} {tr('unit_a')}")
    except queue.Empty:
        pass
    except Exception:
        pass  # Игнорируем любые ошибки виджетов
    finally:
        # Цикл продолжится в любом случае
        root.after(100, _check_param_queue)
        _refresh_measurement_controls()


# =============================================================================
# 5. Обработка событий GUI
# =============================================================================

def _update_port_list(ports=None):
    """Обновляет меню портов, сохраняя выбор, если он ещё доступен."""
    if ports is None:
        ports = list_com_ports()

    previous_port = port_var.get()
    choices = ports or [tr("status_no_ports")]

    port_menu.configure(values=choices)

    if previous_port in choices:
        port_var.set(previous_port)
    else:
        port_var.set(choices[0])


def refresh_ports():
    """Обновляет меню и показывает один и тот же список портов."""
    ports = list_com_ports()
    _update_port_list(ports)

    if ports:
        _show_emis_notice(
            tr("dlg_available_ports"),
            tr("dlg_ports_found").format("\n".join(ports)),
            wait=True,
        )
    else:
        _show_emis_notice(
            tr("dlg_available_ports"),
            tr("dlg_no_port"),
            wait=True,
        )


def _valid_modbus_address(value):
    return (
        1 <= len(value) <= 3
        and all(char in "0123456789" for char in value)
        and 1 <= int(value) <= 254
    )


def _show_emis_notice(title, message, *, parent=None, wait=False, action=None):
    parent = root if parent is None else parent
    dialog = tk.Toplevel(parent, background=emis_background)
    dialog.withdraw()
    dialog.title(title)
    dialog.transient(parent)
    dialog.resizable(False, False)

    card = ttk.Frame(dialog, style="Emis.Card.TFrame", padding=(18, 14))
    card.pack(padx=12, pady=12, fill="both", expand=True)
    ttk.Label(card, text=title, style="Emis.Heading.TLabel").pack(anchor="w")
    ttk.Label(card, text=message, justify="left", wraplength=460).pack(anchor="w", pady=(8, 12))
    button = ttk.Button(card, text="OK", command=dialog.destroy, style="Emis.Primary.TButton")
    if action is None:
        button.pack(anchor="e")
    else:
        label, callback = action
        button.configure(text=label, command=lambda: callback(dialog))
        button.pack(anchor="e")

    dialog.bind("<Escape>", lambda _event: dialog.destroy())
    dialog.bind("<Return>", lambda _event: button.invoke())
    dialog.update_idletasks()
    x = parent.winfo_rootx() + (parent.winfo_width() - dialog.winfo_reqwidth()) // 2
    y = parent.winfo_rooty() + (parent.winfo_height() - dialog.winfo_reqheight()) // 2
    dialog.geometry(f"{x:+d}{y:+d}")
    dialog.deiconify()
    dialog.wait_visibility()
    dialog.grab_set()
    button.focus_set()
    if wait:
        parent.wait_window(dialog)


def _choose_meter_type(reason):
    """Предлагает ручной выбор, когда определение по регистрам не удалось."""
    selected = None
    dialog = tk.Toplevel(root, background=emis_background)
    dialog.withdraw()
    dialog.title(tr("dlg_select_type"))
    dialog.transient(root)
    dialog.resizable(False, False)

    def select(meter_type):
        nonlocal selected
        selected = meter_type
        dialog.destroy()

    card = ttk.Frame(dialog, style="Emis.Card.TFrame", padding=(18, 14))
    card.pack(padx=12, pady=12, fill="both", expand=True)
    ttk.Label(card, text=tr("dlg_select_type_prompt").rstrip(":："), style="Emis.Heading.TLabel").pack(anchor="w")
    ttk.Label(card, text=reason, wraplength=360, justify="left", foreground="#53645F").pack(
        anchor="w", pady=(8, 12)
    )

    choices = ttk.Frame(card)
    choices.pack(fill="x")
    for column, (meter_type, label) in enumerate((("single", tr("dlg_single")), ("dual", tr("dlg_dual")))):
        choices.columnconfigure(column, weight=1, uniform="meter_choices")
        frame = ttk.Frame(choices)
        frame.grid(row=0, column=column, padx=6, sticky="ew")
        image = DEVICE_IMAGES.get(meter_type)
        if image:
            ttk.Label(frame, image=image).pack(pady=(0, 6))
        ttk.Button(
            frame, text=label, command=lambda value=meter_type: select(value),
            style="Emis.Primary.TButton", width=18,
        ).pack()
    cancel_button = ttk.Button(card, text=tr("dlg_cancel"), command=dialog.destroy)
    cancel_button.pack(anchor="e", pady=(12, 0))
    dialog.bind("<Escape>", lambda _event: dialog.destroy())
    dialog.update_idletasks()
    x = root.winfo_rootx() + (root.winfo_width() - dialog.winfo_reqwidth()) // 2
    y = root.winfo_rooty() + (root.winfo_height() - dialog.winfo_reqheight()) // 2
    dialog.geometry(f"{x:+d}{y:+d}")
    dialog.deiconify()
    dialog.wait_visibility()
    dialog.grab_set()
    cancel_button.focus_set()
    root.wait_window(dialog)
    return selected


def connect_scan():
    global conn, connect_btn, disconnect_btn, status_canvas, status_indicator, is_device_ready
    global search_window_ref, search_check_id

    # Отменяем старые таймеры
    if search_check_id: root.after_cancel(search_check_id); search_check_id = None

    port = port_var.get().strip()
    if not port or port == tr("status_no_ports"):
        messagebox.showerror(tr("dlg_error"), tr("dlg_no_port"))
        return

    if power_supply_pending_port and port.upper() == power_supply_pending_port.upper():
        messagebox.showwarning(tr("dlg_warning"), tr("power_supply_busy").format(port=port))
        return

    address = addr_var.get()
    if not _valid_modbus_address(address):
        messagebox.showerror(tr("dlg_input_error"), tr("invalid_modbus_address"))
        return
    preferred_slave = int(address)
    preferred_baud = int(speed_var.get())
    preferred_parity = parity_var.get()

    # Создаём окно поиска
    search_window_ref = tk.Toplevel(root)
    search_window_ref.title(tr("dlg_search"))
    search_window_ref.resizable(False, False)
    search_window_ref.transient(root)
    search_window_ref.grab_set()
    progress_label = tk.Label(search_window_ref, text=tr("dlg_searching"), padx=20, pady=20, width=44)
    progress_label.pack()
    search_window_ref.update_idletasks()

    x = root.winfo_rootx() + (root.winfo_width() - search_window_ref.winfo_width()) // 2
    y = root.winfo_rooty() + (root.winfo_height() - search_window_ref.winfo_height()) // 2
    search_window_ref.geometry(f"+{x}+{y}")

    root.config(cursor="watch")
    root.update()

    scan_result = [None]
    scan_error = [None]
    scan_cancelled = threading.Event()

    def do_scan():
        try:
            success, result = scan_device(
                port, preferred_slave, preferred_baud, preferred_parity,
                cancelled=scan_cancelled,
            )
            if success and not scan_cancelled.is_set():
                try:
                    result["device_type"] = detect_device_type(
                        result["port"], result["slave"], result["baud"], result["parity"]
                    )
                except Exception as error:
                    result["type_detection_error"] = tr("dlg_detect_type_error") + f"\n{error}"
            scan_result[0] = result if success else None
            scan_error[0] = None if success else result
        except Exception as e:
            scan_error[0] = str(e)

    worker = threading.Thread(target=do_scan, daemon=True)

    def do_cleanup(success=False, result_data=None, error_msg=None):
        global search_window_ref, search_check_id
        if scan_cancelled.is_set():
            return
        
        # Отмена таймеров
        if search_check_id: root.after_cancel(search_check_id); search_check_id = None

        if success and result_data:
            global conn, was_ever_connected, is_device_ready, device_type
            search_window_ref.destroy()
            search_window_ref = None
            root.config(cursor="")

            detected_type = result_data.get("device_type")
            selected_type = detected_type
            if selected_type is None:
                selected_type = _choose_meter_type(result_data["type_detection_error"])
                if selected_type is None:
                    return

            conn = result_data
            conn["device_type"] = selected_type
            conn["device_type_confirmed"] = detected_type is not None
            device_type = selected_type
            was_ever_connected = True
            is_device_ready = True

            addr_var.set(str(conn["slave"]))
            speed_var.set(str(conn["baud"]))
            parity_var.set(conn["parity"])

            create_parameters_tab()
            create_settings_tab()
            set_buttons_state("normal")
            connect_btn.config(state="disabled")
            refresh_btn.config(state="disabled")
            disconnect_btn.config(state="normal")
            status_canvas.itemconfig(status_indicator, fill="#66cc66")
            meter_status_details.pack(side="left")
            update_device_type_display()
            root.update_idletasks()
            root.minsize(root.winfo_reqwidth(), min(root.winfo_reqheight(), 500))
            start_time_reader()
            meter_type = tr("device_dual" if selected_type == "dual" else "device_single")
            _show_emis_notice(
                tr("dlg_connected"),
                tr("dlg_connected_msg").format(
                    meter_type, result_data["slave"], result_data["baud"], result_data["parity"]
                ),
            )

        elif error_msg:
            # Обработка ошибки (без изменений)
            try:
                if search_window_ref and search_window_ref.winfo_exists():
                    search_window_ref.grab_release()
                    search_window_ref.destroy()
            except: pass
            finally: search_window_ref = None
            root.config(cursor="")
            root.update_idletasks()

            if "could not open port" in error_msg or "FileNotFoundError" in error_msg:
                _show_emis_notice(tr("dlg_port_unavailable"), tr("dlg_port_unavailable_msg").format(port), wait=True)
            else:
                _show_emis_notice(tr("dlg_error"), error_msg, wait=True)

    def cancel_scan():
        """Отменяет поиск и не даёт его потоку завершить подключение."""
        global search_window_ref, search_check_id

        scan_cancelled.set()
        cancel_button.configure(state="disabled")

    def close_cancelled_scan():
        global search_window_ref
        try:
            if search_window_ref and search_window_ref.winfo_exists():
                search_window_ref.grab_release()
                search_window_ref.destroy()
        except tk.TclError:
            pass
        finally:
            search_window_ref = None

        root.config(cursor="")
        root.update_idletasks()

    cancel_button = ttk.Button(
        search_window_ref,
        text=tr("dlg_cancel"),
        command=cancel_scan,
        width=12,
    )
    cancel_button.pack(pady=(0, 15))

    search_window_ref.protocol("WM_DELETE_WINDOW", cancel_scan)

    def check_complete():
        global search_check_id
        search_check_id = None
        if worker.is_alive():
            search_check_id = root.after(100, check_complete)
        elif scan_cancelled.is_set():
            close_cancelled_scan()
        elif scan_result[0] is not None:
            do_cleanup(success=True, result_data=scan_result[0])
        else:
            do_cleanup(error_msg=str(scan_error[0] or tr("dlg_error")))

    worker.start()
    search_check_id = root.after(100, check_complete)


def disconnect_device(show_message=False):
    global conn, connect_btn, disconnect_btn, status_canvas, status_indicator, was_ever_connected, is_device_ready, device_type
    if not stop_time_reader():
        messagebox.showwarning(
            tr("dlg_warning"),
            tr("dlg_poll_stop_pending"),
        )
        return
    conn = None
    device_type = None
    meter_status_details.pack_forget()
    _update_meter_status_details(None)
    _stop_measurement()
    is_device_ready = False
    set_buttons_state("disabled")

    if connect_btn:
        connect_btn.config(state="normal")
    if refresh_btn:
        refresh_btn.config(state="normal")
    if disconnect_btn:
        disconnect_btn.config(state="disabled")
    if status_canvas and status_indicator:
        status_canvas.itemconfig(status_indicator, fill="red")

    # Сброс при отключении всех значений всех параметров
    param_update_queue.put(None)
    settings_update_queue.put(None)
    time_update_queue.put(tr("status_disconnected"))
    info_update_queue.put(None)
    root.after(0, _check_info_queue)
    root.after(0, _check_param_queue)
    root.after(0, _check_settings_queue)
    root.after(0, _check_time_queue)

    # Показываем сообщение только если было успешное подключение ранее
    if show_message and was_ever_connected:
        _show_emis_notice(tr("dlg_warning"), tr("dlg_disconnected"), wait=True)

    # Обновляем отображение типа
    update_device_type_display()


def trigger_disconnect():
    """Безопасный вызов отключения из фонового потока или таймера."""
    global conn, was_ever_connected

    # Проверяем, подключены ли мы вообще
    if conn is not None and was_ever_connected:
        disconnect_device(show_message=True)
    else:
        # Если просто нет подключения, тихо обновляем статус (чтобы не светить ошибку при старте)
        if status_canvas and status_indicator:
            status_canvas.itemconfig(status_indicator, fill="red")


def write_settings():
    """Записывает новые параметры связи и возобновляет чтение.

    Перед записью функция полностью останавливает фоновый поток, чтобы
    он не использовал COM-порт одновременно с операцией настройки.
    После успешной записи или ошибки чтение запускается снова.
    """
    global conn, writing_in_progress, post_write_cooldown_until

    if writing_in_progress:
        return

    if not conn:
        messagebox.showwarning(
            tr("dlg_warning"),
            tr("dlg_connect_first"),
        )
        return

    if not _show_confirm_dialog(
        tr("dlg_warning"),
        tr("dlg_write_params_warning"),
    ):
        return

    address = addr_var.get()
    if not _valid_modbus_address(address):
        _show_emis_notice(tr("dlg_input_error"), tr("invalid_modbus_address"), wait=True)
        return
    new_slave = int(address)

    original_write_button_text = write_btn.cget("text")
    writing_in_progress = True
    reader_stopped = False
    write_btn.config(text=tr("btn_writing"), state="disabled")

    try:
        new_baud = int(speed_var.get())
        new_parity = parity_var.get()
        connection = conn.copy()
        result_queue = queue.Queue()
        finished = tk.BooleanVar(master=root, value=False)

        def write_in_background():
            stopped = False
            try:
                stopped = stop_time_reader()
                success, result = (False, None)
                if stopped:
                    success, result = write_device_settings(
                        connection["port"], connection["slave"], connection["baud"], connection["parity"],
                        new_slave, new_baud, new_parity,
                    )
            except Exception as error:
                success, result = False, error
            result_queue.put((stopped, success, result))

        def check_write_result():
            if result_queue.empty():
                root.after(40, check_write_result)
            else:
                finished.set(True)

        root_cursor = root.cget("cursor")
        button_cursor = write_btn.cget("cursor")
        root.tk.call("tk", "busy", "hold", root._w, "-cursor", "watch")
        try:
            root.config(cursor="watch")
            write_btn.config(cursor="watch")
            _stop_measurement()
            threading.Thread(target=write_in_background, daemon=True).start()
            root.after(40, check_write_result)
            root.wait_variable(finished)
            reader_stopped, success, result = result_queue.get_nowait()
        finally:
            root.tk.call("tk", "busy", "forget", root._w)
            root.config(cursor=root_cursor)
            write_btn.config(cursor=button_cursor)

        if isinstance(result, Exception):
            raise result

        if not reader_stopped:
            _show_emis_notice(
                tr("dlg_write_error"),
                tr("dlg_port_not_initialized"),
                wait=True,
            )
            return

        if not success:
            # Возвращаем в интерфейс последние рабочие параметры.
            addr_var.set(str(conn["slave"]))
            speed_var.set(str(conn["baud"]))
            parity_var.set(conn["parity"])
            parity_combo.set(conn["parity"])

            _show_emis_notice(
                tr("dlg_write_error"),
                result,
                wait=True,
            )
            return

        # write_device_settings() уже дождалась перезапуска UART
        # и проверила связь по новым параметрам.
        conn.update(
            slave=result["slave"],
            baud=result["baud"],
            parity=result["parity"],
        )

        addr_var.set(str(conn["slave"]))
        speed_var.set(str(conn["baud"]))
        parity_var.set(conn["parity"])
        parity_combo.set(conn["parity"])

        # Короткая защита перед первым фоновым чтением.
        post_write_cooldown_until = time.time() + 1.0

        _show_emis_notice(
            tr("dlg_write_success"),
            tr("dlg_write_success_msg").format(
                result["slave"],
                result["baud"],
                result["parity"],
            ),
            wait=True,
        )

    except (TypeError, ValueError, KeyError) as error:
        _show_emis_notice(
            tr("dlg_write_error"),
            str(error),
            wait=True,
        )

    except Exception as error:
        _show_emis_notice(
            tr("dlg_write_error"),
            str(error),
            wait=True,
        )

    finally:
        writing_in_progress = False
        write_btn.config(
            text=original_write_button_text,
            state="normal" if conn and is_device_ready else "disabled",
        )
        root.update_idletasks()

        # Чтение возобновляется как после успеха, так и после ошибки.
        if reader_stopped and conn:
            start_time_reader()


def _write_time_to_device(year=None, month=None, day=None, hour=None, minute=None, second=None, parent_win=None):
    """Записывает время в устройство. Пропущенные компоненты берутся из текущего времени устройства.

    Args:
        year (int, optional): Год.
        month (int, optional): Месяц.
        day (int, optional): День.
        hour (int, optional): Час.
        minute (int, optional): Минута.
        second (int, optional): Секунда.
        parent_win (tk.Toplevel, optional): Родительское окно для сообщений.

    Returns:
        tuple: (успех, результат)
    """
    global conn
    if not conn:
        return False, tr("dlg_no_connection")

    # Читаем текущее время устройства
    success, result = read_device_time(conn["port"], conn["slave"], conn["baud"], conn["parity"])
    if success:
        cur = result["data"]
    else:
        cur = {"year": 2025, "month": 1, "day": 1, "hour": 0, "minute": 0, "second": 0}

    Y = year if year is not None else cur["year"]
    M = month if month is not None else cur["month"]
    D = day if day is not None else cur["day"]
    H = hour if hour is not None else cur["hour"]
    m = minute if minute is not None else cur["minute"]
    S = second if second is not None else cur["second"]

    success, msg = write_device_time(
        conn["port"], conn["slave"], conn["baud"], conn["parity"],
        Y, M, D, H, m, S
    )
    if not success:
        messagebox.showerror(tr("dlg_time_write_error"), msg, parent=parent_win)
        return False, msg

    _show_emis_notice(tr("dlg_write_success"), tr("dlg_time_written"), parent=parent_win, wait=True)
    start_time_reader()
    return True, "OK"


def open_time_settings():
    """Открывает окно настройки даты и времени."""
    global conn, is_device_ready
    if not conn:
        _show_emis_notice(tr("dlg_warning"), tr("dlg_no_connection"), wait=True)
        return
    if not is_device_ready:
        messagebox.showwarning(tr("dlg_warning"), tr("dlg_time_writing").split('\n')[0] + "...")
        return

    win = tk.Toplevel(root)
    win.title(tr("dlg_time_settings"))
    win.resizable(False, False)
    win.grab_set()
    win.transient(root)

    hour_var = tk.StringVar()
    minute_var = tk.StringVar()

    header_frame = tk.Frame(win)
    header_frame.pack(pady=(10, 5), fill="x")
    tk.Label(header_frame, text=tr("dlg_select_date"), anchor="w").pack(side="left", padx=(0, 10))

    cal = Calendar(win, selectmode='day', locale='ru_RU', date_pattern='dd.mm.yyyy',
                   showweeknumbers=False, font=("Segoe UI", 10))
    cal.pack(padx=15, pady=5)

    time_label_frame = tk.Frame(win)
    time_label_frame.pack(pady=(10, 0), fill="x")
    tk.Label(time_label_frame, text=tr("dlg_optional_time"), anchor="w").pack(side="left", padx=(0, 10))

    time_input_frame = tk.Frame(win)
    time_input_frame.pack(pady=5)
    tk.Label(time_input_frame, text=tr("dlg_hours")).grid(row=0, column=0, padx=(0, 2))
    tk.Label(time_input_frame, text=tr("dlg_minutes")).grid(row=0, column=2, padx=(2, 0))

    def make_validated_entry(parent, var, max_val):
        def validate(P):
            if P == "": return True
            if P.isdigit() and 0 <= int(P) <= max_val and len(P) <= len(str(max_val)):
                return True
            return False
        vcmd = (parent.register(validate), '%P')
        return tk.Entry(parent, textvariable=var, width=3, validate='key', validatecommand=vcmd)

    hour_entry = make_validated_entry(time_input_frame, hour_var, 23)
    hour_entry.grid(row=1, column=0, padx=(0, 2))
    tk.Label(time_input_frame, text=":").grid(row=1, column=1)
    minute_entry = make_validated_entry(time_input_frame, minute_var, 59)
    minute_entry.grid(row=1, column=2, padx=(2, 0))
    win.update_idletasks()
    x = root.winfo_rootx() + (root.winfo_width() - win.winfo_width()) // 2
    y = root.winfo_rooty() + (root.winfo_height() - win.winfo_height()) // 2
    win.geometry(f"+{x}+{y}")

    def apply_time():
        global manual_write_in_progress
        wait_win = None
        try:
            root.config(cursor="watch")
            root.update_idletasks()

            wait_win = tk.Toplevel(win, background=emis_background)
            wait_win.title(tr("dlg_time_settings"))
            wait_win.resizable(False, False)
            wait_win.transient(win)
            wait_win.grab_set()
            wait_win.config(cursor="watch")

            card = ttk.Frame(wait_win, style="Emis.Card.TFrame", padding=(18, 14))
            card.pack(padx=12, pady=12, fill="both", expand=True)
            ttk.Label(card, text=wait_win.title(), style="Emis.Heading.TLabel").pack(anchor="w")
            ttk.Label(card, text=tr("dlg_time_writing"), justify="left").pack(anchor="w", pady=(8, 0))

            wait_win.update_idletasks()
            wait_win.lift()
            wait_win.focus_force()
            wx = win.winfo_rootx() + (win.winfo_width() - wait_win.winfo_width()) // 2
            wy = win.winfo_rooty() + (win.winfo_height() - wait_win.winfo_height()) // 2
            wait_win.geometry(f"{wx:+d}{wy:+d}")
            wait_win.update()

            root.attributes('-disabled', True)
            root.update()

            manual_write_in_progress = True
            stop_time_reader()
            time.sleep(0.5)

            selected_date = cal.selection_get()
            hour_str = hour_var.get().strip()
            minute_str = minute_var.get().strip()

            success_read, cur = read_device_time(conn["port"], conn["slave"], conn["baud"], conn["parity"])
            cur = cur["data"] if success_read else {"year": 2025, "month": 1, "day": 1, "hour": 0, "minute": 0, "second": 0}

            Y, M, D = selected_date.year, selected_date.month, selected_date.day
            H = int(hour_str) if hour_str else cur["hour"]
            m = int(minute_str) if minute_str else cur["minute"]
            S = cur["second"]

            success, msg = write_device_time(conn["port"], conn["slave"], conn["baud"], conn["parity"], Y, M, D, H, m, S)
            time.sleep(1.0)

            if wait_win and wait_win.winfo_exists():
                wait_win.destroy()
            wait_win = None

            root.attributes('-disabled', False)
            root.config(cursor="")
            root.update_idletasks()

            if not success:
                if "Неверный дескриптор" in msg or "Bad file descriptor" in msg:
                    messagebox.showerror(tr("dlg_write_error"), tr("dlg_port_unavailable_msg").format(conn["port"]), parent=win)
                else:
                    messagebox.showerror(tr("dlg_write_error"), msg, parent=win)
            else:
                new_time_str = f"{Y:04}-{M:02}-{D:02} {H:02}:{m:02}:{S:02}"
                _show_meter_time(new_time_str)
                time_update_queue.put(new_time_str)
                root.after(0, _check_time_queue)

                _show_emis_notice(tr("dlg_write_success"), tr("dlg_time_written"), parent=win, wait=True)
                win.destroy()

        except Exception as e:
            if wait_win and wait_win.winfo_exists(): wait_win.destroy()
            root.attributes('-disabled', False)
            root.config(cursor="")
            root.update_idletasks()
            messagebox.showerror(tr("dlg_input_error"), f"{tr('dlg_write_failed')}:\n{e}", parent=win)
        finally:
            if wait_win and wait_win.winfo_exists(): wait_win.destroy()
            root.attributes('-disabled', False)
            root.config(cursor="")
            root.update_idletasks()
            manual_write_in_progress = False
            start_time_reader()

    def on_cancel():
        win.destroy()

    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=10)
    ttk.Button(btn_frame, text=tr("dlg_cancel"), command=on_cancel, width=10).pack(side="left", padx=5)
    ttk.Button(btn_frame, text=tr("dlg_apply"), command=apply_time, style="Emis.Primary.TButton").pack(side="left", padx=5)


def sync_pc_time():
    """Синхронизирует время устройства с текущим временем ПК."""
    global conn, is_device_ready
    if not conn:
        _show_emis_notice(tr("dlg_warning"), tr("dlg_no_connection"), wait=True)
        return
    if not is_device_ready:
        messagebox.showwarning(tr("dlg_warning"), tr("dlg_time_writing").split('\n')[0])  # Используем существующий ключ
        return

    stop_time_reader()
    time.sleep(0.8)

    root.config(cursor="watch")
    root.update()

    try:
        success, result = sync_device_with_pc_time(
            conn["port"], conn["slave"], conn["baud"], conn["parity"]
        )
        if not success:
            # Проверяем на ошибку дескриптора
            if "Неверный дескриптор" in result or "Bad file descriptor" in result:
                messagebox.showerror(tr("dlg_write_error"),
                    tr("dlg_port_unavailable_msg").format(conn["port"]))
            else:
                messagebox.showerror(tr("dlg_sync_error"), result)
            return

        _show_emis_notice(tr("dlg_write_success"), tr("dlg_sync_success").format(result), wait=True)
        _show_meter_time(result)
        # Принудительно обновляем очередь времени
        time_update_queue.put(result)
        root.after(0, _check_time_queue)
        start_time_reader()

    except Exception as e:
        messagebox.showerror(tr("dlg_input_error"), f"{tr('dlg_write_failed')}:\n{e}")
    finally:
        root.config(cursor="")


def clear_energy_values():
    global conn, operation_in_progress
    if not conn:
        _show_emis_notice(tr("dlg_warning"), tr("dlg_no_connection"), wait=True)
        return

    pwd_res = _prompt_password()
    if pwd_res is None:
        return  # Пользователь закрыл окно или нажал "Отмена" — тихо выходим
    if not pwd_res:
        messagebox.showerror(tr("dlg_error"), tr("dlg_wrong_password"))
        return

    operation_in_progress = True
    stop_time_reader()
    root.config(cursor="watch")
    root.update()

    try:
        local_conn = conn.copy() if conn else None
        if not local_conn:
            raise Exception(tr("dlg_no_connection"))

        if not _show_confirm_dialog(
            tr("dlg_clear_confirm"),
            tr("dlg_clear_confirm_msg")
        ):
            return

        success, msg = clear_device_energy(
            local_conn["port"], local_conn["slave"], local_conn["baud"], local_conn["parity"]
        )
        if not success:
            messagebox.showerror(tr("dlg_clear_error"), msg)
            return

        _show_emis_notice(tr("dlg_write_success"), tr("dlg_clear_success"), wait=True)

        # Сбрасываем только актуальную очередь настроек
        settings_update_queue.put(None)
        root.after(0, _check_settings_queue)

    except Exception as e:
        messagebox.showerror(tr("dlg_input_error"), str(e))
    finally:
        operation_in_progress = False
        root.config(cursor="")
        start_time_reader()


def _prompt_password():
    """Показывает модальное окно для ввода пароля.
    Возвращает: True (верно), False (неверно), None (отмена/закрытие)"""
    result = [None]
    win = tk.Toplevel(root)
    win.title(tr("dlg_password"))
    win.transient(root)
    win.grab_set()
    win.resizable(False, False)

    tk.Label(win, text=tr("dlg_password_prompt"), font=("Segoe UI", 10)).pack(pady=(15, 5))
    password_var = tk.StringVar()
    entry = tk.Entry(win, textvariable=password_var, show="*", font=("Consolas", 10), width=15)
    entry.pack(pady=5)
    entry.focus()

    def on_ok():
        if password_var.get() == "0451":
            result[0] = True
        else:
            result[0] = False
        win.destroy()

    def on_cancel():
        result[0] = None
        win.destroy()

    win.protocol("WM_DELETE_WINDOW", on_cancel)
    entry.bind('<Return>', lambda e: on_ok())

    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=10)
    ttk.Button(btn_frame, text=tr("dlg_cancel"), command=on_cancel, width=10).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="OK", command=on_ok, style="Emis.Primary.TButton").pack(side="left", padx=5)

    win.update_idletasks()
    x = root.winfo_rootx() + (root.winfo_width() - win.winfo_width()) // 2
    y = root.winfo_rooty() + (root.winfo_height() - win.winfo_height()) // 2
    win.geometry(f"+{x}+{y}")

    root.wait_window(win)
    return result[0]


def show_help():
    """Открывает справку с оглавлением."""
    from help_topics import HELP_TOPICS

    existing = getattr(show_help, "window", None)
    if existing is not None and existing.winfo_exists():
        existing.deiconify()
        existing.lift()
        existing.focus_set()
        return

    topics = HELP_TOPICS[current_language]
    window = tk.Toplevel(root)
    show_help.window = window
    window.title(tr("dlg_help"))
    window.transient(root)
    width, height = 720, 460
    x = max(0, (window.winfo_screenwidth() - width) // 2)
    y = max(0, (window.winfo_screenheight() - height) // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")
    window.minsize(500, 300)

    content = ttk.Frame(window, padding=12)
    content.pack(fill="both", expand=True)
    content.columnconfigure(1, weight=1)
    content.rowconfigure(0, weight=1)

    navigation = ttk.Treeview(
        content, show="tree", selectmode="browse", takefocus=True
    )
    navigation.column("#0", width=180, minwidth=140, stretch=False)
    navigation.grid(row=0, column=0, sticky="ns", padx=(0, 12))

    article = ttk.Frame(content)
    article.grid(row=0, column=1, sticky="nsew")
    article.columnconfigure(0, weight=1)
    article.rowconfigure(1, weight=1)

    title = ttk.Label(article, style="Emis.Heading.TLabel")
    title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
    body = tk.Text(article, wrap="word", font="TkDefaultFont", padx=8, pady=6)
    scrollbar = ttk.Scrollbar(article, orient="vertical", command=body.yview)
    body.configure(yscrollcommand=scrollbar.set)
    body.grid(row=1, column=0, sticky="nsew")
    scrollbar.grid(row=1, column=1, sticky="ns")

    def show_topic(_event=None):
        selection = navigation.selection()
        if selection:
            heading, text = topics[int(selection[0])]
            title.configure(text=heading)
            body.configure(state="normal")
            body.delete("1.0", tk.END)
            body.insert("1.0", text)
            body.configure(state="disabled")
            body.yview_moveto(0)

    for index, (heading, _) in enumerate(topics):
        navigation.insert("", "end", iid=str(index), text=heading)
    navigation.bind("<<TreeviewSelect>>", show_topic)
    navigation.selection_set("0")
    navigation.focus("0")
    navigation.focus_set()
    show_topic()
    window.bind("<Escape>", lambda _event: window.destroy())


def show_update_available_dialog(latest_version, release_url):
    """Показывает окно с предложением скачать новую версию."""
    dialog = tk.Toplevel(root)
    dialog.title(tr("dlg_update_check"))
    dialog.resizable(False, False)
    dialog.transient(root)
    dialog.grab_set()

    def close_dialog():
        """Закрывает окно обновления."""
        if dialog.winfo_exists():
            dialog.destroy()

    def download_update():
        """Открывает страницу опубликованного GitHub Release."""
        webbrowser.open(release_url)
        close_dialog()

    dialog.protocol(
        "WM_DELETE_WINDOW",
        close_dialog,
    )

    tk.Label(
        dialog,
        text=tr("dlg_update_check"),
        font=("Segoe UI", 11, "bold"),
    ).pack(
        padx=25,
        pady=(18, 10),
    )

    tk.Label(
        dialog,
        text=tr("msg_update_available").format(
            latest_version=latest_version,
            current_version=APP_VERSION,
        ),
        justify="left",
        wraplength=380,
    ).pack(
        padx=25,
        pady=(0, 15),
    )

    button_frame = tk.Frame(dialog)
    button_frame.pack(
        pady=(0, 18),
    )

    ttk.Button(
        button_frame,
        text=tr("btn_close"),
        command=close_dialog,
        width=14,
    ).pack(
        side="left",
        padx=5,
    )

    ttk.Button(
        button_frame,
        text=tr("btn_download_update"),
        command=download_update,
        width=14,
    ).pack(
        side="left",
        padx=5,
    )

    dialog.update_idletasks()

    x = root.winfo_rootx() + (
        root.winfo_width() - dialog.winfo_width()
    ) // 2
    y = root.winfo_rooty() + (
        root.winfo_height() - dialog.winfo_height()
    ) // 2

    dialog.geometry(f"+{x}+{y}")


def check_for_updates(show_messages=True):
    """Проверяет наличие новой опубликованной версии на GitHub."""
    global update_check_in_progress

    if update_check_in_progress:
        return

    update_check_in_progress = True
    result_queue = queue.Queue()

    root.config(cursor="watch")
    root.update_idletasks()

    def finish_check(success, result):
        """Показывает результат проверки в основном потоке Tkinter."""
        global update_check_in_progress

        update_check_in_progress = False
        root.config(cursor="")

        if not success:
            if show_messages:
                message_key = (
                    "msg_update_network_error"
                    if result == "network_error"
                    else "msg_update_invalid_data"
                )

                messagebox.showerror(
                    tr("dlg_update_check"),
                    tr(message_key),
                )

            return

        latest_version = result["version"]
        release_url = result["release_url"]

        try:
            update_available = is_version_newer(
                latest_version,
                APP_VERSION,
            )
        except ValueError:
            if show_messages:
                messagebox.showerror(
                    tr("dlg_update_check"),
                    tr("msg_update_invalid_data"),
                )

            return

        if update_available:
            show_update_available_dialog(
                latest_version,
                release_url,
            )
            return

        if show_messages:
            messagebox.showinfo(
                tr("dlg_update_check"),
                tr("msg_update_current").format(
                    current_version=APP_VERSION,
                ),
            )

    def wait_for_result():
        """Проверяет очередь из главного потока Tkinter."""
        try:
            success, result = result_queue.get_nowait()
        except queue.Empty:
            root.after(100, wait_for_result)
            return

        finish_check(success, result)

    def check_in_background():
        """Выполняет сетевой запрос без блокировки интерфейса."""
        try:
            success, result = get_latest_release()
        except Exception:
            success = False
            result = "network_error"

        result_queue.put(
            (
                success,
                result,
            )
        )

    threading.Thread(
        target=check_in_background,
        daemon=True,
    ).start()

    root.after(100, wait_for_result)


def _create_measurement_controls(parent):
    global measurement_button, measurement_status, measurement_protocol_button

    measurement_protocol_button = ttk.Button(
        parent,
        text=tr("measurement_protocol"),
        command=_open_verification,
        style="Emis.Primary.TButton",
        state="disabled",
    )
    measurement_protocol_button.pack(pady=(4, 0))
    _refresh_measurement_controls()


def create_parameters_tab():
    """Создаёт вкладку «Параметры» в зависимости от типа счётчика."""
    global param_voltage_label, param_current_label, param_power_label
    global param_v1_label, param_i1_label, param_p1_label
    global param_v2_label, param_i2_label, param_p2_label
    global param_energy_abs_label, param_energy_pos_label, param_energy_neg_label
    global param_nom_voltage_label, param_nom_current_label
    global param_ch1_energy_abs_label, param_ch1_energy_pos_label, param_ch1_energy_neg_label
    global param_ch1_nom_v_label, param_ch1_nom_i_label
    global param_ch2_energy_abs_label, param_ch2_energy_pos_label, param_ch2_energy_neg_label
    global param_ch2_nom_v_label, param_ch2_nom_i_label

    if device_type is None:
        return

    for widget in tab_params.winfo_children():
        widget.destroy()

    def channel_card(parent, column, heading=None):
        card = ttk.Frame(parent, padding=(16, 14), style="Emis.Card.TFrame")
        card.grid(row=0, column=column, sticky="nsew", padx=5)
        card.columnconfigure(1, weight=1)
        row = 0
        if heading:
            ttk.Label(card, text=tr(heading), style="Emis.Heading.TLabel").grid(
                row=row, column=0, columnspan=2, sticky="w", pady=(0, 7)
            )
            row += 1

        labels = []
        for section, keys in (
            ("lbl_nominal", ("lbl_nom_v", "lbl_nom_i")),
            ("lbl_energy", ("lbl_abs", "lbl_pos", "lbl_neg")),
            ("lbl_current_params", ("lbl_voltage", "lbl_current", "lbl_power")),
        ):
            if labels:
                ttk.Separator(card).grid(row=row, column=0, columnspan=2, sticky="ew", pady=7)
                row += 1
            ttk.Label(card, text=tr(section).rstrip(":："), style="Emis.Heading.TLabel").grid(
                row=row, column=0, columnspan=2, sticky="w", pady=(2, 3)
            )
            row += 1
            for key in keys:
                ttk.Label(card, text=tr(key).rstrip(":："), foreground="#53645F").grid(
                    row=row, column=0, sticky="w", padx=(0, 12), pady=3
                )
                value = ttk.Label(card, text=tr("status_disconnected"), font=("Consolas", 11), foreground=emis_text)
                value.grid(row=row, column=1, sticky="nw", pady=3)
                labels.append(value)
                row += 1
                if key == "lbl_abs":
                    ttk.Label(card, text=tr("lbl_abs_hint"), foreground="#53645F").grid(
                        row=row, column=0, columnspan=2, sticky="w", pady=(0, 2)
                    )
                    row += 1
        return labels

    single = device_type == "single"
    cards = ttk.Frame(tab_params, style="Emis.Background.TFrame")
    cards.pack(fill="x" if not single else "none", padx=15, pady=(14, 8))
    if single:
        (
            param_nom_voltage_label, param_nom_current_label,
            param_energy_abs_label, param_energy_pos_label, param_energy_neg_label,
            param_voltage_label, param_current_label, param_power_label,
        ) = channel_card(cards, 0)
    else:
        cards.columnconfigure((0, 1), weight=1, uniform="meter_channels")
        (
            param_ch1_nom_v_label, param_ch1_nom_i_label,
            param_ch1_energy_abs_label, param_ch1_energy_pos_label, param_ch1_energy_neg_label,
            param_v1_label, param_i1_label, param_p1_label,
        ) = channel_card(cards, 0, "lbl_channel_a")
        (
            param_ch2_nom_v_label, param_ch2_nom_i_label,
            param_ch2_energy_abs_label, param_ch2_energy_pos_label, param_ch2_energy_neg_label,
            param_v2_label, param_i2_label, param_p2_label,
        ) = channel_card(cards, 1, "lbl_channel_b")

    _create_measurement_controls(tab_params)
    if power_supply_visible:
        _create_power_supply_panel(tab_params)


def create_settings_tab():
    """Создаёт вкладку «Настройки прибора»."""
    global settings_max_i_a_label, settings_max_i_b_label
    global settings_sens_v_label, settings_sens_i_label
    global settings_decimal_combo
    global settings_pulse_combos

    if device_type is None:
        return

    for widget in tab_settings.winfo_children():
        widget.destroy()
    settings_action_buttons.clear()
    control_state = "normal" if conn and is_device_ready else "disabled"

    center_block = ttk.Frame(tab_settings, padding=(22, 16), style="Emis.Card.TFrame")
    center_block.pack(pady=20)
    grid_frame = ttk.Frame(center_block)
    grid_frame.pack()
    ttk.Label(grid_frame, text=tr("tab_settings"), style="Emis.Heading.TLabel").grid(
        row=0, column=0, columnspan=3, sticky="w", pady=(0, 8)
    )

    def add_caption(row, key):
        ttk.Label(
            grid_frame, text=tr(key).rstrip(":："), justify="left",
            foreground="#53645F", wraplength=180,
        ).grid(row=row, column=0, sticky="w", padx=(0, 14), pady=4)

    def add_editable_row(row, key, command):
        add_caption(row, key)
        value = ttk.Label(
            grid_frame, text=tr("status_disconnected"), font=("Consolas", 11),
            foreground=emis_text, width=-12, anchor="w",
        )
        value.grid(row=row, column=1, sticky="nw", pady=4)
        button = ttk.Button(
            grid_frame, text=tr("btn_change"), command=command, width=10, state=control_state,
        )
        button.grid(row=row, column=2, sticky="nw", pady=4, padx=(10, 0))
        settings_action_buttons.append(button)
        return value

    dual = device_type == "dual"
    settings_max_i_a_label = add_editable_row(
        1, "lbl_max_current_a" if dual else "lbl_max_current", _on_change_max_current_a
    )
    settings_max_i_b_label = None
    if dual:
        settings_max_i_b_label = add_editable_row(2, "lbl_max_current_b", _on_change_max_current_b)

    sensitivity_row = 3 if dual else 2
    settings_sens_v_label = add_editable_row(sensitivity_row, "lbl_sens_voltage", _on_change_sens_voltage)
    settings_sens_i_label = add_editable_row(sensitivity_row + 1, "lbl_sens_current", _on_change_sens_current)
    add_caption(sensitivity_row + 2, "lbl_decimal")
    settings_decimal_combo = ttk.Combobox(
        grid_frame,
        values=tuple(str(value) for value in ENERGY_DECIMAL_PLACES),
        state="readonly" if control_state == "normal" else "disabled",
        width=8,
    )
    settings_decimal_combo.grid(row=sensitivity_row + 2, column=1, sticky="nw", pady=4)
    settings_decimal_combo.bind('<<ComboboxSelected>>', _on_change_decimal_places)

    # Постоянная импульсного выхода: один или два канала.
    settings_pulse_combos = {}

    channels = [("a", "lbl_pulse_constant_ch1")]
    if device_type == "dual":
        channels.append(("b", "lbl_pulse_constant_ch2"))

    for row, (channel, label_key) in enumerate(channels, start=sensitivity_row + 3):
        add_caption(row, label_key)

        combo = ttk.Combobox(
            grid_frame,
            values=[str(value) for value in PULSE_CONSTANT_VALUES],
            state="disabled",
            width=8,
        )
        combo.grid(row=row, column=1, sticky="nw", pady=4)
        settings_pulse_combos[channel] = combo
        combo.bind(
            "<<ComboboxSelected>>",
            lambda event, selected_channel=channel:
                _on_change_pulse_constant(selected_channel),
        )

        tk.Label(
            grid_frame,
            text=tr("unit_imp_kwh"),
        ).grid(
            row=row, column=2, sticky="nw",
            pady=4, padx=(10, 0),
        )

    ttk.Separator(center_block).pack(fill="x", pady=12)
    clear_button = ttk.Button(
        center_block, text=tr("btn_clear_energy"),
        command=clear_energy_values, style="Emis.Primary.TButton", state=control_state,
    )
    clear_button.pack()
    settings_action_buttons.append(clear_button)


def create_info_tab():
    """Создаёт вкладку «Информация о приборе»."""
    global info_serial_label, info_manufacturer_label, info_meter_type_label
    global info_sw_version_label, info_release_date_label
    global info_series_label, info_channels_label
    global info_power_supply_label, info_manufacture_date_label
    global info_sequence_number_label

    for widget in tab_info.winfo_children():
        widget.destroy()
    info_action_buttons.clear()
    control_state = "normal" if conn and is_device_ready else "disabled"

    grid_frame = ttk.Frame(tab_info, padding=(22, 16), style="Emis.Card.TFrame")
    grid_frame.pack(pady=20)

    def add_heading(row, key):
        ttk.Label(grid_frame, text=tr(key).rstrip(":："), style="Emis.Heading.TLabel").grid(
            row=row, column=0, columnspan=3, sticky="w", pady=(0, 8)
        )

    def add_row(row, key):
        ttk.Label(grid_frame, text=tr(key).rstrip(":："), justify="left", foreground="#53645F").grid(
            row=row, column=0, sticky="w", padx=(0, 14), pady=4
        )
        value = ttk.Label(grid_frame, text=tr("status_disconnected"), font=("Consolas", 11), foreground=emis_text, width=-17, anchor="w")
        value.grid(row=row, column=1, sticky="nw", pady=4)
        return value

    add_heading(0, "lbl_info_heading")
    info_serial_label = add_row(1, "lbl_serial")
    info_manufacturer_label = add_row(2, "lbl_manufacturer")
    info_meter_type_label = add_row(3, "lbl_meter_type")
    info_sw_version_label = add_row(4, "lbl_info_sw_version")
    info_release_date_label = add_row(5, "lbl_release_date")

    # Кнопки редактирования только для верхних информационных полей.
    editable_fields = (
        ("serial_number", "lbl_serial", info_serial_label),
        ("manufacturer", "lbl_manufacturer", info_manufacturer_label),
        ("meter_type", "lbl_meter_type", info_meter_type_label),
        ("sw_version", "lbl_sw_version", info_sw_version_label),
        ("release_date", "lbl_release_date", info_release_date_label),
    )

    for row, (field, label_key, value_label) in enumerate(editable_fields, start=1):
        button = ttk.Button(
            grid_frame,
            text=tr("btn_change"),
            command=lambda field=field, key=label_key, label=value_label:
                _on_change_device_info(field, key, label),
            width=10,
            state=control_state,
        )
        info_action_buttons.append(button)
        button.grid(
            row=row,
            column=2,
            sticky="nw",
            pady=4,
            padx=(10, 0),
        )

    # Автозаполнение по отсканированному серийному номеру.
    autofill_button = ttk.Button(
        grid_frame,
        text=tr("btn_info_autofill"),
        command=_show_device_info_autofill_dialog,
        style="Emis.Primary.TButton",
        width=24,
        state=control_state,
    )
    info_action_buttons.append(autofill_button)
    autofill_button.grid(
        row=6,
        column=0,
        columnspan=3,
        pady=(12, 5),
    )

    ttk.Separator(grid_frame).grid(row=7, column=0, columnspan=3, sticky="ew", pady=12)

    add_heading(8, "lbl_serial_decoding")
    info_series_label = add_row(9, "lbl_meter_series")
    info_channels_label = add_row(10, "lbl_info_channels")
    info_power_supply_label = add_row(11, "lbl_power_supply")
    info_manufacture_date_label = add_row(12, "lbl_manufacture_date")
    info_sequence_number_label = add_row(13, "lbl_sequence_number")


def widget_exists(w):
    """Проверяет, существует ли виджет в Tkinter."""
    try:
        return w.winfo_exists() if w else False
    except:
        return False


def _check_settings_queue():
    """Обрабатывает очередь обновления настроек."""
    global latest_verification_settings, latest_tariff_periods

    try:
        while True:
            settings = settings_update_queue.get_nowait()
            latest_verification_settings = settings
            if settings is None or "tariff_periods" in settings:
                latest_tariff_periods = None if settings is None else settings["tariff_periods"]
                _refresh_active_tariff()
            # Обновляем постоянную импульсного выхода по каналам.
            for channel, combo in settings_pulse_combos.items():
                key = (
                    "pulse_constant_ch1"
                    if channel == "a"
                    else "pulse_constant_ch2"
                )
                value = settings.get(key) if settings is not None else None

                if value is None:
                    combo.set("")
                    combo.configure(state="disabled")
                else:
                    # Получаем путь фокуса Tk без поиска Python-виджета.
                    focus_path = str(combo.tk.call("focus"))
                    combo_path = str(combo)
                    selecting = (
                        focus_path == combo_path
                        or focus_path.startswith(combo_path + ".")
                    )

                    if combo.instate(["disabled"]) or not selecting:
                        combo.set(str(value))

                    # Во время операции выбор остаётся заблокированным.
                    combo.configure(
                        state="disabled"
                        if not conn or settings_dialog_open or operation_in_progress
                        else "readonly"
                    )
            if settings is None:
                if settings_max_i_a_label: settings_max_i_a_label.config(text=tr("status_disconnected"))
                if settings_max_i_b_label: settings_max_i_b_label.config(text=tr("status_disconnected"))
                if settings_sens_v_label: settings_sens_v_label.config(text=tr("status_disconnected"))
                if settings_sens_i_label: settings_sens_i_label.config(text=tr("status_disconnected"))
            else:
                if settings_max_i_a_label: settings_max_i_a_label.config(text=f"{settings['max_current_a']:.0f} {tr('unit_a')}")
                if settings_max_i_b_label:
                    if 'max_current_b' in settings:
                        settings_max_i_b_label.config(text=f"{settings['max_current_b']:.0f} {tr('unit_a')}")
                    else:
                        settings_max_i_b_label.config(text=tr("status_disconnected"))
                if settings_sens_v_label: settings_sens_v_label.config(text=f"{settings['sens_voltage']:.1f} {tr('unit_percent')}")
                if settings_sens_i_label: settings_sens_i_label.config(text=f"{settings['sens_current']:.1f} {tr('unit_percent')}")

                # Безопасное обновление Combobox (избегаем ошибки 'popdown')
                try:
                    if settings_decimal_combo and settings_decimal_combo.focus_get() != settings_decimal_combo:
                        settings_decimal_combo.set(str(settings['decimal_places']))
                except Exception:
                    # Если фокус не удалось определить (например, при пересоздании), пропускаем обновление
                    pass
    except queue.Empty:
        pass
    root.after(100, _check_settings_queue)


def _set_app_title(info=None):
    title = f"{tr('app_name')} V{APP_VERSION}"
    serial_number = ((info or {}).get("serial_number") or "").strip()
    if serial_number:
        title += f" · № {serial_number}"
    if root.title() != title:
        root.title(title)


def _update_meter_status_details(info):
    _set_app_title(info)
    for field, label in meter_status_values.items():
        value = (info or {}).get(field)
        label.config(text=(value or "").strip() or "—")


def _check_info_queue():
    """Обрабатывает очередь обновления информации о приборе."""
    global latest_verification_info
    try:
        while True:
            info = info_update_queue.get_nowait()
            if conn or info is None:
                _update_meter_status_details(info)
            latest_verification_info = info
            if info is None:
                if info_serial_label: info_serial_label.config(text=tr("status_disconnected"))
                if info_manufacturer_label: info_manufacturer_label.config(text=tr("status_disconnected"))
                if info_meter_type_label: info_meter_type_label.config(text=tr("status_disconnected"))
                if info_sw_version_label: info_sw_version_label.config(text=tr("status_disconnected"))
                if info_release_date_label: info_release_date_label.config(text=tr("status_disconnected"))
                if info_series_label: info_series_label.config(text=tr("status_disconnected"))
                if info_channels_label: info_channels_label.config(text=tr("status_disconnected"))
                if info_power_supply_label: info_power_supply_label.config(text=tr("status_disconnected"))
                if info_manufacture_date_label: info_manufacture_date_label.config(text=tr("status_disconnected"))
                if info_sequence_number_label: info_sequence_number_label.config(text=tr("status_disconnected"))
            else:
                if info_serial_label: info_serial_label.config(text=info.get('serial_number', tr("status_disconnected")))
                serial_details = decode_meter_serial_number(
                    info.get("serial_number", "")
                )

                if serial_details is None:
                    decoded_values = {
                        "series": "—",
                        "channels": "—",
                        "power_supply": "—",
                        "manufacture_date": "—",
                        "sequence_number": "—",
                    }
                else:
                    decoded_values = {
                        "series": serial_details["series"],
                        "channels": tr(
                            "serial_single_channel"
                            if serial_details["channel_code"] == "1"
                            else "serial_dual_channel"
                        ),
                        "power_supply": tr(
                            "serial_power_dc"
                            if serial_details["power_code"] == "1"
                            else "serial_power_ac"
                        ),
                        "manufacture_date": (
                            f"{serial_details['month']:02d}."
                            f"{serial_details['year']}"
                        ),
                        "sequence_number": (
                            serial_details["sequence_number"]
                        ),
                    }

                if info_series_label:
                    info_series_label.config(
                        text=decoded_values["series"],
                    )

                if info_channels_label:
                    info_channels_label.config(
                        text=decoded_values["channels"],
                    )

                if info_power_supply_label:
                    info_power_supply_label.config(
                        text=decoded_values["power_supply"],
                    )

                if info_manufacture_date_label:
                    info_manufacture_date_label.config(
                        text=decoded_values["manufacture_date"],
                    )

                if info_sequence_number_label:
                    info_sequence_number_label.config(
                        text=decoded_values["sequence_number"],
                    )
                if info_manufacturer_label: info_manufacturer_label.config(text=info.get('manufacturer', tr("status_disconnected")))
                if info_meter_type_label: info_meter_type_label.config(text=info.get('meter_type', tr("status_disconnected")))
                if info_sw_version_label: info_sw_version_label.config(text=info.get('sw_version', tr("status_disconnected")))
                if info_release_date_label: info_release_date_label.config(text=info.get('release_date', tr("status_disconnected")))
    except queue.Empty:
        pass
    root.after(100, _check_info_queue)


def _show_numeric_input_dialog(title, prompt, current_value, write_func=None):
    """Показывает диалог ввода числового значения."""
    global settings_dialog_open

    dialog = tk.Toplevel(root)
    dialog.title(title)
    dialog.grab_set()
    dialog.resizable(False, False)

    tk.Label(dialog, text=prompt, font=("Segoe UI", 10)).pack(pady=(15, 5), padx=20)

    value_var = tk.StringVar(value=f"{current_value:.2f}" if current_value != tr("status_disconnected") and current_value is not None else "")
    entry = tk.Entry(dialog, textvariable=value_var, font=("Consolas", 12), width=15)
    entry.pack(pady=5)
    entry.focus()
    entry.select_range(0, 'end')

    def on_ok():
        global settings_dialog_open
        try:
            new_value = float(value_var.get().replace(',', '.'))
            if not conn:
                messagebox.showerror(tr("dlg_input_error"), tr("dlg_no_connection"), parent=dialog)
                return

            if write_func:
                success, msg = write_func(conn["port"], conn["slave"], conn["baud"], conn["parity"], new_value)
                if success:
                    _show_emis_notice(tr("dlg_write_success"), tr("dlg_value_written"), parent=dialog, wait=True)
                else:
                    messagebox.showerror(tr("dlg_write_error"), msg, parent=dialog)
            settings_dialog_open = False
            dialog.destroy()
            start_time_reader()
        except Exception as e:
            messagebox.showerror(tr("dlg_input_error"), str(e), parent=dialog)

    def on_cancel():
        global settings_dialog_open
        settings_dialog_open = False
        dialog.destroy()
        start_time_reader()

    entry.bind('<Return>', lambda e: on_ok())

    btn_frame = tk.Frame(dialog)
    btn_frame.pack(pady=15)
    ttk.Button(btn_frame, text=tr("dlg_cancel"), command=on_cancel, width=10).pack(side="left", padx=5)
    ttk.Button(btn_frame, text=tr("dlg_apply"), command=on_ok, style="Emis.Primary.TButton").pack(side="left", padx=5)

    dialog.update_idletasks()
    x = root.winfo_rootx() + (root.winfo_width() - dialog.winfo_width()) // 2
    y = root.winfo_rooty() + (root.winfo_height() - dialog.winfo_height()) // 2
    dialog.geometry(f"+{x}+{y}")


def _show_confirm_dialog(title, message):
    """Показывает подтверждение в стиле ЭМИС."""
    confirmed = False
    win = tk.Toplevel(root, background=emis_background)
    win.withdraw()
    win.title(title)
    win.transient(root)
    win.resizable(False, False)

    card = ttk.Frame(win, style="Emis.Card.TFrame", padding=(18, 14))
    card.pack(padx=12, pady=12, fill="both", expand=True)
    ttk.Label(card, text=title, style="Emis.Heading.TLabel").pack(anchor="w")
    ttk.Label(card, text=message, justify="left", wraplength=360).pack(anchor="w", pady=(8, 12))
    buttons = ttk.Frame(card)
    buttons.pack(anchor="e")

    def accept():
        nonlocal confirmed
        confirmed = True
        win.destroy()

    ttk.Button(buttons, text=tr("dlg_yes"), command=accept, style="Emis.Primary.TButton").pack(side="left", padx=(0, 8))
    cancel = ttk.Button(buttons, text=tr("dlg_no"), command=win.destroy)
    cancel.pack(side="left")
    win.bind("<Escape>", lambda _event: win.destroy())

    win.update_idletasks()
    x = root.winfo_rootx() + (root.winfo_width() - win.winfo_reqwidth()) // 2
    y = root.winfo_rooty() + (root.winfo_height() - win.winfo_reqheight()) // 2
    win.geometry(f"{x:+d}{y:+d}")
    win.deiconify()
    win.wait_visibility()
    win.grab_set()
    cancel.focus_set()
    root.wait_window(win)
    return confirmed


def _on_change_max_current_a():
    global settings_dialog_open
    if not conn:
        _show_emis_notice(tr("dlg_warning"), tr("dlg_no_connection"), wait=True)
        return
    if settings_dialog_open: return
    settings_dialog_open = True
    stop_time_reader()
    time.sleep(0.3)

    current_text = settings_max_i_a_label.cget("text")
    try: current_val = float(current_text.replace(" " + tr("unit_a"), "").replace(",", "."))
    except: current_val = 0

    dialog = tk.Toplevel(root)
    dialog.title(tr("dlg_max_current_a"))
    dialog.grab_set()
    dialog.resizable(False, False)

    # Единая функция очистки (срабатывает при любом закрытии)
    def cleanup_and_close():
        global settings_dialog_open
        settings_dialog_open = False
        start_time_reader()
        if dialog.winfo_exists(): dialog.destroy()

    dialog.protocol("WM_DELETE_WINDOW", cleanup_and_close)

    tk.Label(dialog, text=tr("dlg_max_current_a_prompt"), font=("Segoe UI", 10)).pack(pady=(15, 5), padx=20)
    value_var = tk.StringVar(value=f"{current_val:.0f}")
    entry = tk.Entry(dialog, textvariable=value_var, font=("Consolas", 12), width=15, **_numeric_input(dialog, integer=True))
    entry.pack(pady=5); entry.focus(); entry.select_range(0, 'end')

    def on_ok():
        raw_value = value_var.get().strip()
        if not raw_value or any(char not in "0123456789" for char in raw_value):
            messagebox.showerror(
                tr("dlg_input_error"), tr("dlg_invalid_number"), parent=dialog
            )
            entry.focus_set()
            return

        try:
            new_value = int(raw_value)
            _stop_measurement()
            success, msg = write_max_current(conn["port"], conn["slave"], conn["baud"], conn["parity"], 'a', new_value)
            if success:
                _, new_settings = read_device_settings_params(conn["port"], conn["slave"], conn["baud"], conn["parity"], device_type)
                settings_update_queue.put(new_settings)
                root.after(0, _check_settings_queue)
                _show_emis_notice(tr("dlg_write_success"), tr("dlg_value_written"), parent=dialog, wait=True)
            else:
                messagebox.showerror(tr("dlg_write_error"), msg, parent=dialog)
        except Exception as e:
            messagebox.showerror(tr("dlg_input_error"), str(e), parent=dialog)
        finally:
            cleanup_and_close()

    def on_cancel(): cleanup_and_close()

    entry.bind('<Return>', lambda e: on_ok())
    btn_frame = tk.Frame(dialog); btn_frame.pack(pady=15)
    ttk.Button(btn_frame, text=tr("dlg_cancel"), command=on_cancel, width=10).pack(side="left", padx=5)
    ttk.Button(btn_frame, text=tr("dlg_apply"), command=on_ok, style="Emis.Primary.TButton").pack(side="left", padx=5)
    dialog.update_idletasks()
    dialog.geometry(f"+{root.winfo_rootx() + (root.winfo_width() - dialog.winfo_width()) // 2}+{root.winfo_rooty() + (root.winfo_height() - dialog.winfo_height()) // 2}")


def _on_change_max_current_b():
    global settings_dialog_open
    if device_type != "dual":
        return
    if not conn:
        _show_emis_notice(tr("dlg_warning"), tr("dlg_no_connection"), wait=True)
        return
    if settings_dialog_open:
        return
    settings_dialog_open = True

    stop_time_reader()
    time.sleep(0.3)

    current_text = settings_max_i_b_label.cget("text")
    try: current_val = float(current_text.replace(" " + tr("unit_a"), "").replace(",", "."))
    except: current_val = 0

    dialog = tk.Toplevel(root)
    dialog.title(tr("dlg_max_current_b"))
    dialog.grab_set()
    dialog.resizable(False, False)

    # Единая функция очистки (срабатывает при закрытии любым способом)
    def cleanup_and_close():
        global settings_dialog_open
        settings_dialog_open = False
        start_time_reader()
        if dialog.winfo_exists():
            dialog.destroy()

    # Перехват нажатия на крестик
    dialog.protocol("WM_DELETE_WINDOW", cleanup_and_close)

    tk.Label(dialog, text=tr("dlg_max_current_b_prompt"), font=("Segoe UI", 10)).pack(pady=(15, 5), padx=20)
    value_var = tk.StringVar(value=f"{current_val:.0f}")
    entry = tk.Entry(dialog, textvariable=value_var, font=("Consolas", 12), width=15, **_numeric_input(dialog, integer=True))
    entry.pack(pady=5)
    entry.focus()
    entry.select_range(0, 'end')

    def on_ok():
        raw_value = value_var.get().strip()
        if not raw_value or any(char not in "0123456789" for char in raw_value):
            messagebox.showerror(
                tr("dlg_input_error"), tr("dlg_invalid_number"), parent=dialog
            )
            entry.focus_set()
            return

        try:
            new_value = int(raw_value)
            _stop_measurement()
            success, msg = write_max_current(conn["port"], conn["slave"], conn["baud"], conn["parity"], 'b', new_value)
            if success:
                _, new_settings = read_device_settings_params(conn["port"], conn["slave"], conn["baud"], conn["parity"], device_type)
                settings_update_queue.put(new_settings)
                root.after(0, _check_settings_queue)
                _show_emis_notice(tr("dlg_write_success"), tr("dlg_value_written"), parent=dialog, wait=True)
            else:
                messagebox.showerror(tr("dlg_write_error"), msg, parent=dialog)
        except Exception as e:
            messagebox.showerror(tr("dlg_input_error"), str(e), parent=dialog)
        finally:
            cleanup_and_close()

    def on_cancel():
        cleanup_and_close()

    entry.bind('<Return>', lambda e: on_ok())

    btn_frame = tk.Frame(dialog)
    btn_frame.pack(pady=15)
    ttk.Button(btn_frame, text=tr("dlg_cancel"), command=on_cancel, width=10).pack(side="left", padx=5)
    ttk.Button(btn_frame, text=tr("dlg_apply"), command=on_ok, style="Emis.Primary.TButton").pack(side="left", padx=5)

    dialog.update_idletasks()
    x = root.winfo_rootx() + (root.winfo_width() - dialog.winfo_width()) // 2
    y = root.winfo_rooty() + (root.winfo_height() - dialog.winfo_height()) // 2
    dialog.geometry(f"+{x}+{y}")


def _on_change_sens_voltage():
    global settings_dialog_open
    if not conn:
        _show_emis_notice(tr("dlg_warning"), tr("dlg_no_connection"), wait=True)
        return
    if settings_dialog_open:
        return
    settings_dialog_open = True

    stop_time_reader()
    time.sleep(0.3)

    current_text = settings_sens_v_label.cget("text")
    try: current_val = float(current_text.replace(" " + tr("unit_percent"), "").replace(",", "."))
    except: current_val = 0

    dialog = tk.Toplevel(root)
    dialog.title(tr("dlg_sens_voltage"))
    dialog.grab_set()
    dialog.resizable(False, False)

    # Единая функция очистки
    def cleanup_and_close():
        global settings_dialog_open
        settings_dialog_open = False
        start_time_reader()
        if dialog.winfo_exists():
            dialog.destroy()

    dialog.protocol("WM_DELETE_WINDOW", cleanup_and_close)

    tk.Label(dialog, text=tr("dlg_sens_voltage_prompt"), font=("Segoe UI", 10)).pack(pady=(15, 5), padx=20)
    value_var = tk.StringVar(value=f"{current_val:.2f}")
    entry = tk.Entry(dialog, textvariable=value_var, font=("Consolas", 12), width=15, **_numeric_input(dialog, integer=False))
    entry.pack(pady=5)
    entry.focus()
    entry.select_range(0, 'end')

    def on_ok():
        try:
            new_value = float(value_var.get().replace(',', '.'))
            _stop_measurement()
            success, msg = write_sensitivity_voltage(conn["port"], conn["slave"], conn["baud"], conn["parity"], new_value)
            if success:
                _, new_settings = read_device_settings_params(conn["port"], conn["slave"], conn["baud"], conn["parity"], device_type)
                settings_update_queue.put(new_settings)
                root.after(0, _check_settings_queue)
                _show_emis_notice(tr("dlg_write_success"), tr("dlg_value_written"), parent=dialog, wait=True)
            else:
                messagebox.showerror(tr("dlg_write_error"), msg, parent=dialog)
        except Exception as e:
            messagebox.showerror(tr("dlg_input_error"), str(e), parent=dialog)
        finally:
            cleanup_and_close()

    def on_cancel():
        cleanup_and_close()

    entry.bind('<Return>', lambda e: on_ok())

    btn_frame = tk.Frame(dialog)
    btn_frame.pack(pady=15)
    ttk.Button(btn_frame, text=tr("dlg_cancel"), command=on_cancel, width=10).pack(side="left", padx=5)
    ttk.Button(btn_frame, text=tr("dlg_apply"), command=on_ok, style="Emis.Primary.TButton").pack(side="left", padx=5)

    dialog.update_idletasks()
    x = root.winfo_rootx() + (root.winfo_width() - dialog.winfo_width()) // 2
    y = root.winfo_rooty() + (root.winfo_height() - dialog.winfo_height()) // 2
    dialog.geometry(f"+{x}+{y}")


def _on_change_sens_current():
    global settings_dialog_open
    if not conn:
        _show_emis_notice(tr("dlg_warning"), tr("dlg_no_connection"), wait=True)
        return
    if settings_dialog_open:
        return
    settings_dialog_open = True

    stop_time_reader()
    time.sleep(0.3)

    current_text = settings_sens_i_label.cget("text")
    try: current_val = float(current_text.replace(" " + tr("unit_percent"), "").replace(",", "."))
    except: current_val = 0

    dialog = tk.Toplevel(root)
    dialog.title(tr("dlg_sens_current"))
    dialog.grab_set()
    dialog.resizable(False, False)

    # Единая функция очистки
    def cleanup_and_close():
        global settings_dialog_open
        settings_dialog_open = False
        start_time_reader()
        if dialog.winfo_exists():
            dialog.destroy()

    dialog.protocol("WM_DELETE_WINDOW", cleanup_and_close)

    tk.Label(dialog, text=tr("dlg_sens_current_prompt"), font=("Segoe UI", 10)).pack(pady=(15, 5), padx=20)
    value_var = tk.StringVar(value=f"{current_val:.2f}")
    entry = tk.Entry(dialog, textvariable=value_var, font=("Consolas", 12), width=15, **_numeric_input(dialog, integer=False))
    entry.pack(pady=5)
    entry.focus()
    entry.select_range(0, 'end')

    def on_ok():
        try:
            new_value = float(value_var.get().replace(',', '.'))
            _stop_measurement()
            success, msg = write_sensitivity_current(conn["port"], conn["slave"], conn["baud"], conn["parity"], new_value)
            if success:
                _, new_settings = read_device_settings_params(conn["port"], conn["slave"], conn["baud"], conn["parity"], device_type)
                settings_update_queue.put(new_settings)
                root.after(0, _check_settings_queue)
                _show_emis_notice(tr("dlg_write_success"), tr("dlg_value_written"), parent=dialog, wait=True)
            else:
                messagebox.showerror(tr("dlg_write_error"), msg, parent=dialog)
        except Exception as e:
            messagebox.showerror(tr("dlg_input_error"), str(e), parent=dialog)
        finally:
            cleanup_and_close()

    def on_cancel():
        cleanup_and_close()

    entry.bind('<Return>', lambda e: on_ok())

    btn_frame = tk.Frame(dialog)
    btn_frame.pack(pady=15)
    ttk.Button(btn_frame, text=tr("dlg_cancel"), command=on_cancel, width=10).pack(side="left", padx=5)
    ttk.Button(btn_frame, text=tr("dlg_apply"), command=on_ok, style="Emis.Primary.TButton").pack(side="left", padx=5)

    dialog.update_idletasks()
    x = root.winfo_rootx() + (root.winfo_width() - dialog.winfo_width()) // 2
    y = root.winfo_rooty() + (root.winfo_height() - dialog.winfo_height()) // 2
    dialog.geometry(f"+{x}+{y}")


def _on_change_device_info(field, label_key, value_label):
    """Открывает окно изменения информационного поля."""
    global settings_dialog_open

    if settings_dialog_open or operation_in_progress:
        return

    if not conn:
        _show_emis_notice(tr("dlg_warning"), tr("dlg_no_connection"), wait=True)
        return

    settings_dialog_open = True

    win = tk.Toplevel(root)
    win.title(tr("btn_change") + " — " + tr(label_key).rstrip(":："))
    win.transient(root)
    win.resizable(False, False)
    win.grab_set()

    prompt_key = (
        "info_serial_prompt"
        if field == "serial_number"
        else "info_ascii_prompt"
    )

    tk.Label(
        win,
        text=tr(prompt_key),
        wraplength=400,
        justify="left",
    ).pack(padx=20, pady=(15, 8))

    entry = ttk.Entry(win, width=38, font=("Consolas", 11))
    entry.pack(padx=20, pady=5)

    current_value = value_label.cget("text")
    if current_value != tr("status_disconnected"):
        entry.insert(0, current_value)

    def close_dialog():
        global settings_dialog_open

        if operation_in_progress:
            return

        settings_dialog_open = False
        win.destroy()

    def set_busy(busy):
        state = "disabled" if busy else "normal"
        for widget in (entry, apply_button, cancel_button):
            widget.configure(state=state)

    def show_error(message):
        set_busy(False)
        messagebox.showerror(
            tr("dlg_input_error"),
            message,
            parent=win,
        )
        entry.focus_set()

    def on_apply():
        if operation_in_progress:
            return

        value = entry.get().strip()

        if field == "serial_number":
            valid, result = validate_meter_serial_number(value)
            if not valid:
                show_error(tr("info_serial_prompt"))
                return
            value = result
        else:
            max_length = DEVICE_INFO_REGISTER_COUNT * 2
            if (
                not value
                or len(value) > max_length
                or any(not 32 <= ord(char) <= 126 for char in value)
            ):
                show_error(tr("info_ascii_prompt"))
                return

        set_busy(True)

        started = _write_device_info_async(
            field,
            value,
            on_success=close_dialog,
            on_error=show_error,
        )
        if not started:
            set_busy(False)

    buttons = tk.Frame(win)
    buttons.pack(pady=(10, 15))

    cancel_button = ttk.Button(
        buttons, text=tr("dlg_cancel"), command=close_dialog,
    )
    cancel_button.pack(side="left", padx=5)

    apply_button = ttk.Button(
        buttons, text=tr("dlg_apply"), command=on_apply, style="Emis.Primary.TButton",
    )
    apply_button.pack(side="left", padx=5)

    win.protocol("WM_DELETE_WINDOW", close_dialog)
    win.bind("<Return>", lambda event: on_apply())
    win.bind("<Escape>", lambda event: close_dialog())

    win.update_idletasks()
    x = root.winfo_rootx() + (root.winfo_width() - win.winfo_width()) // 2
    y = root.winfo_rooty() + (root.winfo_height() - win.winfo_height()) // 2
    win.geometry(f"+{x}+{y}")

    entry.focus_set()
    entry.selection_range(0, tk.END)


def _show_device_info_autofill_dialog():
    """Открывает окно сканирования номера для автозаполнения."""
    global settings_dialog_open

    if settings_dialog_open or operation_in_progress:
        return

    if not conn:
        _show_emis_notice(tr("dlg_warning"), tr("dlg_no_connection"), wait=True)
        return

    settings_dialog_open = True

    win = tk.Toplevel(root)
    win.title(tr("btn_info_autofill"))
    win.transient(root)
    win.resizable(False, False)
    win.grab_set()

    tk.Label(
        win,
        text=tr("info_autofill_prompt"),
        wraplength=440,
        justify="left",
    ).pack(padx=20, pady=(15, 10))

    entry = ttk.Entry(win, width=28, font=("Consolas", 13))
    entry.pack(padx=20, pady=5)

    status_label = tk.Label(win, text="")
    status_label.pack(padx=20, pady=5)

    def close_dialog():
        global settings_dialog_open

        if operation_in_progress:
            return

        settings_dialog_open = False
        win.destroy()

    def set_busy(busy):
        state = "disabled" if busy else "normal"
        for widget in (entry, apply_button, cancel_button):
            widget.configure(state=state)

        status_label.configure(
            text=tr("info_autofill_busy") if busy else ""
        )

    def show_error(message, title_key="dlg_write_error"):
        set_busy(False)
        messagebox.showerror(tr(title_key), message, parent=win)
        entry.focus_set()
        entry.selection_range(0, tk.END)

    def on_apply():
        if operation_in_progress:
            return

        valid, result = validate_scanned_serial_number(entry.get())
        if not valid:
            show_error(
                tr("info_autofill_invalid"),
                "dlg_input_error",
            )
            return

        # Фиксируем момент принятия корректного номера.
        scanned_at = datetime.datetime.now()
        set_busy(True)

        started = _autofill_device_info_async(
            result,
            scanned_at,
            on_success=close_dialog,
            on_error=show_error,
        )
        if not started:
            set_busy(False)

    buttons = tk.Frame(win)
    buttons.pack(pady=(5, 15))

    cancel_button = ttk.Button(
        buttons,
        text=tr("dlg_cancel"),
        command=close_dialog,
    )
    cancel_button.pack(side="left", padx=5)

    apply_button = ttk.Button(
        buttons,
        text=tr("dlg_apply"),
        command=on_apply,
        style="Emis.Primary.TButton",
    )
    apply_button.pack(side="left", padx=5)

    win.protocol("WM_DELETE_WINDOW", close_dialog)
    win.bind("<Return>", lambda event: on_apply())
    win.bind("<Escape>", lambda event: close_dialog())

    win.update_idletasks()
    x = root.winfo_rootx() + (root.winfo_width() - win.winfo_width()) // 2
    y = root.winfo_rooty() + (root.winfo_height() - win.winfo_height()) // 2
    win.geometry(f"+{x}+{y}")

    entry.focus_set()


def _autofill_device_info_async(
    serial_number, scanned_at, on_success, on_error
):
    """Выполняет автозаполнение без блокировки интерфейса."""
    global operation_in_progress

    if operation_in_progress:
        return False

    if not conn:
        on_error(tr("dlg_no_connection"))
        return False

    connection = conn.copy()
    selected_type = device_type
    operation_in_progress = True

    def finish(success, message, info, stopped):
        global operation_in_progress

        operation_in_progress = False

        if conn == connection and device_type == selected_type:
            if info is not None:
                info_update_queue.put(info)
            if stopped:
                start_time_reader()

        if success:
            on_success()
        else:
            on_error(message)

    def worker():
        stopped = False
        success = False
        message = ""
        info = None

        try:
            stopped = stop_time_reader()
            if not stopped:
                raise RuntimeError(
                    "Не удалось остановить опрос. Заполнение отменено. "
                    "Переподключитесь к прибору."
                )

            if conn != connection or device_type != selected_type:
                raise RuntimeError("Подключение к прибору изменилось.")

            success, result = autofill_device_info(
                connection["port"],
                connection["slave"],
                connection["baud"],
                connection["parity"],
                serial_number,
                scanned_at,
            )

            if success:
                info = result
            else:
                message = str(result)

        except Exception as error:
            success = False
            message = str(error)

        finally:
            root.after(0, finish, success, message, info, stopped)

    threading.Thread(target=worker, daemon=True).start()
    return True


def _write_device_info_async(field, value, on_success, on_error):
    """Записывает информационное поле в фоновом потоке."""
    global operation_in_progress

    if operation_in_progress:
        return False

    if not conn:
        on_error(tr("dlg_no_connection"))
        return False

    connection = conn.copy()
    selected_type = device_type
    operation_in_progress = True

    def finish(success, message, info, stopped):
        """Возвращает результат в основной поток интерфейса."""
        global operation_in_progress

        operation_in_progress = False

        if conn == connection and device_type == selected_type:
            if info is not None:
                info_update_queue.put(info)
            if stopped:
                start_time_reader()

        if success:
            on_success()
        else:
            on_error(message)

    def worker():
        stopped = False
        success = False
        message = ""
        info = None

        try:
            stopped = stop_time_reader()
            if not stopped:
                raise RuntimeError(
                    "Не удалось остановить опрос. Запись отменена. "
                    "Переподключитесь к прибору."
                )

            if conn != connection or device_type != selected_type:
                raise RuntimeError("Подключение к прибору изменилось.")

            success, message = write_device_info_field(
                connection["port"],
                connection["slave"],
                connection["baud"],
                connection["parity"],
                field,
                value,
            )

            if success:
                read_ok, read_result = read_device_info(
                    connection["port"],
                    connection["slave"],
                    connection["baud"],
                    connection["parity"],
                )

                if read_ok:
                    info = read_result
                else:
                    success = False
                    message = (
                        "Запись проверена, но обновить информацию "
                        "о приборе не удалось: " + str(read_result)
                    )

        except Exception as error:
            success = False
            message = str(error)

        finally:
            root.after(0, finish, success, message, info, stopped)

    threading.Thread(target=worker, daemon=True).start()
    return True


def _on_change_pulse_constant(channel):
    """Записывает выбранное значение без блокировки интерфейса."""
    global settings_dialog_open, operation_in_progress

    if settings_dialog_open or operation_in_progress:
        return

    if not conn:
        _show_emis_notice(tr("dlg_warning"), tr("dlg_no_connection"), wait=True)
        return

    if channel == "b" and device_type != "dual":
        return

    combo = settings_pulse_combos.get(channel)
    if combo is None:
        return

    try:
        value = int(combo.get())
    except ValueError:
        return

    connection = conn.copy()
    selected_type = device_type
    settings_dialog_open = True
    operation_in_progress = True

    for field in settings_pulse_combos.values():
        field.configure(state="disabled")

    def finish(success, message, settings, stopped):
        """Обновляет интерфейс в основном потоке."""
        global settings_dialog_open, operation_in_progress

        settings_dialog_open = False
        operation_in_progress = False

        # Убираем выбранное значение до подтверждения чтением.
        for field in settings_pulse_combos.values():
            field.set("")
            field.configure(state="disabled")

        if conn == connection and device_type == selected_type:
            if settings is not None:
                settings_update_queue.put(settings)
            if stopped:
                start_time_reader()

        if not success:
            messagebox.showerror(tr("dlg_write_error"), message)

    def worker():
        """Останавливает опрос, записывает и перечитывает настройки."""
        stopped = False
        success = False
        message = ""
        settings = None

        try:
            stopped = stop_time_reader()
            if not stopped:
                raise RuntimeError(
                    "Не удалось остановить опрос. Запись отменена. "
                    "Переподключитесь к прибору."
                )

            if conn != connection or device_type != selected_type:
                raise RuntimeError("Подключение к прибору изменилось.")

            success, message = write_pulse_constant(
                connection["port"],
                connection["slave"],
                connection["baud"],
                connection["parity"],
                channel,
                value,
            )

            read_ok, read_result = read_device_settings_params(
                connection["port"],
                connection["slave"],
                connection["baud"],
                connection["parity"],
                selected_type,
            )

            if read_ok:
                settings = read_result
            elif success:
                success = False
                message = (
                    "Запись проверена, но обновить настройки не удалось: "
                    + str(read_result)
                )

        except Exception as error:
            success = False
            message = str(error)

        finally:
            root.after(0, finish, success, message, settings, stopped)

    threading.Thread(target=worker, daemon=True).start()


def _on_change_decimal_places(event=None):
    global settings_dialog_open
    previous_places = (latest_verification_settings or {}).get("decimal_places")
    previous_selection = (
        str(previous_places) if previous_places in ENERGY_DECIMAL_PLACES else ""
    )
    if not conn:
        _show_emis_notice(tr("dlg_warning"), tr("dlg_no_connection"), wait=True)
        settings_decimal_combo.set(previous_selection)
        return
    if settings_dialog_open:
        return
    settings_dialog_open = True

    # Останавливаем поток перед записью
    stop_time_reader()
    time.sleep(0.3)

    try:
        value = int(settings_decimal_combo.get())
        success, msg = write_decimal_places(conn["port"], conn["slave"], conn["baud"], conn["parity"], value)
        if success:
            _, new_settings = read_device_settings_params(conn["port"], conn["slave"], conn["baud"], conn["parity"], device_type)
            settings_update_queue.put(new_settings)
            root.after(0, _check_settings_queue)
        else:
            messagebox.showerror(tr("dlg_write_error"), msg)
            settings_decimal_combo.set(previous_selection) # Сброс при ошибке
    except Exception as e:
        messagebox.showerror(tr("dlg_input_error"), str(e))
        settings_decimal_combo.set(previous_selection)
    finally:
        settings_dialog_open = False
        start_time_reader() # Запускаем поток обратно


def show_tariff_schedule_dialog():
    """Открывает редактор тарифного расписания счётчика."""
    global settings_dialog_open

    if not conn:
        _show_emis_notice(tr("dlg_warning"), tr("dlg_no_connection"), wait=True)
        return

    if settings_dialog_open:
        return

    settings_dialog_open = True
    stop_time_reader()

    try:
        root.config(cursor="watch")
        root.update_idletasks()
        time.sleep(0.3)

        success, result = read_tariff_schedule(
            conn["port"],
            conn["slave"],
            conn["baud"],
            conn["parity"],
        )
    finally:
        root.config(cursor="")

    if not success:
        settings_dialog_open = False
        start_time_reader()

        messagebox.showerror(
            tr("dlg_write_error"),
            result,
        )
        return

    # Для полностью пустого расписания показываем один начальный период.
    periods = result or [(0, 0, 1)]

    dialog = tk.Toplevel(root)
    dialog.title(tr("dlg_tariff_schedule"))
    dialog.resizable(False, False)
    dialog.grab_set()

    def cleanup_and_close():
        """Закрывает окно и возобновляет фоновое чтение прибора."""
        global settings_dialog_open

        settings_dialog_open = False
        start_time_reader()

        if dialog.winfo_exists():
            dialog.destroy()

    dialog.protocol("WM_DELETE_WINDOW", cleanup_and_close)

    ttk.Label(
        dialog,
        text=tr("dlg_tariff_schedule"),
        style="Emis.Heading.TLabel",
    ).pack(
        pady=(15, 10),
        padx=20,
    )

    hint_frame = ttk.Frame(dialog)
    hint_frame.pack(anchor="w", padx=20, pady=(0, 8))
    hint_font = ("TkDefaultFont", 9)
    ttk.Label(
        hint_frame, text=tr("lbl_schedule_important"), font=(*hint_font, "bold"), foreground="#00664D",
    ).pack(side="left", anchor="n", padx=(0, 6))
    schedule_hint = ttk.Label(hint_frame, font=hint_font, wraplength=260, justify="left")
    schedule_hint.pack(side="left", anchor="n")

    table_frame = tk.Frame(dialog)
    table_frame.pack(
        padx=20,
        pady=(0, 10),
    )

    # Здесь храним поля строк, чтобы затем получить введённые значения.
    period_rows = []
    validate_digits = dialog.register(
        lambda value: len(value) <= 2 and all(char in "0123456789" for char in value)
    )

    def get_row_values():
        """Возвращает текущие значения всех строк редактора."""
        return [
            (
                f"{hour_entry.get()}:{minute_entry.get()}",
                tariff_combo.get(),
            )
            for hour_entry, minute_entry, tariff_combo, _, _ in period_rows
        ]

    def redraw_rows(row_values):
        """Перерисовывает строки таблицы после добавления или удаления."""
        nonlocal period_rows

        for widget in table_frame.winfo_children():
            widget.destroy()

        period_rows = []

        tk.Label(
            table_frame,
            text="№",
            width=4,
            anchor="center",
        ).grid(
            row=0,
            column=0,
            padx=5,
            pady=(0, 5),
        )

        tk.Label(
            table_frame,
            text=tr("lbl_tariff_start_time"),
            width=14,
            anchor="center",
        ).grid(
            row=0,
            column=1,
            padx=5,
            pady=(0, 5),
        )

        tk.Label(
            table_frame,
            text=tr("lbl_tariff_number"),
            width=10,
            anchor="center",
        ).grid(
            row=0,
            column=2,
            padx=5,
            pady=(0, 5),
        )

        for index, (time_value, tariff_value) in enumerate(
            row_values,
            start=1,
        ):
            tk.Label(
                table_frame,
                text=str(index),
                width=4,
                anchor="center",
            ).grid(
                row=index,
                column=0,
                padx=5,
                pady=3,
            )

            time_frame = ttk.Frame(table_frame)
            time_frame.grid(row=index, column=1, padx=5, pady=3)
            hour, minute = time_value.split(":")
            hour_var = tk.StringVar(master=dialog, value=hour)
            minute_var = tk.StringVar(master=dialog, value=minute)
            hour_entry = ttk.Entry(time_frame, width=3, justify="center", textvariable=hour_var)
            minute_entry = ttk.Entry(time_frame, width=3, justify="center", textvariable=minute_var)
            for entry in (hour_entry, minute_entry):
                entry.configure(validate="key", validatecommand=(validate_digits, "%P"))
            hour_entry.pack(side="left")
            ttk.Label(time_frame, text=":").pack(side="left", padx=2)
            minute_entry.pack(side="left")

            tariff_combo = ttk.Combobox(
                table_frame,
                values=["1", "2", "3", "4"],
                state="readonly",
                width=8,
                justify="center",
            )
            tariff_combo.set(tariff_value)
            tariff_combo.grid(
                row=index,
                column=2,
                padx=5,
                pady=3,
            )

            ttk.Button(
                table_frame,
                text=tr("btn_remove_period"),
                command=lambda row_index=index - 1: remove_row(
                    row_index,
                ),
                width=10,
            ).grid(
                row=index,
                column=3,
                padx=(5, 0),
                pady=3,
            )

            period_rows.append(
                (
                    hour_entry,
                    minute_entry,
                    tariff_combo,
                    hour_var,
                    minute_var,
                )
            )
            hour_var.trace_add("write", refresh_schedule_validation)
            minute_var.trace_add("write", refresh_schedule_validation)

        refresh_schedule_validation()

    def add_row():
        """Добавляет пустой тарифный период в конец таблицы."""
        row_values = get_row_values()

        if len(row_values) >= 14:
            _show_emis_notice(
                tr("dlg_warning"),
                tr("err_schedule_limit"),
                parent=dialog, wait=True,
            )
            dialog.grab_set()
            return

        row_values.append(("00:00", "1"))
        redraw_rows(row_values)

    def remove_row(row_index):
        """Удаляет выбранный тарифный период."""
        row_values = get_row_values()

        if len(row_values) <= 1:
            return

        del row_values[row_index]
        redraw_rows(row_values)

    def get_periods_to_write():
        """Преобразует поля окна в периоды для записи в прибор."""
        row_values = get_row_values()

        if not row_values:
            raise ValueError(tr("err_schedule_empty"))

        parsed_periods = []
        previous_minutes = -1

        for index, (time_value, tariff_value) in enumerate(
            row_values,
            start=1,
        ):
            time_parts = time_value.split(":")

            if len(time_parts) != 2:
                raise ValueError(
                    tr("err_schedule_time").format(row=index)
                )

            try:
                hour = int(time_parts[0])
                minute = int(time_parts[1])
            except ValueError as error:
                raise ValueError(
                    tr("err_schedule_time").format(row=index)
                ) from error

            if not 0 <= hour <= 23 or not 0 <= minute <= 59:
                raise ValueError(
                    tr("err_schedule_time").format(row=index)
                )

            start_minutes = hour * 60 + minute
            if start_minutes <= previous_minutes:
                previous = f"{previous_minutes // 60:02d}:{previous_minutes % 60:02d}"
                raise ValueError(tr("err_schedule_order").format(row=index, previous=previous))
            previous_minutes = start_minutes

            parsed_periods.append(
                (
                    hour,
                    minute,
                    int(tariff_value),
                )
            )

        return parsed_periods

    def refresh_schedule_validation(*_args):
        try:
            periods_to_write = get_periods_to_write()
        except ValueError as error:
            schedule_hint.config(text=str(error), foreground="#9C2929")
            save_button.config(state="disabled")
            return None

        schedule_hint.config(text=tr("hint_schedule_order"), foreground="#437467")
        save_button.config(state="normal")
        return periods_to_write

    def save_schedule():
        """Проверяет и записывает тарифное расписание в счётчик."""
        periods_to_write = refresh_schedule_validation()
        if periods_to_write is None:
            return

        try:
            root.config(cursor="watch")
            root.update_idletasks()

            success, result = write_tariff_schedule(
                conn["port"],
                conn["slave"],
                conn["baud"],
                conn["parity"],
                periods_to_write,
            )
        finally:
            root.config(cursor="")

        if not success:
            messagebox.showerror(
                tr("dlg_write_error"),
                result,
                parent=dialog,
            )
            return

        _show_emis_notice(
            tr("dlg_write_success"),
            tr("dlg_schedule_saved"),
            parent=dialog, wait=True,
        )

        cleanup_and_close()

    initial_rows = [
        (
            f"{hour:02d}:{minute:02d}",
            str(tariff_number),
        )
        for hour, minute, tariff_number in periods
    ]

    ttk.Button(
        dialog,
        text=tr("btn_add_period"),
        command=add_row,
        width=18,
    ).pack(
        pady=(0, 5),
    )

    button_frame = tk.Frame(dialog)
    button_frame.pack(
        pady=(5, 15),
    )

    ttk.Button(
        button_frame,
        text=tr("dlg_cancel"),
        command=cleanup_and_close,
        width=14,
    ).pack(
        side="left",
        padx=5,
    )

    save_button = ttk.Button(
        button_frame,
        text=tr("btn_save_schedule"),
        command=save_schedule,
        style="Emis.Primary.TButton",
    )
    save_button.pack(side="left", padx=5)

    redraw_rows(initial_rows)
    dialog.update_idletasks()

    x = root.winfo_rootx() + (
        root.winfo_width() - dialog.winfo_width()
    ) // 2
    y = root.winfo_rooty() + (
        root.winfo_height() - dialog.winfo_height()
    ) // 2

    dialog.geometry(f"+{x}+{y}")


def update_device_type_display():
    global type_image_label
    device_name = tr("device_name")  # "СКВТ ЭМИС-ЭЛЕКТРА 977"

    # Если тип ещё не выбран — показываем прочерк
    if device_type is None:
        type_text = tr("status_disconnected")
        img = None
    elif device_type == "single":
        type_text = f"{device_name}\n{tr('device_single')}"
        img = DEVICE_IMAGES.get("single")
    elif device_type == "dual":
        type_text = f"{device_name}\n{tr('device_dual')}"
        img = DEVICE_IMAGES.get("dual")
    else:
        type_text = tr("status_disconnected")
        img = None

    type_label.config(text=type_text)

    if img:
        type_image_label.config(image=img)
    else:
        type_image_label.config(image="")


def resize_window_to_content():
    """Автоматически подстраивает размер окна под контент после смены языка."""
    root.update_idletasks()

    # Получаем требуемый размер контента
    required_width = root.winfo_reqwidth()
    required_height = root.winfo_reqheight()

    # Ограничиваем высоту 90% экрана, ширина — по контенту
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    max_height = int(screen_height * 0.9)
    actual_height = min(required_height, max_height)

    # Центрируем окно на экране
    x = (screen_width - required_width) // 2
    y = (screen_height - actual_height) // 2

    # Применяем новый размер
    root.geometry(f"{required_width}x{actual_height}+{x}+{y}")
    root.resizable(True, True)


# =============================================================================
# 6. Создание графического интерфейса
# =============================================================================

# Загружаем сохраненный язык
load_config()

root = tk.Tk()
_set_app_title()
# ICO содержит отдельные изображения для разных размеров Windows.
try:
    app_icon_path = resource_path("app.ico")

    # Значок главного окна.
    root.iconbitmap(app_icon_path)

    # Значок будущих дочерних окон.
    root.iconbitmap(default=app_icon_path)

except tk.TclError:
    # Запасной вариант, если система не поддерживает ICO.
    try:
        app_icon_img = tk.PhotoImage(file=resource_path("app.png"))
        root.iconphoto(True, app_icon_img)
    except tk.TclError:
        pass
# Shared palette for the main window, tabs and dialogs.
emis_background = "#F1F4F3"
emis_surface = "#FFFFFF"
emis_text = "#24332F"
emis_green = "#009975"
root.configure(background=emis_background)
root.option_add("*Background", emis_surface)
root.option_add("*Foreground", emis_text)
emis_style = ttk.Style(root)
emis_style.theme_use("clam")


def _without_focus_outline(layout):
    """Keep widget contents while removing the theme's dotted focus element."""
    result = []
    for element, options in layout:
        options = dict(options)
        children = _without_focus_outline(options.get("children", []))
        if element.rsplit(".", 1)[-1] == "focus":
            result.extend(children)
        else:
            if "children" in options:
                options["children"] = children
            result.append((element, options))
    return result


for widget_style in ("TButton", "TNotebook.Tab", "TCombobox", "TMenubutton", "Treeview.Item"):
    layout = _without_focus_outline(emis_style.layout(widget_style))
    emis_style.layout(widget_style, layout)

# Native Tk buttons use their highlight ring instead of a ttk layout element.
root.option_add("*Button.highlightThickness", 0)
emis_style.map("TCombobox", bordercolor=[("focus", "#009975")])

emis_style.configure(".", background=emis_surface, foreground=emis_text)
emis_style.configure("TNotebook", background=emis_background, borderwidth=0)
emis_style.configure("TNotebook.Tab", padding=(12, 8), background=emis_background)
emis_style.map("TNotebook.Tab", background=[("selected", "#DDF3EB")],
               foreground=[("selected", "#00664D")])
# Stretchable images give ttk controls rounded borders without extra dependencies.
emis_theme_images = []


def _rounded_surface(fill, outline):
    from math import isqrt

    size, radius = 21, 7
    image = tk.PhotoImage(master=root, width=size, height=size)
    for y in range(size):
        dy = max(radius - y, y - (size - 1 - radius), 0)
        inset = radius - isqrt(radius * radius - dy * dy)
        image.put(outline, to=(inset, y, size - inset, y + 1))
        if 0 < y < size - 1:
            previous_dy = max(radius - y + 1, y + 1 - (size - 1 - radius), 0)
            inner = max(inset + 1, radius - isqrt(radius * radius - previous_dy * previous_dy))
            image.put(fill, to=(inner, y, size - inner, y + 1))
    emis_theme_images.append(image)
    return image


emis_style.configure("TButton", padding=(10, 6), background="#FFFFFF",
                     foreground="#00664D", bordercolor="#A0DACC")
emis_style.map("TButton",
               background=[("disabled", "#E8EDF0"), ("pressed", "#D5EFE6"), ("active", "#E7F7F1")],
               foreground=[("disabled", "#62716D")],
               bordercolor=[("disabled", "#D4DEDE"), ("focus", "#009975")])
emis_style.configure("Emis.Primary.TButton", background="#007F62",
                     foreground="#FFFFFF", bordercolor="#007F62")
emis_style.map("Emis.Primary.TButton",
               background=[("disabled", "#E8EDF0"), ("pressed", "#005742"), ("active", "#006C54")])
emis_style.element_create(
    "Emis.Card.surface", "image", _rounded_surface("#FFFFFF", "#D4DEDE"),
    border=8, sticky="nsew",
)
emis_style.layout("Emis.Card.TFrame", [("Emis.Card.surface", {"sticky": "nsew"})])
emis_style.configure("Emis.Card.TFrame", background=emis_background)
emis_style.configure("Emis.Background.TFrame", background=emis_background)
emis_style.configure("Emis.Header.TLabel", background=emis_background, foreground="#00664D",
                     font=("TkDefaultFont", 16, "bold"))
root.option_add("*Entry.selectBackground", "#DDF3EB")
root.option_add("*Entry.selectForeground", "#00664D")
root.option_add("*Spinbox.selectBackground", "#DDF3EB")
root.option_add("*Spinbox.selectForeground", "#00664D")
emis_style.configure("TEntry", padding=5, fieldbackground="#FFFFFF")
for input_style in ("TEntry", "TSpinbox", "TCombobox"):
    emis_style.map(input_style, selectbackground=[("!disabled", "#DDF3EB")],
                   selectforeground=[("!disabled", "#00664D")])
root.option_add("*TCombobox*Listbox.selectBackground", "#DDF3EB")
root.option_add("*TCombobox*Listbox.selectForeground", "#00664D")
root.option_add("*Menu.activeBackground", "#DDF3EB")
root.option_add("*Menu.activeForeground", "#00664D")
emis_style.configure("TCombobox", padding=5, selectbackground="#DDF3EB", selectforeground="#00664D")
emis_style.map("TCombobox",
               fieldbackground=[("readonly", "#FFFFFF")],
               foreground=[("readonly", emis_text)],
               bordercolor=[("focus", emis_green)])
emis_style.configure("Emis.Heading.TLabel", foreground="#00664D",
                     font=("TkDefaultFont", 11, "bold"))
emis_style.map("Treeview", background=[("selected", "#DDF3EB")],
               foreground=[("selected", emis_text)])

# Загружаем картинки устройств
load_device_images()

# Общий статус связи над вкладками.
app_header = ttk.Frame(root, style="Emis.Background.TFrame")
app_header.pack(fill="x", padx=16, pady=(12, 10))
try:
    logo = tk.PhotoImage(file=resource_path("images/emis-electra-ui.png"))
    app_logo = logo.subsample(max(1, (logo.width() + 109) // 110))
    ttk.Label(app_header, image=app_logo, background=emis_background).pack(side="left", padx=(0, 12))
except tk.TclError:
    pass
app_header_title = ttk.Label(app_header, text=tr("app_name"), style="Emis.Header.TLabel")
app_header_title.pack(side="left")
status_row = ttk.Frame(root, style="Emis.Background.TFrame")
status_row.pack(anchor="w", padx=16, pady=(0, 8))
connection_status_bar = ttk.Frame(status_row, padding=(10, 5), style="Emis.Card.TFrame")
connection_status_bar.pack(side="left")
lbl_status = tk.Label(connection_status_bar, text=tr("lbl_status"))
lbl_status.pack(side="left")
status_canvas = tk.Canvas(connection_status_bar, width=16, height=16, highlightthickness=0)
status_canvas.pack(side="left", padx=(3, 0))
status_indicator = status_canvas.create_oval(2, 2, 14, 14, fill="red")

meter_status_details = ttk.Frame(status_row, style="Emis.Background.TFrame")
meter_status_values = {}
meter_status_captions = {}
for field, caption in (("serial_number", "lbl_serial"), ("sw_version", "lbl_status_sw_version")):
    badge = ttk.Frame(meter_status_details, padding=(10, 5), style="Emis.Card.TFrame")
    badge.pack(side="left", padx=(8, 0))
    caption_label = tk.Label(badge, text=tr(caption))
    caption_label.pack(side="left")
    meter_status_captions[caption] = caption_label
    value_label = tk.Label(badge, text="—", font=("Consolas", 10))
    value_label.pack(side="left", padx=(3, 0))
    meter_status_values[field] = value_label


# 1. Cоздаём notebook и вкладки
notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True, padx=12, pady=(0, 12))

tab_conn = tk.Frame(notebook, background=emis_background)
notebook.add(tab_conn, text="...")
tab_info = tk.Frame(notebook, background=emis_background)
notebook.add(tab_info, text="...")
tab_time = tk.Frame(notebook, background=emis_background)
notebook.add(tab_time, text="...")
tab_params = tk.Frame(notebook, background=emis_background)
notebook.add(tab_params, text="...")
tab_settings = tk.Frame(notebook, background=emis_background)
notebook.add(tab_settings, text="...")

tab_tariff = tk.Frame(notebook, background=emis_background)
notebook.add(tab_tariff, text=tr("tab_tariff"))
tab_archives = tk.Frame(notebook, background=emis_background)
notebook.add(tab_archives, text=tr("tab_archives"))

tariff_panel = ttk.Frame(tab_tariff, padding=(24, 18), style="Emis.Card.TFrame")
tariff_panel.pack(pady=(28, 0))
tariff_title = ttk.Label(tariff_panel, text=tr("lbl_current_tariff"), style="Emis.Heading.TLabel")
tariff_title.pack()
active_tariff_label = ttk.Label(tariff_panel, text="—", font=("Consolas", 24), anchor="center")
active_tariff_label.pack(pady=(6, 0))

tariff_actions = ttk.Frame(tariff_panel)
tariff_actions.pack(pady=(20, 0))
tariff_schedule_label = ttk.Label(tariff_actions, text=tr("lbl_tariff_schedule"))
tariff_schedule_label.pack(side="left", padx=(0, 8))
tariff_schedule_button = ttk.Button(
    tariff_actions, text=tr("btn_tariff_schedule"),
    command=show_tariff_schedule_dialog, style="Emis.Primary.TButton", state="disabled",
)
tariff_schedule_button.pack(side="left")


# 2. Статичные элементы вкладки "Соединение"
com_controls_frame = ttk.Frame(tab_conn, padding=(12, 8), style="Emis.Card.TFrame")
com_controls_frame.pack(pady=(12, 6), padx=10, fill="x")
lbl_com_port = tk.Label(com_controls_frame, text=tr("lbl_com_port"))
lbl_com_port.pack(side="left")
port_var = tk.StringVar(value=tr("status_no_ports"))
port_menu = ttk.Combobox(com_controls_frame, textvariable=port_var, state="readonly", width=11)
port_menu.pack(side="left", padx=(5, 10))

refresh_btn = ttk.Button(com_controls_frame, text=tr("btn_refresh"), command=refresh_ports, width=14)
refresh_btn.pack(side="left", padx=(0, 8))
connect_btn = ttk.Button(com_controls_frame, text=tr("btn_connect"), command=connect_scan, style="Emis.Primary.TButton", width=16)
connect_btn.pack(side="left", padx=(0, 8))
disconnect_btn = ttk.Button(com_controls_frame, text=tr("btn_disconnect"), command=disconnect_device, style="Emis.Primary.TButton", state="disabled", width=16)
disconnect_btn.pack(side="left")

# Горизонтальный разделитель
sep = tk.Frame(tab_conn, height=2, bd=1, relief="sunken")
sep.pack(fill="x", padx=10, pady=6)

# Два столбца: параметры слева, тип счётчика справа
content_frame = ttk.Frame(tab_conn, padding=(12, 10), style="Emis.Card.TFrame")
content_frame.pack(fill="both", expand=True, padx=10)

# Левая колонка: параметры устройства
left_frame = tk.Frame(content_frame)
left_frame.pack(side="left", fill="y", expand=True)
lbl_modbus_title = ttk.Label(left_frame, text=tr("lbl_modbus_params"), style="Emis.Heading.TLabel")
lbl_modbus_title.pack(anchor="w", pady=(0, 5))

# Адрес
row_addr = tk.Frame(left_frame)
row_addr.pack(fill="x", pady=2)
lbl_address = tk.Label(row_addr, text=tr("lbl_address"))
lbl_address.pack(side="left")
addr_var = tk.StringVar(value="1")
addr_combo = ttk.Entry(
    row_addr, textvariable=addr_var, width=8, validate="key",
    validatecommand=(root.register(lambda value: not value or _valid_modbus_address(value)), "%P"),
)
addr_combo.pack(side="right")

# Скорость
row_speed = tk.Frame(left_frame)
row_speed.pack(fill="x", pady=2)
lbl_baud = tk.Label(row_speed, text=tr("lbl_baud"))
lbl_baud.pack(side="left")
speed_var = tk.StringVar(value=str(9600))
speed_combo = ttk.Combobox(row_speed, textvariable=speed_var, values=[str(v) for v in BAUD_VALUES], state="readonly", width=8)
speed_combo.pack(side="right")

# Чётность
row_parity = tk.Frame(left_frame)
row_parity.pack(fill="x", pady=2)
lbl_parity = tk.Label(row_parity, text=tr("lbl_parity"))
lbl_parity.pack(side="left")
parity_var = tk.StringVar(value="Even")
parity_combo = ttk.Combobox(row_parity, textvariable=parity_var, values=PARITY_LIST, state="readonly", width=8)
parity_combo.pack(side="right")

write_btn = ttk.Button(left_frame, text="Записать", command=write_settings, style="Emis.Primary.TButton", state="disabled")
write_btn.pack(pady=10)

# Вертикальный разделитель
separator = tk.Frame(content_frame, width=2, bg="gray")
separator.pack(side="left", fill="y", padx=10)

# Правая колонка: тип счётчика
right_frame = tk.Frame(content_frame)
right_frame.pack(side="left", fill="y", expand=True)

# Надпись "Тип подключаемого счётчика:" — жирным
type_label_title = ttk.Label(right_frame, text=tr("lbl_device_type"), style="Emis.Heading.TLabel")
type_label_title.pack(anchor="w", pady=(0, 5))

# Контейнер для картинки и текста
type_display_container = tk.Frame(right_frame)
type_display_container.pack(pady=5)

# Метка для картинки (пока пустая)
type_image_label = tk.Label(type_display_container)
type_image_label.pack(pady=2)

# Метка типа счётчика — две строки
type_label = tk.Label(type_display_container, text="—", justify="center", font=("TkDefaultFont", 10))
type_label.pack(pady=2)


# 3. Статичные элементы вкладки "Дата и время"
clock_panel = ttk.Frame(tab_time, padding=(24, 18), style="Emis.Card.TFrame")
clock_panel.pack(pady=(28, 0))
lbl_time_title = ttk.Label(clock_panel, text=tr("lbl_current_time"), style="Emis.Heading.TLabel")
lbl_time_title.pack()
current_time_value = ttk.Label(
    clock_panel, text=tr("lbl_meter_time_unavailable"),
    font=("Consolas", 24), width=21, anchor="center",
)
current_time_value.pack(pady=(6, 0))

time_btn_frame = ttk.Frame(clock_panel)
time_btn_frame.pack(pady=(20, 0))
settings_btn = ttk.Button(time_btn_frame, text=tr("btn_time_settings"), state="disabled")
settings_btn.pack(side="left", padx=(0, 8))
sync_pc_btn = ttk.Button(time_btn_frame, text=tr("btn_sync_pc"), style="Emis.Primary.TButton", state="disabled")
sync_pc_btn.pack(side="left")

# 4. Вызов set_language — все виджеты и функции уже созданы
set_language(current_language)


# =============================================================================
# 7. Завершение и запуск
# =============================================================================

root.update_idletasks()
width = root.winfo_reqwidth()
height = root.winfo_reqheight()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x = (screen_width - width) // 2
y = (screen_height - height) // 2
root.geometry(f"{width}x{height}+{x}+{y}")


def on_closing():
    """Обработка закрытия главного окна."""
    if writing_in_progress:
        return
    if power_supply_pending_port:
        messagebox.showwarning(
            tr("dlg_warning"),
            tr("power_supply_busy").format(port=power_supply_pending_port),
        )
        return
    stop_time_reader()
    root.destroy()


root.protocol("WM_DELETE_WINDOW", on_closing)

# Инициализация
_update_port_list()
# Создание динамических вкладок
create_parameters_tab()
create_settings_tab()
create_info_tab()

# Запуск фоновых проверок очередей
_check_settings_queue()
_check_time_queue()
_check_param_queue()
_check_info_queue()

settings_btn.config(command=open_time_settings)
sync_pc_btn.config(command=sync_pc_time)
update_device_type_display()

# Автоматическая подстройка размера окна
root.update_idletasks()
required_width = root.winfo_reqwidth()
required_height = root.winfo_reqheight()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

max_height = int(screen_height * 0.9)
actual_height = min(required_height, max_height)

root.minsize(required_width, min(actual_height, 500))
root.geometry(f"{required_width}x{actual_height}")
root.resizable(True, True)

# Тихо проверяем обновления после полной инициализации интерфейса.
# Сообщение появится только при наличии новой версии.
root.after(
    500,
    lambda: check_for_updates(show_messages=False),
)

root.mainloop()
