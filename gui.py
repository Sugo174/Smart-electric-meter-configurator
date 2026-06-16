""""
Конфигуратор счётчика постоянной энергии СКВТ ЭМИС-ЭЛЕКТРА 977

Версия: 1.08a
Назначение: Контроль и настройка параметров счётчика постоянной энергии
СКВТ ЭМИС-ЭЛЕКТРА 977 по протоколу ModBus RTU через COM-порт.
Автор: Boris Svistunov
Дата: 18.05.2026

Примечание: Все операции с COM-портом выполняются в фоновом потоке,
чтобы не блокировать GUI.
"""

# =============================================================================
# 1. Импорты
# =============================================================================

import tkinter as tk
from tkinter import ttk, messagebox
import time
import queue
import threading
import serial
import sys
import json
import os

# Сторонние библиотеки
import sv_ttk  # Современная тема для tkinter
from tkcalendar import Calendar 

# Локальные модули
from constants import BAUD_VALUES, PARITY_LIST
from device import (
    list_com_ports,
    scan_device,
    write_device_settings,
    read_device_time,
    write_device_time,
    sync_device_with_pc_time,
    read_device_parameters,
    read_device_parameters_dual,
    clear_device_energy,
    read_device_settings_params,
    write_max_current,
    write_sensitivity_voltage,
    write_sensitivity_current,
    write_decimal_places,
    write_tariff_periods,
    read_device_info
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
        "app_title": "Конфигуратор СКВТ ЭМИС-ЭЛЕКТРА 977 V1.08",
        "menu_settings": "☰ Настройки программы",
        "menu_help": "Справка",
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
        "btn_change_type": "Изменить тип счётчика",
        "device_name": "СКВТ ЭМИС-ЭЛЕКТРА 977",
        "device_single": "(одноканальный)",
        "device_dual": "(двухканальный)",
        "dlg_port_not_initialized": "Порт не инициализирован. Переподключите устройство.",
        "dlg_available_ports": "Доступные COM-порты",
        "dlg_ports_found": "Найдены порты:\n\n{}",
        "dlg_yes": "Да",
        "dlg_no": "Нет",
        
        # Вкладка "Дата и время"
        "lbl_current_time": "Текущее время устройства (ГГ-ММ-ДД чч:мм:сс):",
        "btn_time_settings": "Настроить",
        "btn_sync_pc": "Синхронизация с ПК🔄",
        "dlg_time_writing": "Идет запись времени...\nПожалуйста, подождите.",
                
        # Вкладка "Текущие значения" - одноканальный
        "lbl_energy": "Электроэнергия:",
        "lbl_energy_abs": "Абсолютная активная:",
        "lbl_energy_pos": "Суммарная положительная:",
        "lbl_energy_neg": "Суммарная обратная:",
        "lbl_current_params": "Текущие параметры:",
        "lbl_voltage": "Напряжение:",
        "lbl_current": "Ток:",
        "lbl_power": "Мощность:",
        "lbl_nominal": "Номинальные параметры:",
        "lbl_nom_voltage": "Номинальное напряжение:",
        "lbl_nom_current": "Номинальный ток:",
        
        # Вкладка "Текущие значения" - двухканальный
        "lbl_channel_a": "Канал A",
        "lbl_channel_b": "Канал B",
        "lbl_abs": "Абсолютная:",
        "lbl_pos": "Положительная:",
        "lbl_neg": "Обратная:",
        "lbl_nom_v": "Номинальное напр.:",
        "lbl_nom_i": "Номинальный ток:",
        
        # Вкладка "Настройки прибора"
        "lbl_max_current_a": "Максимальный ток канала A:",
        "lbl_max_current_b": "Максимальный ток канала B:",
        "lbl_sens_voltage": "Порог чувствительности напряжения:",
        "lbl_sens_current": "Порог чувствительности тока:",
        "lbl_decimal": "Десятичных знаков энергии:",
        "lbl_tariff": "Тарифных отрезков:",
        "btn_change": "Изменить",
        "btn_clear_energy": "Очистить значения энергии",
        
        # Вкладка "Информация о приборе"
        "lbl_serial": "Серийный номер:",
        "lbl_manufacturer": "Производитель:",
        "lbl_meter_type": "Тип счетчика:",
        "lbl_sw_version": "Версия метрологического ПО:",
        "lbl_release_date": "Дата выпуска:",
        
        # Диалоги
        "dlg_select_type": "Выбор типа счётчика",
        "dlg_select_type_prompt": "Выберите тип подключаемого счётчика:",
        "dlg_single": "Одноканальный",
        "dlg_dual": "Двухканальный",
        "dlg_exit": "Выход",
        "dlg_exit_confirm": "Тип счётчика не выбран.\nЗакрыть программу?",
        "dlg_search": "Поиск устройства",
        "dlg_searching": "Выполняется поиск устройства...\nПожалуйста, подождите.",
        "dlg_connected": "Подключено",
        "dlg_connected_msg": "Подключено устройство:\nАдрес: {}\nСкорость: {}\nЧётность: {}",
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
        "dlg_help_text":
            "Конфигуратор счетчика постоянного тока СКВТ ЭМИС-ЭЛЕКТРА 977 \n\n"
            "*** Алгоритм подключения счетчика ***\n\n"
            "1. Подключите устройство через USB - RS-485 адаптер. \n"
            "2. Подключите питание к устройству.\n"        
            "3. Нажмите кнопку «Обновить», чтобы увидеть доступные COM-порты. \n"
            "3. Выберите необходимый COM-порт.\n"
            "4. Нажмите кнопку «Подключиться» — программа подключится к устройству"
            " с любыми настройками соедения, определив их автоматически.\n"
            "5. Для изменения настроек соединения устройства - выберите необходимую"
            " скорость и/или адрес и/или четность и нажмите кнопку «Записать»,"
            " чтобы применить новые параметры соединения устройства. \n\n"
            "ВАЖНО: для корректной работы рекомендуется использвать"
            " только чётность ModBus соединения - EVEN \n\n\n"
            "*** Работа с программой после подключения счётчика ***\n\n"
            "1. Во вкладке «Соединение» доступна кнопка смены типа счётчика. \n"
            "2. Во вкладке «Инфо о приборе» информация о ПО и дате выпуска. \n"
            "3. Во вкладке «Дата и время» доступна ручная настройка даты и"
            " времени устройства, а так же синхронизация этих параметров с ПК. \n"
            "4. Во вкладке «Текущие значения» доступны для визуального контроля:"
            "все виды электроэнергии, напряжение, ток и мощность в зависимости"
            "от выбранного типа устройства. \n"
            "5. Во вкладке «Настройки прибора» доступны для изменения:"
            " некоторые пороговые значения прибора и ряд других настроек.",
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
    },
    
    "en": {
        # Menu
        "app_title": "Configurator SKVT EMIS-ELECTRA 977 V1.08",
        "menu_settings": "☰ Program Settings",
        "menu_help": "Help",
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
        "btn_change_type": "Change Meter Type",
        "device_name": "SKVT EMIS-ELECTRA 977",
        "device_single": "(single-channel)",
        "device_dual": "(dual-channel)",
        "dlg_port_not_initialized": "Port not initialized. Reconnect the device.",
        "dlg_available_ports": "Available COM Ports",
        "dlg_ports_found": "Ports found:\n\n{}",
        "dlg_yes": "Yes",
        "dlg_no": "No",
        
        # Date & Time tab
        "lbl_current_time": "Device Time (YY-MM-DD hh:mm:ss):",
        "btn_time_settings": "Settings",
        "btn_sync_pc": "Sync with PC🔄",
        "dlg_time_writing": "Writing time...\nPlease wait.",
        
        # Current Values - single channel
        "lbl_energy": "Energy:",
        "lbl_energy_abs": "Absolute Active:",
        "lbl_energy_pos": "Total Positive:",
        "lbl_energy_neg": "Total Negative:",
        "lbl_current_params": "Current Parameters:",
        "lbl_voltage": "Voltage:",
        "lbl_current": "Current:",
        "lbl_power": "Power:",
        "lbl_nominal": "Nominal Parameters:",
        "lbl_nom_voltage": "Nominal Voltage:",
        "lbl_nom_current": "Nominal Current:",
        
        # Current Values - dual channel
        "lbl_channel_a": "Channel A",
        "lbl_channel_b": "Channel B",
        "lbl_abs": "Absolute:",
        "lbl_pos": "Positive:",
        "lbl_neg": "Negative:",
        "lbl_nom_v": "Nom. Voltage:",
        "lbl_nom_i": "Nom. Current:",
        
        # Device Settings tab
        "lbl_max_current_a": "Max Current Channel A:",
        "lbl_max_current_b": "Max Current Channel B:",
        "lbl_sens_voltage": "Voltage Sensitivity Threshold:",
        "lbl_sens_current": "Current Sensitivity Threshold:",
        "lbl_decimal": "Energy Decimal Places:",
        "lbl_tariff": "Tariff Periods:",
        "btn_change": "Change",
        "btn_clear_energy": "Clear Energy Values",
        
        # Device Info tab
        "lbl_serial": "Serial Number:",
        "lbl_manufacturer": "Manufacturer:",
        "lbl_meter_type": "Meter Type:",
        "lbl_sw_version": "Metrological SW Version:",
        "lbl_release_date": "Release Date:",
        
        # Dialogs
        "dlg_select_type": "Select Meter Type",
        "dlg_select_type_prompt": "Select meter type to connect:",
        "dlg_single": "Single-Channel",
        "dlg_dual": "Dual-Channel",
        "dlg_exit": "Exit",
        "dlg_exit_confirm": "Meter type not selected.\nClose program?",
        "dlg_search": "Searching Device",
        "dlg_searching": "Searching for device...\nPlease wait.",
        "dlg_connected": "Connected",
        "dlg_write_params_warning": "Changing connection parameters will disconnect the device. Continue?",
        "dlg_connected_msg": "Device connected:\nAddress: {}\nBaud: {}\nParity: {}",
        "dlg_error": "Error",
        "dlg_no_port": "COM port not selected",
        "dlg_port_unavailable": "Connection Error",
        "dlg_port_unavailable_msg": "Port {} unavailable.\n\nPossible causes:\n• RS485 (A/B) cable disconnected\n• USB-RS485 adapter not connected\n• Adapter driver not responding\n\nRecommended:\n1. Check physical cable connections\n2. Reconnect USB adapter\n3. Click 'Refresh'",
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
        "dlg_help_text":
            "SKVT EMIS-ELECTRA 977 DC Energy Meter Configurator\n\n"
            "*** Meter Connection Procedure ***\n\n"
            "1. Connect the device via a USB-RS485 adapter. \n"
            "2. Power on the device.\n"
            "3. Click 'Refresh' to see available COM ports. \n"
            "4. Select the required COM port.\n"
            "5. Click 'Connect' - the program will connect to the device with any connection settings, automatically detecting them.\n"
            "6. To change device connection settings - select the required speed and/or address and/or parity and click 'Write' to apply the new connection parameters. \n\n"
            "IMPORTANT: for correct operation, it is recommended to use only EVEN ModBus connection parity. \n\n\n"
            "*** Working with the program after connecting the meter ***\n\n"
            "1. The 'Connection' tab contains the button to change the meter type. \n"
            "2. The 'Device Info' tab displays information about the metrological software and manufacturing date. \n"
            "3. The 'Date & Time' tab allows manual setting of the device date and time, as well as synchronization with the PC. \n"
            "4. The 'Current Values' tab provides visual monitoring: all energy types, voltage, current, and power depending on the selected device type. \n"
            "5. The 'Device Settings' tab allows modification of: some device threshold values and a number of other settings.",
        "dlg_change_type_warning": "Changing meter type requires reconnection.\nDisconnecting now.",
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
    },
    
    "zh": {
        # 菜单
        "app_title": "配置器 SKVT EMIS-ELECTRA 977 V1.08",
        "menu_settings": "☰ 程序设置",
        "menu_help": "帮助",
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
        "btn_change_type": "更改电表类型",
        "device_name": "SKVT EMIS-ELECTRA 977",
        "device_single": "(单通道)",
        "device_dual": "(双通道)",
        "dlg_port_not_initialized": "端口未初始化。请重新连接设备。",
        "dlg_available_ports": "可用COM端口",
        "dlg_ports_found": "找到的端口:\n\n{}",
        "dlg_yes": "是",
        "dlg_no": "否",
        
        # 日期时间选项卡
        "lbl_current_time": "设备时间 (年-月-日 时:分:秒):",
        "btn_time_settings": "设置",
        "btn_sync_pc": "与电脑同步🔄",
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
        
        # 当前值 - 双通道
        "lbl_channel_a": "通道A",
        "lbl_channel_b": "通道B",
        "lbl_abs": "绝对:",
        "lbl_pos": "正向:",
        "lbl_neg": "反向:",
        "lbl_nom_v": "额定电压:",
        "lbl_nom_i": "额定电流:",
        
        # 设备设置选项卡
        "lbl_max_current_a": "通道A最大电流:",
        "lbl_max_current_b": "通道B最大电流:",
        "lbl_sens_voltage": "电压灵敏度阈值:",
        "lbl_sens_current": "电流灵敏度阈值:",
        "lbl_decimal": "电能小数位数:",
        "lbl_tariff": "费率时段数:",
        "btn_change": "更改",
        "btn_clear_energy": "清除电能值",
        
        # 设备信息选项卡
        "lbl_serial": "序列号:",
        "lbl_manufacturer": "制造商:",
        "lbl_meter_type": "电表类型:",
        "lbl_sw_version": "计量软件版本:",
        "lbl_release_date": "生产日期:",
        
        # 对话框
        "dlg_select_type": "选择电表类型",
        "dlg_select_type_prompt": "选择要连接的电表类型:",
        "dlg_single": "单通道",
        "dlg_dual": "双通道",
        "dlg_exit": "退出",
        "dlg_exit_confirm": "未选择电表类型。\n关闭程序?",
        "dlg_search": "搜索设备",
        "dlg_searching": "正在搜索设备...\n请稍候。",
        "dlg_connected": "已连接",
        "dlg_write_params_warning": "更改连接参数将断开设备连接。继续?",
        "dlg_connected_msg": "设备已连接:\n地址: {}\n波特率: {}\n奇偶校验: {}",
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
        "dlg_help_text":
            "SKVT EMIS-ELECTRA 977 直流电能表配置器\n\n"
            "*** 电表连接步骤 ***\n\n"
            "1. 通过 USB-RS485 适配器连接设备。\n"
            "2. 给设备上电。\n"
            "3. 点击'刷新'查看可用 COM 端口。\n"
            "4. 选择所需的 COM 端口。\n"
            "5. 点击'连接' - 程序将连接设备并自动检测任何连接设置。\n"
            "6. 要更改设备连接设置 - 选择所需的波特率和/或地址和/或校验位，然后点击'写入'应用新参数。\n\n"
            "重要：为确保正常工作，建议 ModBus 连接仅使用 EVEN (偶) 校验位。\n\n\n"
            "*** 连接电表后的软件操作 ***\n\n"
            "1. 在'连接'选项卡中可以更改电表类型。\n"
            "2. '设备信息'选项卡显示计量软件和生产日期信息。\n"
            "3. '日期和时间'选项卡支持手动设置设备日期和时间，以及与电脑同步。\n"
            "4. '当前值'选项卡用于直观监控：根据所选设备类型显示各类电能、电压、电流及功率。\n"
            "5. '设备设置'选项卡用于修改：部分设备阈值参数及其他设置项。",
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
    }
}

# Вспомогательная функция для получения перевода
def tr(key):
    """Возвращает перевод для текущего языка."""
    return TRANSLATIONS.get(current_language, TRANSLATIONS["ru"]).get(key, key)

def set_language(lang_code):
    global current_language
    if lang_code not in TRANSLATIONS:
        return
    current_language = lang_code
    
    # Меняем заголовок главного окна
    root.title(tr("app_title"))
    
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
    
    settings_m.add_separator()
    
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
    
    # 3. Пересоздаём динамические вкладки
    global ui_rebuild_in_progress
    ui_rebuild_in_progress = True  # Приостанавливаем фоновый опрос
    
    create_parameters_tab()
    create_settings_tab()
    create_info_tab()

    ui_rebuild_in_progress = False # Разрешаем опрос снова
    
    # 4. Безопасно обновляем статичные элементы 
    try:
        lbl_modbus_title.config(text=tr("lbl_modbus_params"))
        lbl_time_title.config(text=tr("lbl_current_time"))
        lbl_com_port.config(text=tr("lbl_com_port"))
        lbl_status.config(text=tr("lbl_status"))
        lbl_address.config(text=tr("lbl_address"))
        lbl_baud.config(text=tr("lbl_baud"))
        lbl_parity.config(text=tr("lbl_parity"))
        write_btn.config(text=tr("btn_write"))
        refresh_btn.config(text=tr("btn_refresh"))
        connect_btn.config(text=tr("btn_connect"))
        disconnect_btn.config(text=tr("btn_disconnect"))
        change_type_btn.config(text=tr("btn_change_type"))
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
settings_tariff_combo = None

# Метки информации о приборе
info_serial_label = None
info_manufacturer_label = None
info_meter_type_label = None
info_sw_version_label = None
info_release_date_label = None

# Очереди
time_update_queue = queue.Queue()
param_update_queue = queue.Queue()
settings_update_queue = queue.Queue()
info_update_queue = queue.Queue()

# Глобальный флаг: выбрал ли пользователь тип счётчика
user_has_chosen_device_type = False

# Флаги фонового потока
time_reader_active = False
time_reader_thread = None
disconnect_flag = False  # Флаг обрыва связи для безопасной передачи в GUI

# Состояние устройства и GUI
device_type = None  # None пока пользователь не выбрал тип
was_ever_connected = False
writing_in_progress = False
post_write_cooldown_until = 0
operation_in_progress = False
manual_write_in_progress = False
settings_dialog_open = False

# Глобальные ссылки на модальные окна (для корректного закрытия)
search_window_ref = None
search_timeout_id = None
search_check_id = None

# Метка для картинки типа счётчика во вкладке "Соединение"
type_image_label = None

# Флаг: идёт перестройка интерфейса (смена языка/типа)
ui_rebuild_in_progress = False  

# =============================================================================
# 4. Вспомогательные функции
# =============================================================================

# Путь к файлу настроек
CONFIG_FILE = "config.json"
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
        "help": resource_path("icons/help.png"),
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
                saved_lang = config.get("language", "ru")
                if saved_lang in TRANSLATIONS:
                    current_language = saved_lang
    except Exception as e:
        print(f"[CONFIG] Ошибка загрузки: {e}")
        current_language = "ru"


def save_config():
    """Сохраняет текущие настройки в файл config.json"""
    try:
        config = {"language": current_language}
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


def start_time_reader():
    """Запускает фоновый поток для чтения времени и параметров."""
    global time_reader_active, time_reader_thread
    stop_time_reader()
    time_reader_active = True
    time_reader_thread = threading.Thread(target=_time_reader_worker, daemon=True)
    time_reader_thread.start()


def stop_time_reader():
    """Останавливает фоновый поток и гарантирует закрытие порта."""
    global time_reader_active, time_reader_thread, conn  
    time_reader_active = False
    
    if time_reader_thread:
        time_reader_thread.join(timeout=1.0)
        time_reader_thread = None
    
    # Принудительно закрываем порт если он открыт
    if conn and 'port_obj' in conn:
        try:
            if conn['port_obj'].is_open:
                conn['port_obj'].close()
        except Exception:
            pass


def _time_reader_worker():
    """Фоновый поток: читает время, параметры и настройки с устройства."""
    global time_reader_active, conn, disconnect_flag  
    
    next_time_read = time.time() + 1
    next_param_read = time.time() + 1
    next_settings_read = time.time() + 2
    next_info_read = time.time() + 2  
    
    while time_reader_active:
        if not conn:
            break

        if ui_rebuild_in_progress:
            time.sleep(0.1)
            continue
        
        # БЛОКИРОВКА: если идет ручная запись - вообще ничего не делаем        
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
            if now >= next_time_read:
                success, result = read_device_time(conn["port"], conn["slave"], conn["baud"], conn["parity"])
                if success:
                    time_update_queue.put(result["formatted"])
                else:
                    raise Exception("Потеряна связь с устройством")
                next_time_read = now + 1
                
            # 2. Параметры (каждую секунду)
            if now >= next_param_read:
                if device_type == "single":
                    success, params = read_device_parameters(conn["port"], conn["slave"], conn["baud"], conn["parity"])
                else:
                    success, params = read_device_parameters_dual(conn["port"], conn["slave"], conn["baud"], conn["parity"])
                if success:
                    param_update_queue.put(params)
                else:
                    raise Exception("Потеряна связь при чтении параметров")
                next_param_read = now + 1
                
            # 3. Настройки прибора (каждые 2 секунды)
            if now >= next_settings_read:
                success, settings = read_device_settings_params(
                    conn["port"], conn["slave"], conn["baud"], conn["parity"], device_type
                )
                if success:
                    settings_update_queue.put(settings)
                else:
                    raise Exception("Потеряна связь при чтении настроек")
                next_settings_read = now + 2
                
            # 4. Инфо о приборе (каждые 2 секунды)
            if now >= next_info_read:
                success, info = read_device_info(
                    conn["port"], conn["slave"], conn["baud"], conn["parity"]
                )
                if success:
                    info_update_queue.put(info)
                else:
                    raise Exception("Потеряна связь при чтении информации")
                next_info_read = now + 2

        except Exception:
            # 1. Останавливаем поток чтения
            time_reader_active = False
            disconnect_flag = True  # Сигнал главному потоку
            
            # 2. Очищаем очереди
            try:
                param_update_queue.put(None)
                settings_update_queue.put(None)
                time_update_queue.put(tr("status_disconnected"))
                info_update_queue.put(None)
            except:
                pass

            return

        time.sleep(0.1)


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
            current_time_value.config(text=time_str)
    except queue.Empty:
        pass
    root.after(100, _check_time_queue)


def _check_param_queue():
    """Обрабатывает очередь обновления параметров. Гарантирует непрерывный цикл."""
    try:
        while True:
            params = param_update_queue.get_nowait()
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
                # Обновление
                if device_type == "single":
                    if param_energy_abs_label and param_energy_abs_label.winfo_exists():
                        param_energy_abs_label.config(text=f"{params.get('energy_abs', 0):.2f} {tr('unit_kwh')}")
                    if param_energy_pos_label and param_energy_pos_label.winfo_exists():
                        param_energy_pos_label.config(text=f"{params.get('energy_pos', 0):.2f} {tr('unit_kwh')}")
                    if param_energy_neg_label and param_energy_neg_label.winfo_exists():
                        param_energy_neg_label.config(text=f"{params.get('energy_neg', 0):.2f} {tr('unit_kwh')}")
                    if param_voltage_label and param_voltage_label.winfo_exists():
                        param_voltage_label.config(text=f"{params.get('voltage', 0):.2f} {tr('unit_v')}")
                    if param_current_label and param_current_label.winfo_exists():
                        param_current_label.config(text=f"{params.get('current', 0):.3f} {tr('unit_a')}")
                    if param_power_label and param_power_label.winfo_exists():
                        param_power_label.config(text=f"{params.get('power', 0):.3f} {tr('unit_kw')}")
                    if param_nom_voltage_label and param_nom_voltage_label.winfo_exists():
                        param_nom_voltage_label.config(text=f"{params.get('nom_voltage', 0):.2f} {tr('unit_v')}")
                    if param_nom_current_label and param_nom_current_label.winfo_exists():
                        param_nom_current_label.config(text=f"{params.get('nom_current', 0):.2f} {tr('unit_a')}")
                else:
                    # Канал 1
                    if param_ch1_energy_abs_label and param_ch1_energy_abs_label.winfo_exists():
                        param_ch1_energy_abs_label.config(text=f"{params['ch1']['energy_abs']:.2f} {tr('unit_kwh')}")
                    if param_ch1_energy_pos_label and param_ch1_energy_pos_label.winfo_exists():
                        param_ch1_energy_pos_label.config(text=f"{params['ch1']['energy_pos']:.2f} {tr('unit_kwh')}")
                    if param_ch1_energy_neg_label and param_ch1_energy_neg_label.winfo_exists():
                        param_ch1_energy_neg_label.config(text=f"{params['ch1']['energy_neg']:.2f} {tr('unit_kwh')}")
                    if param_v1_label and param_v1_label.winfo_exists():
                        param_v1_label.config(text=f"{params['ch1']['voltage']:.2f} {tr('unit_v')}")
                    if param_i1_label and param_i1_label.winfo_exists():
                        param_i1_label.config(text=f"{params['ch1']['current']:.3f} {tr('unit_a')}")
                    if param_p1_label and param_p1_label.winfo_exists():
                        param_p1_label.config(text=f"{params['ch1']['power']:.3f} {tr('unit_kw')}")
                    if param_ch1_nom_v_label and param_ch1_nom_v_label.winfo_exists():
                        param_ch1_nom_v_label.config(text=f"{params['ch1']['nom_voltage']:.2f} {tr('unit_v')}")
                    if param_ch1_nom_i_label and param_ch1_nom_i_label.winfo_exists():
                        param_ch1_nom_i_label.config(text=f"{params['ch1']['nom_current']:.2f} {tr('unit_a')}")
                    # Канал 2
                    if param_ch2_energy_abs_label and param_ch2_energy_abs_label.winfo_exists():
                        param_ch2_energy_abs_label.config(text=f"{params['ch2']['energy_abs']:.2f} {tr('unit_kwh')}")
                    if param_ch2_energy_pos_label and param_ch2_energy_pos_label.winfo_exists():
                        param_ch2_energy_pos_label.config(text=f"{params['ch2']['energy_pos']:.2f} {tr('unit_kwh')}")
                    if param_ch2_energy_neg_label and param_ch2_energy_neg_label.winfo_exists():
                        param_ch2_energy_neg_label.config(text=f"{params['ch2']['energy_neg']:.2f} {tr('unit_kwh')}")
                    if param_v2_label and param_v2_label.winfo_exists():
                        param_v2_label.config(text=f"{params['ch2']['voltage']:.2f} {tr('unit_v')}")
                    if param_i2_label and param_i2_label.winfo_exists():
                        param_i2_label.config(text=f"{params['ch2']['current']:.3f} {tr('unit_a')}")
                    if param_p2_label and param_p2_label.winfo_exists():
                        param_p2_label.config(text=f"{params['ch2']['power']:.3f} {tr('unit_kw')}")
                    if param_ch2_nom_v_label and param_ch2_nom_v_label.winfo_exists():
                        param_ch2_nom_v_label.config(text=f"{params['ch2']['nom_voltage']:.2f} {tr('unit_v')}")
                    if param_ch2_nom_i_label and param_ch2_nom_i_label.winfo_exists():
                        param_ch2_nom_i_label.config(text=f"{params['ch2']['nom_current']:.2f} {tr('unit_a')}")
    except queue.Empty:
        pass
    except Exception:
        pass  # Игнорируем любые ошибки виджетов
    finally:
        # Цикл продолжится в любом случае
        root.after(100, _check_param_queue)


# =============================================================================
# 5. Обработка событий GUI
# =============================================================================

def _update_port_list():
    """Обновляет список доступных COM-портов в меню выбора."""
    ports = list_com_ports() or [tr("status_no_ports")]
    menu = port_menu["menu"]
    menu.delete(0, "end")
    for p in ports:
        menu.add_command(label=p, command=lambda v=p: port_var.set(v))
    port_var.set(ports[0])
    set_buttons_state("disabled")


def refresh_ports():
    """Показывает список доступных COM-портов в диалоговом окне."""
    ports = list_com_ports()
    if not ports:
        messagebox.showinfo(tr("dlg_available_ports"), tr("dlg_no_port"))
        ports = [tr("status_no_ports")]
    else:
        port_list = "\n".join(ports)
        messagebox.showinfo(tr("dlg_available_ports"), tr("dlg_ports_found").format(port_list))
    _update_port_list()


def connect_scan():
    global conn, connect_btn, disconnect_btn, status_canvas, status_indicator, is_device_ready
    global search_window_ref, search_timeout_id, search_check_id
    
    # Отменяем старые таймеры
    if search_timeout_id: root.after_cancel(search_timeout_id); search_timeout_id = None
    if search_check_id: root.after_cancel(search_check_id); search_check_id = None
    
    port = port_var.get().strip()
    if not port or port == tr("status_no_ports"):
        messagebox.showerror(tr("dlg_error"), tr("dlg_no_port"))
        return

    # Создаём окно поиска
    search_window_ref = tk.Toplevel(root)
    search_window_ref.title(tr("dlg_search"))
    search_window_ref.resizable(False, False)
    search_window_ref.transient(root)
    search_window_ref.grab_set()
    tk.Label(search_window_ref, text=tr("dlg_searching"), padx=20, pady=20).pack()
    search_window_ref.update_idletasks()
    
    x = root.winfo_rootx() + (root.winfo_width() - search_window_ref.winfo_width()) // 2
    y = root.winfo_rooty() + (root.winfo_height() - search_window_ref.winfo_height()) // 2
    search_window_ref.geometry(f"+{x}+{y}")
    
    root.config(cursor="watch")
    root.update()

    scan_result = [None]
    scan_error = [None]
    
    def do_scan():
        try:
            success, result = scan_device(port, int(addr_var.get()), int(speed_var.get()), parity_var.get())
            scan_result[0] = result if success else None
            scan_error[0] = None if success else result
        except Exception as e:
            scan_error[0] = str(e)
    
    threading.Thread(target=do_scan, daemon=True).start()
    
    def do_cleanup(success=False, result_data=None, error_msg=None):
        global search_window_ref, search_timeout_id, search_check_id
        
        # Отмена таймеров
        if search_timeout_id: root.after_cancel(search_timeout_id); search_timeout_id = None
        if search_check_id: root.after_cancel(search_check_id); search_check_id = None
        
        if success and result_data:
            global conn, was_ever_connected, is_device_ready
            conn = result_data
            was_ever_connected = True
            is_device_ready = True
            
            # 1. Обновляем комбобоксы (пока окно ещё висит)
            addr_var.set(str(conn["slave"]))
            speed_var.set(str(conn["baud"]))
            parity_var.set(conn["parity"])
            parity_combo.set(conn["parity"])
            
            # 2. Запускаем поток чтения данных (он начнёт заполнять вкладки прямо сейчас)
            start_time_reader()
            
            # 3. ПЛАНИРУЕМ финализацию через 1.5 сек
            def finalize_connection():
                global is_device_ready, search_window_ref
                
                # Закрываем окно поиска
                try:
                    if search_window_ref and search_window_ref.winfo_exists():
                        search_window_ref.grab_release()
                        search_window_ref.destroy()
                except: pass
                finally: 
                    search_window_ref = None
                
                # Сбрасываем курсор
                root.config(cursor="")
                root.update_idletasks()
                
                # Показываем сообщение об успехе
                messagebox.showinfo(tr("dlg_connected"), 
                    tr("dlg_connected_msg").format(conn['slave'], conn['baud'], conn['parity']))
                
                # Активируем кнопки и индикатор
                set_buttons_state("normal")
                connect_btn.config(state="disabled")
                refresh_btn.config(state="disabled")
                disconnect_btn.config(state="normal")
                status_canvas.itemconfig(status_indicator, fill="#66cc66")
                update_device_type_display()

            # Ждем 6 секунды перед выполнением финализации
            root.after(6000, finalize_connection)
            
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
                messagebox.showerror(tr("dlg_port_unavailable"), tr("dlg_port_unavailable_msg").format(port))
            else:
                messagebox.showerror(tr("dlg_error"), error_msg)
    
    def on_timeout():
        global search_timeout_id
        search_timeout_id = None
        if scan_result[0] is None and scan_error[0] is None:
            scan_error[0] = "Превышено время ожидания подключения (45 сек)"
            do_cleanup(error_msg=scan_error[0])
    
    search_timeout_id = root.after(45000, on_timeout)
    
    def check_complete():
        global search_check_id
        search_check_id = None
        if scan_result[0] is not None:
            do_cleanup(success=True, result_data=scan_result[0])
        elif scan_error[0] is not None:
            do_cleanup(error_msg=str(scan_error[0]))
        else:
            search_check_id = root.after(100, check_complete)
    
    search_check_id = root.after(100, check_complete)


def disconnect_device(show_message=False):
    global conn, connect_btn, disconnect_btn, status_canvas, status_indicator, was_ever_connected, is_device_ready
    stop_time_reader()
    conn = None
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
        messagebox.showwarning(tr("dlg_warning"), tr("dlg_disconnected"))

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
    """Записывает новые параметры подключения."""
    global conn
    if not conn:
        messagebox.showwarning(tr("dlg_warning"), tr("dlg_connect_first"))
        return

    if not _show_confirm_dialog(tr("dlg_warning"), tr("dlg_write_params_warning")):
        return

    stop_time_reader()
    time.sleep(0.5)
    root.config(cursor="watch")
    root.update()

    try:
        new_slave = int(addr_var.get())
        new_baud = int(speed_var.get())
        new_parity = parity_var.get()

        global writing_in_progress
        writing_in_progress = True

        success, result = write_device_settings(
            conn["port"], 
            conn["slave"], 
            conn["baud"], 
            conn["parity"],
            new_slave, 
            new_baud, 
            new_parity
        )
        
        if not success:
            messagebox.showerror(tr("dlg_write_error"), result)
            addr_var.set(str(conn["slave"]))
            speed_var.set(str(conn["baud"]))
            parity_var.set(conn["parity"])
            return

        # Обновляем объект подключения
        conn.update(slave=result["slave"], baud=result["baud"], parity=result["parity"])
        
        # Обновляем комбобоксы СРАЗУ (пока курсор ещё watch)
        addr_var.set(str(conn["slave"]))
        speed_var.set(str(conn["baud"]))
        parity_var.set(conn["parity"])
        parity_combo.set(conn["parity"])
        
        # Даём прибору время на применение настроек UART
        time.sleep(8.0)
        
        # Сбрасываем курсор
        root.config(cursor="")
        root.update_idletasks()
        
        # Показываем сообщение об успехе
        messagebox.showinfo(
            tr("dlg_write_success"),
            tr("dlg_write_success_msg").format(result['slave'], result['baud'], result['parity'])
        )
        
        # Перезапускаем поток чтения
        global post_write_cooldown_until
        post_write_cooldown_until = time.time() + 3.0
        start_time_reader()

    finally:
        writing_in_progress = False  
        root.config(cursor="")


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

    messagebox.showinfo(tr("dlg_write_success"), tr("dlg_time_written"), parent=parent_win)
    start_time_reader()
    return True, "OK"


def write_time():
    """Записывает только часы и/или минуты, оставляя дату без изменений."""
    hour_str = hour_var.get().strip()
    minute_str = minute_var.get().strip()

    if not hour_str and not minute_str:
        messagebox.showwarning(tr("dlg_warning"), tr("dlg_optional_time"))
        return

    success, result = read_device_time(
        conn["port"], conn["slave"], conn["baud"], conn["parity"]
    )
    if success:
        cur = result["data"]
    else:
        cur = {"year": 2025, "month": 1, "day": 1, "hour": 0, "minute": 0, "second": 0}

    Y = cur["year"]
    M = cur["month"]
    D = cur["day"]
    H = int(hour_str) if hour_str else cur["hour"]
    m = int(minute_str) if minute_str else cur["minute"]
    S = cur["second"]

    success, msg = write_device_time(
        conn["port"], conn["slave"], conn["baud"], conn["parity"],
        Y, M, D, H, m, S
    )
    if not success:
        messagebox.showerror(tr("dlg_time_write_error"), msg)
        return

    messagebox.showinfo(tr("dlg_write_success"), tr("dlg_time_written"))
    start_time_reader()


def open_time_settings():
    """Открывает окно настройки даты и времени."""
    global conn, is_device_ready
    if not conn:
        messagebox.showwarning(tr("dlg_warning"), tr("dlg_no_connection"))
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

    # ЦЕНТРИРОВАНИЕ ОКНА КАЛЕНДАРЯ
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
            
            wait_win = tk.Toplevel(root)
            wait_win.title(tr("dlg_time_settings"))
            wait_win.resizable(False, False)
            wait_win.transient(root)
            wait_win.grab_set()
            wait_win.config(cursor="watch")
            
            tk.Label(wait_win, text=tr("dlg_time_writing"), padx=25, pady=20,
                     font=("Segoe UI", 11)).pack()
            
            wait_win.update_idletasks()
            wait_win.lift()
            wait_win.focus_force()
            wx = root.winfo_rootx() + (root.winfo_width() - wait_win.winfo_width()) // 2
            wy = root.winfo_rooty() + (root.winfo_height() - wait_win.winfo_height()) // 2
            wait_win.geometry(f"+{wx}+{wy}")
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
                # МГНОВЕННОЕ ОБНОВЛЕНИЕ БЕЗ ЗАВИСАНИЯ
                new_time_str = f"{Y:04}-{M:02}-{D:02} {H:02}:{m:02}:{S:02}"
                current_time_value.config(text=new_time_str)
                time_update_queue.put(new_time_str)
                root.after(0, _check_time_queue)
                
                messagebox.showinfo(tr("dlg_write_success"), tr("dlg_time_written"), parent=win)
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
    ttk.Button(btn_frame, text=tr("dlg_apply"), command=apply_time, width=10).pack(side="left", padx=5)


def sync_pc_time():
    """Синхронизирует время устройства с текущим временем ПК."""
    global conn, is_device_ready
    if not conn:
        messagebox.showwarning(tr("dlg_warning"), tr("dlg_no_connection"))
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

        messagebox.showinfo(tr("dlg_write_success"), tr("dlg_sync_success").format(result))
        current_time_value.config(text=result)
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
        messagebox.showwarning(tr("dlg_warning"), tr("dlg_no_connection"))
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

        if not messagebox.askyesno(
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

        messagebox.showinfo(tr("dlg_write_success"), tr("dlg_clear_success"))

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
    ttk.Button(btn_frame, text="OK", command=on_ok, width=10).pack(side="left", padx=5)

    win.update_idletasks()
    x = root.winfo_rootx() + (root.winfo_width() - win.winfo_width()) // 2
    y = root.winfo_rooty() + (root.winfo_height() - win.winfo_height()) // 2
    win.geometry(f"+{x}+{y}")

    root.wait_window(win)
    return result[0]


def show_help():
    """Показывает окно справки."""
    help_text = tr("dlg_help_text")
    messagebox.showinfo(tr("dlg_help"), help_text)


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

    # Очищаем старое содержимое
    for widget in tab_params.winfo_children():
        widget.destroy()

    if device_type == "single": 
        center_frame = tk.Frame(tab_params)
        center_frame.pack(pady=20)

        # --- Блок 1: Энергия ---
        tk.Label(center_frame, text=tr("lbl_energy"), font=("TkDefaultFont", 10, "bold")).pack(anchor="w", pady=(0, 4))
        
        row_e1 = tk.Frame(center_frame)
        row_e1.pack(anchor="w", pady=2)
        tk.Label(row_e1, text=tr("lbl_energy_abs")).pack(side="left")
        param_energy_abs_label = tk.Label(row_e1, text=tr("status_disconnected"), font=("Consolas", 12))
        param_energy_abs_label.pack(side="left", padx=(10, 0))

        row_e2 = tk.Frame(center_frame)
        row_e2.pack(anchor="w", pady=2)
        tk.Label(row_e2, text=tr("lbl_energy_pos")).pack(side="left")
        param_energy_pos_label = tk.Label(row_e2, text=tr("status_disconnected"), font=("Consolas", 12))
        param_energy_pos_label.pack(side="left", padx=(10, 0))

        row_e3 = tk.Frame(center_frame)
        row_e3.pack(anchor="w", pady=(0, 8))
        tk.Label(row_e3, text=tr("lbl_energy_neg")).pack(side="left")
        param_energy_neg_label = tk.Label(row_e3, text=tr("status_disconnected"), font=("Consolas", 12))
        param_energy_neg_label.pack(side="left", padx=(10, 0))

        tk.Frame(center_frame, height=2, bd=1, relief="sunken").pack(fill="x", pady=5)

        # --- Блок 2: Текущие параметры ---
        tk.Label(center_frame, text=tr("lbl_current_params"), font=("TkDefaultFont", 10, "bold")).pack(anchor="w", pady=(4, 0))

        row1 = tk.Frame(center_frame)
        row1.pack(anchor="w", pady=2)
        tk.Label(row1, text=tr("lbl_voltage")).pack(side="left")
        param_voltage_label = tk.Label(row1, text=tr("status_disconnected"), font=("Consolas", 12))
        param_voltage_label.pack(side="left", padx=(10, 0))

        row2 = tk.Frame(center_frame)
        row2.pack(anchor="w", pady=2)
        tk.Label(row2, text=tr("lbl_current")).pack(side="left")
        param_current_label = tk.Label(row2, text=tr("status_disconnected"), font=("Consolas", 12))
        param_current_label.pack(side="left", padx=(10, 0))

        row3 = tk.Frame(center_frame)
        row3.pack(anchor="w", pady=(0, 8))
        tk.Label(row3, text=tr("lbl_power")).pack(side="left")
        param_power_label = tk.Label(row3, text=tr("status_disconnected"), font=("Consolas", 12))
        param_power_label.pack(side="left", padx=(10, 0))

        tk.Frame(center_frame, height=2, bd=1, relief="sunken").pack(fill="x", pady=5)

        # --- Блок 3: Номиналы ---
        tk.Label(center_frame, text=tr("lbl_nominal"), font=("TkDefaultFont", 10, "bold")).pack(anchor="w", pady=(4, 0))

        row_n1 = tk.Frame(center_frame)
        row_n1.pack(anchor="w", pady=2)
        tk.Label(row_n1, text=tr("lbl_nom_voltage")).pack(side="left")
        param_nom_voltage_label = tk.Label(row_n1, text=tr("status_disconnected"), font=("Consolas", 12))
        param_nom_voltage_label.pack(side="left", padx=(10, 0))

        row_n2 = tk.Frame(center_frame)
        row_n2.pack(anchor="w", pady=2)
        tk.Label(row_n2, text=tr("lbl_nom_current")).pack(side="left")
        param_nom_current_label = tk.Label(row_n2, text=tr("status_disconnected"), font=("Consolas", 12))
        param_nom_current_label.pack(side="left", padx=(10, 0))

    else:   # Двухканальный счетчик
        main_frame = tk.Frame(tab_params)
        main_frame.pack(pady=10)

        # --- ЛЕВАЯ КОЛОНКА: КАНАЛ A ---
        col1 = tk.Frame(main_frame)
        col1.pack(side="left", padx=20, pady=5)
        tk.Label(col1, text=tr("lbl_channel_a"), font=("TkDefaultFont", 10, "bold")).pack(anchor="w", pady=(0, 10))

        # Блок 1: Энергия
        tk.Label(col1, text=tr("lbl_energy"), font=("TkDefaultFont", 9, "bold")).pack(anchor="w", pady=(4, 0))
        
        r1 = tk.Frame(col1); r1.pack(anchor="w", pady=1)
        tk.Label(r1, text=tr("lbl_abs")).pack(side="left")
        param_ch1_energy_abs_label = tk.Label(r1, text=tr("status_disconnected"), font=("Consolas", 11))
        param_ch1_energy_abs_label.pack(side="left", padx=(5, 0))

        r2 = tk.Frame(col1); r2.pack(anchor="w", pady=1)
        tk.Label(r2, text=tr("lbl_pos")).pack(side="left")
        param_ch1_energy_pos_label = tk.Label(r2, text=tr("status_disconnected"), font=("Consolas", 11))
        param_ch1_energy_pos_label.pack(side="left", padx=(5, 0))

        r3 = tk.Frame(col1); r3.pack(anchor="w", pady=(1, 4))
        tk.Label(r3, text=tr("lbl_neg")).pack(side="left")
        param_ch1_energy_neg_label = tk.Label(r3, text=tr("status_disconnected"), font=("Consolas", 11))
        param_ch1_energy_neg_label.pack(side="left", padx=(5, 0))

        tk.Frame(col1, height=2, bd=1, relief="sunken").pack(fill="x", pady=4)
        
        # Блок 2: Текущие параметры
        tk.Label(col1, text=tr("lbl_current_params"), font=("TkDefaultFont", 9, "bold")).pack(anchor="w", pady=(4, 0))

        row_v1 = tk.Frame(col1); row_v1.pack(anchor="w", pady=1)
        tk.Label(row_v1, text=tr("lbl_voltage")).pack(side="left")
        param_v1_label = tk.Label(row_v1, text=tr("status_disconnected"), font=("Consolas", 11))
        param_v1_label.pack(side="left", padx=(10, 0))

        row_i1 = tk.Frame(col1); row_i1.pack(anchor="w", pady=1)
        tk.Label(row_i1, text=tr("lbl_current")).pack(side="left")
        param_i1_label = tk.Label(row_i1, text=tr("status_disconnected"), font=("Consolas", 11))
        param_i1_label.pack(side="left", padx=(10, 0))

        row_p1 = tk.Frame(col1); row_p1.pack(anchor="w", pady=(1, 4))
        tk.Label(row_p1, text=tr("lbl_power")).pack(side="left")
        param_p1_label = tk.Label(row_p1, text=tr("status_disconnected"), font=("Consolas", 11))
        param_p1_label.pack(side="left", padx=(10, 0))

        tk.Frame(col1, height=2, bd=1, relief="sunken").pack(fill="x", pady=4)
        
        # Блок 3: Номиналы
        tk.Label(col1, text=tr("lbl_nominal"), font=("TkDefaultFont", 9, "bold")).pack(anchor="w", pady=(4, 0))

        rn1 = tk.Frame(col1); rn1.pack(anchor="w", pady=1)
        tk.Label(rn1, text=tr("lbl_nom_v")).pack(side="left")
        param_ch1_nom_v_label = tk.Label(rn1, text=tr("status_disconnected"), font=("Consolas", 11))
        param_ch1_nom_v_label.pack(side="left", padx=(5, 0))

        rn2 = tk.Frame(col1); rn2.pack(anchor="w", pady=1)
        tk.Label(rn2, text=tr("lbl_nom_i")).pack(side="left")
        param_ch1_nom_i_label = tk.Label(rn2, text=tr("status_disconnected"), font=("Consolas", 11))
        param_ch1_nom_i_label.pack(side="left", padx=(5, 0))

        separator = tk.Frame(main_frame, width=2, bg="gray")
        separator.pack(side="left", fill="y", padx=10)
        
        # --- ПРАВАЯ КОЛОНКА: КАНАЛ B ---
        col2 = tk.Frame(main_frame)
        col2.pack(side="left", padx=20, pady=5)
        tk.Label(col2, text=tr("lbl_channel_b"), font=("TkDefaultFont", 10, "bold")).pack(anchor="w", pady=(0, 10))

        # Блок 1: Энергия
        tk.Label(col2, text=tr("lbl_energy"), font=("TkDefaultFont", 9, "bold")).pack(anchor="w", pady=(4, 0))
        
        r1b = tk.Frame(col2); r1b.pack(anchor="w", pady=1)
        tk.Label(r1b, text=tr("lbl_abs")).pack(side="left")
        param_ch2_energy_abs_label = tk.Label(r1b, text=tr("status_disconnected"), font=("Consolas", 11))
        param_ch2_energy_abs_label.pack(side="left", padx=(5, 0))

        r2b = tk.Frame(col2); r2b.pack(anchor="w", pady=1)
        tk.Label(r2b, text=tr("lbl_pos")).pack(side="left")
        param_ch2_energy_pos_label = tk.Label(r2b, text=tr("status_disconnected"), font=("Consolas", 11))
        param_ch2_energy_pos_label.pack(side="left", padx=(5, 0))

        r3b = tk.Frame(col2); r3b.pack(anchor="w", pady=(1, 4))
        tk.Label(r3b, text=tr("lbl_neg")).pack(side="left")
        param_ch2_energy_neg_label = tk.Label(r3b, text=tr("status_disconnected"), font=("Consolas", 11))
        param_ch2_energy_neg_label.pack(side="left", padx=(5, 0))

        tk.Frame(col2, height=2, bd=1, relief="sunken").pack(fill="x", pady=4)

        # Блок 2: Текущие параметры
        tk.Label(col2, text=tr("lbl_current_params"), font=("TkDefaultFont", 9, "bold")).pack(anchor="w", pady=(4, 0))

        row_v2 = tk.Frame(col2); row_v2.pack(anchor="w", pady=1)
        tk.Label(row_v2, text=tr("lbl_voltage")).pack(side="left")
        param_v2_label = tk.Label(row_v2, text=tr("status_disconnected"), font=("Consolas", 11))
        param_v2_label.pack(side="left", padx=(10, 0))

        row_i2 = tk.Frame(col2); row_i2.pack(anchor="w", pady=1)
        tk.Label(row_i2, text=tr("lbl_current")).pack(side="left")
        param_i2_label = tk.Label(row_i2, text=tr("status_disconnected"), font=("Consolas", 11))
        param_i2_label.pack(side="left", padx=(10, 0))

        row_p2 = tk.Frame(col2); row_p2.pack(anchor="w", pady=(1, 4))
        tk.Label(row_p2, text=tr("lbl_power")).pack(side="left")
        param_p2_label = tk.Label(row_p2, text=tr("status_disconnected"), font=("Consolas", 11))
        param_p2_label.pack(side="left", padx=(10, 0))

        tk.Frame(col2, height=2, bd=1, relief="sunken").pack(fill="x", pady=4)

        # Блок 3: Номиналы
        tk.Label(col2, text=tr("lbl_nominal"), font=("TkDefaultFont", 9, "bold")).pack(anchor="w", pady=(4, 0))

        rn1b = tk.Frame(col2); rn1b.pack(anchor="w", pady=1)
        tk.Label(rn1b, text=tr("lbl_nom_v")).pack(side="left")
        param_ch2_nom_v_label = tk.Label(rn1b, text=tr("status_disconnected"), font=("Consolas", 11))
        param_ch2_nom_v_label.pack(side="left", padx=(5, 0))

        rn2b = tk.Frame(col2); rn2b.pack(anchor="w", pady=1)
        tk.Label(rn2b, text=tr("lbl_nom_i")).pack(side="left")
        param_ch2_nom_i_label = tk.Label(rn2b, text=tr("status_disconnected"), font=("Consolas", 11))
        param_ch2_nom_i_label.pack(side="left", padx=(5, 0))


def on_close_attempt(win):
    """Обработка закрытия окна выбора типа счётчика."""
    if messagebox.askyesno(tr("dlg_exit"), tr("dlg_exit_confirm")):
        win.destroy()
        root.destroy()
        sys.exit()  


def choose_device_type_on_start():
    """Отображает окно выбора типа счётчика при запуске программы."""
    global device_type, user_has_chosen_device_type
    win = tk.Toplevel(root)
    win.title(tr("dlg_select_type"))
    win.grab_set()
    win.resizable(False, False)
    
    def on_close():
        if messagebox.askyesno(tr("dlg_exit"), tr("dlg_exit_confirm")):
            win.destroy()
            root.quit()  
       
    win.protocol("WM_DELETE_WINDOW", on_close)

    tk.Label(win, text=tr("dlg_select_type_prompt"), font=("Segoe UI", 10)).pack(pady=(15, 10))

    # Контейнер для двух колонок
    container = tk.Frame(win)
    container.pack(padx=20, pady=5)

    def set_type(t):
        global device_type, user_has_chosen_device_type
        device_type = t
        user_has_chosen_device_type = True
        win.destroy()

    # --- ЛЕВАЯ КОЛОНКА: ОДНОКАНАЛЬНЫЙ ---
    frame_single = tk.Frame(container)
    frame_single.pack(side="left", padx=15)
    if "single" in DEVICE_IMAGES:
        tk.Label(frame_single, image=DEVICE_IMAGES["single"]).pack(pady=5)
    tk.Button(frame_single, text=tr("dlg_single"), command=lambda: set_type("single"), width=22).pack(pady=5)

    # --- ПРАВАЯ КОЛОНКА: ДВУХКАНАЛЬНЫЙ ---
    frame_dual = tk.Frame(container)
    frame_dual.pack(side="left", padx=15)
    if "dual" in DEVICE_IMAGES:
        tk.Label(frame_dual, image=DEVICE_IMAGES["dual"]).pack(pady=5)
    tk.Button(frame_dual, text=tr("dlg_dual"), command=lambda: set_type("dual"), width=22).pack(pady=5)

    win.update_idletasks()
    x = root.winfo_x() + (root.winfo_width() - win.winfo_width()) // 2
    y = root.winfo_y() + (root.winfo_height() - win.winfo_height()) // 2
    win.geometry(f"+{x}+{y}")

    win.wait_window()
    
    # ПОСЛЕ ВЫБОРА ТИПА - ОБНОВЛЯЕМ ОТОБРАЖЕНИЕ
    if user_has_chosen_device_type:
        update_device_type_display()
        

def create_settings_tab():
    """Создаёт вкладку «Настройки прибора»."""
    global settings_max_i_a_label, settings_max_i_b_label
    global settings_sens_v_label, settings_sens_i_label
    global settings_decimal_combo, settings_tariff_combo

    # Очищаем старое содержимое
    for widget in tab_settings.winfo_children():
        widget.destroy()

    # 1. Контейнер на всю площадь вкладки (распорка)
    main_container = tk.Frame(tab_settings)
    main_container.pack(expand=True, fill="both")

    # 2. Центральный блок настроек (автоматически центрируется внутри)
    center_block = tk.Frame(main_container)
    center_block.pack(pady=20)

    # 3. Сетка для строк (размер определяется контентом, не растягивается)
    grid_frame = tk.Frame(center_block)
    grid_frame.pack()

    # --- Строка 1 ---
    tk.Label(grid_frame, text=tr("lbl_max_current_a"),
             anchor="e", width=34, font=("TkDefaultFont", 10)).grid(row=0, column=0, sticky="e", pady=5, padx=(0, 12))
    settings_max_i_a_label = tk.Label(grid_frame, text=tr("status_disconnected"), font=("Consolas", 11), width=8, anchor="w")
    settings_max_i_a_label.grid(row=0, column=1, sticky="w", pady=5)
    ttk.Button(grid_frame, text=tr("btn_change"), command=_on_change_max_current_a, width=10).grid(row=0, column=2, sticky="w", pady=5, padx=(10, 0))

    # --- Строка 2 ---
    tk.Label(grid_frame, text=tr("lbl_max_current_b"),
             anchor="e", width=34, font=("TkDefaultFont", 10)).grid(row=1, column=0, sticky="e", pady=5, padx=(0, 12))
    settings_max_i_b_label = tk.Label(grid_frame, text=tr("status_disconnected"), font=("Consolas", 11), width=8, anchor="w")
    settings_max_i_b_label.grid(row=1, column=1, sticky="w", pady=5)
    ttk.Button(grid_frame, text=tr("btn_change"), command=_on_change_max_current_b, width=10).grid(row=1, column=2, sticky="w", pady=5, padx=(10, 0))

    # --- Строка 3 ---
    tk.Label(grid_frame, text=tr("lbl_sens_voltage"),
             anchor="e", width=34, font=("TkDefaultFont", 10)).grid(row=2, column=0, sticky="e", pady=5, padx=(0, 12))
    settings_sens_v_label = tk.Label(grid_frame, text=tr("status_disconnected"), font=("Consolas", 11), width=8, anchor="w")
    settings_sens_v_label.grid(row=2, column=1, sticky="w", pady=5)
    ttk.Button(grid_frame, text=tr("btn_change"), command=_on_change_sens_voltage, width=10).grid(row=2, column=2, sticky="w", pady=5, padx=(10, 0))

    # --- Строка 4 ---
    tk.Label(grid_frame, text=tr("lbl_sens_current"),
             anchor="e", width=34, font=("TkDefaultFont", 10)).grid(row=3, column=0, sticky="e", pady=5, padx=(0, 12))
    settings_sens_i_label = tk.Label(grid_frame, text=tr("status_disconnected"), font=("Consolas", 11), width=8, anchor="w")
    settings_sens_i_label.grid(row=3, column=1, sticky="w", pady=5)
    ttk.Button(grid_frame, text=tr("btn_change"), command=_on_change_sens_current, width=10).grid(row=3, column=2, sticky="w", pady=5, padx=(10, 0))

    # --- Строка 5 ---
    tk.Label(grid_frame, text=tr("lbl_decimal"),
             anchor="e", width=34, font=("TkDefaultFont", 10)).grid(row=4, column=0, sticky="e", pady=5, padx=(0, 12))
    settings_decimal_combo = ttk.Combobox(grid_frame, values=[str(i) for i in range(1, 4)], state="readonly", width=8)
    settings_decimal_combo.grid(row=4, column=1, sticky="w", pady=5)
    settings_decimal_combo.bind('<<ComboboxSelected>>', _on_change_decimal_places)

    # --- Строка 6 ---
    tk.Label(grid_frame, text=tr("lbl_tariff"),
             anchor="e", width=34, font=("TkDefaultFont", 10)).grid(row=5, column=0, sticky="e", pady=5, padx=(0, 12))
    settings_tariff_combo = ttk.Combobox(grid_frame, values=[str(i) for i in range(1, 15)], state="readonly", width=8)
    settings_tariff_combo.grid(row=5, column=1, sticky="w", pady=5)
    settings_tariff_combo.bind('<<ComboboxSelected>>', _on_change_tariff_periods)

    # Разделитель и кнопка очистки (в том же центральном блоке, выравниваются по ширине сетки)
    tk.Frame(center_block, height=2, bd=1, relief="sunken").pack(fill="x", pady=15)
    ttk.Button(center_block, text=tr("btn_clear_energy"), command=clear_energy_values).pack(pady=(0, 10))


def create_info_tab():
    """Создаёт вкладку «Информация о приборе»."""
    global info_serial_label, info_manufacturer_label, info_meter_type_label
    global info_sw_version_label, info_release_date_label

    # Очищаем старое содержимое
    for widget in tab_info.winfo_children():
        widget.destroy()
        
    # 1. Контейнер на всю площадь вкладки (распорка)
    main_container = tk.Frame(tab_info)
    main_container.pack(expand=True, fill="both")

    # 2. Центральный блок (автоматически центрируется)
    center_block = tk.Frame(main_container)
    center_block.pack(pady=20)

    # 3. Сетка для строк
    grid_frame = tk.Frame(center_block)
    grid_frame.pack()

    # Вспомогательная функция для создания строки
    def _add_row(row, label_key, label_ref):
        tk.Label(grid_frame, text=tr(label_key),
                 anchor="e", width=35, font=("TkDefaultFont", 10)).grid(row=row, column=0, sticky="e", pady=6, padx=(0, 15))
        lbl = tk.Label(grid_frame, text=tr("status_disconnected"), font=("Consolas", 11), width=35, anchor="w")
        lbl.grid(row=row, column=1, sticky="w", pady=6)
        return lbl

    # Создаём метки и сохраняем их в глобальные переменные
    info_serial_label = _add_row(0, "lbl_serial", None)
    info_manufacturer_label = _add_row(1, "lbl_manufacturer", None)
    info_meter_type_label = _add_row(2, "lbl_meter_type", None)
    info_sw_version_label = _add_row(3, "lbl_sw_version", None)
    info_release_date_label = _add_row(4, "lbl_release_date", None)
      

def widget_exists(w):
    """Проверяет, существует ли виджет в Tkinter."""
    try:
        return w.winfo_exists() if w else False
    except:
        return False


def _check_settings_queue():
    """Обрабатывает очередь обновления настроек."""
    try:
        while True:
            settings = settings_update_queue.get_nowait()
            if settings is None:
                if settings_max_i_a_label: settings_max_i_a_label.config(text=tr("status_disconnected"))
                if settings_max_i_b_label: settings_max_i_b_label.config(text=tr("status_disconnected"))
                if settings_sens_v_label: settings_sens_v_label.config(text=tr("status_disconnected"))
                if settings_sens_i_label: settings_sens_i_label.config(text=tr("status_disconnected"))
            else:
                if settings_max_i_a_label: settings_max_i_a_label.config(text=f"{settings['max_current_a']:.2f} {tr('unit_a')}")
                if settings_max_i_b_label: 
                    if 'max_current_b' in settings:
                        settings_max_i_b_label.config(text=f"{settings['max_current_b']:.2f} {tr('unit_a')}")
                    else:
                        settings_max_i_b_label.config(text=tr("status_disconnected"))
                if settings_sens_v_label: settings_sens_v_label.config(text=f"{settings['sens_voltage']:.1f} {tr('unit_percent')}")
                if settings_sens_i_label: settings_sens_i_label.config(text=f"{settings['sens_current']:.1f} {tr('unit_percent')}")
                
                # Безопасное обновление Combobox (избегаем ошибки 'popdown')
                try:
                    if settings_decimal_combo and settings_decimal_combo.focus_get() != settings_decimal_combo:
                        settings_decimal_combo.set(str(settings['decimal_places']))
                    if settings_tariff_combo and settings_tariff_combo.focus_get() != settings_tariff_combo:
                        settings_tariff_combo.set(str(settings['tariff_periods']))
                except Exception:
                    # Если фокус не удалось определить (например, при пересоздании), пропускаем обновление
                    pass
    except queue.Empty:
        pass
    root.after(100, _check_settings_queue)


def _check_info_queue():
    """Обрабатывает очередь обновления информации о приборе."""
    try:
        while True:
            info = info_update_queue.get_nowait()
            if info is None:
                if info_serial_label: info_serial_label.config(text=tr("status_disconnected"))
                if info_manufacturer_label: info_manufacturer_label.config(text=tr("status_disconnected"))
                if info_meter_type_label: info_meter_type_label.config(text=tr("status_disconnected"))
                if info_sw_version_label: info_sw_version_label.config(text=tr("status_disconnected"))
                if info_release_date_label: info_release_date_label.config(text=tr("status_disconnected"))
            else:
                if info_serial_label: info_serial_label.config(text=info.get('serial_number', tr("status_disconnected")))
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
                    messagebox.showinfo(tr("dlg_write_success"), tr("dlg_value_written"), parent=dialog)
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
    ttk.Button(btn_frame, text=tr("dlg_apply"), command=on_ok, width=10).pack(side="left", padx=5)
    
    dialog.update_idletasks()
    x = root.winfo_rootx() + (root.winfo_width() - dialog.winfo_width()) // 2
    y = root.winfo_rooty() + (root.winfo_height() - dialog.winfo_height()) // 2
    dialog.geometry(f"+{x}+{y}")


def _show_confirm_dialog(title, message):
    """Показывает модальное окно подтверждения с переведенными кнопками."""
    result = [False]
    win = tk.Toplevel(root)
    win.title(title)
    win.transient(root)
    win.grab_set()
    win.resizable(False, False)

    tk.Label(win, text=message, font=("Segoe UI", 10), padx=20, pady=15, justify="center").pack()

    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=10)

    def on_yes():
        result[0] = True
        win.destroy()
    def on_no():
        result[0] = False
        win.destroy()

    ttk.Button(btn_frame, text=tr("dlg_yes"), command=on_yes, width=10).pack(side="left", padx=5)
    ttk.Button(btn_frame, text=tr("dlg_no"), command=on_no, width=10).pack(side="left", padx=5)

    win.update_idletasks()
    x = root.winfo_rootx() + (root.winfo_width() - win.winfo_width()) // 2
    y = root.winfo_rooty() + (root.winfo_height() - win.winfo_height()) // 2
    win.geometry(f"+{x}+{y}")

    root.wait_window(win)
    return result[0]


def _on_change_max_current_a():
    global settings_dialog_open
    if not conn:
        messagebox.showwarning(tr("dlg_warning"), tr("dlg_no_connection"))
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
    value_var = tk.StringVar(value=f"{current_val:.2f}")
    entry = tk.Entry(dialog, textvariable=value_var, font=("Consolas", 12), width=15)
    entry.pack(pady=5); entry.focus(); entry.select_range(0, 'end')

    def on_ok():
        try:
            new_value = float(value_var.get().replace(',', '.'))
            success, msg = write_max_current(conn["port"], conn["slave"], conn["baud"], conn["parity"], 'a', new_value)
            if success:
                _, new_settings = read_device_settings_params(conn["port"], conn["slave"], conn["baud"], conn["parity"], device_type)
                settings_update_queue.put(new_settings)
                root.after(0, _check_settings_queue)
                messagebox.showinfo(tr("dlg_write_success"), tr("dlg_value_written"), parent=dialog)
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
    ttk.Button(btn_frame, text=tr("dlg_apply"), command=on_ok, width=10).pack(side="left", padx=5)
    dialog.update_idletasks()
    dialog.geometry(f"+{root.winfo_rootx() + (root.winfo_width() - dialog.winfo_width()) // 2}+{root.winfo_rooty() + (root.winfo_height() - dialog.winfo_height()) // 2}")


def _on_change_max_current_b():
    global settings_dialog_open
    if device_type != "dual": 
        return
    if not conn:
        messagebox.showwarning(tr("dlg_warning"), tr("dlg_no_connection"))
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

    # Перехват нажатия на крестик (✕)
    dialog.protocol("WM_DELETE_WINDOW", cleanup_and_close)

    tk.Label(dialog, text=tr("dlg_max_current_b_prompt"), font=("Segoe UI", 10)).pack(pady=(15, 5), padx=20)
    value_var = tk.StringVar(value=f"{current_val:.2f}")
    entry = tk.Entry(dialog, textvariable=value_var, font=("Consolas", 12), width=15)
    entry.pack(pady=5)
    entry.focus()
    entry.select_range(0, 'end')

    def on_ok():
        try:
            new_value = float(value_var.get().replace(',', '.'))
            success, msg = write_max_current(conn["port"], conn["slave"], conn["baud"], conn["parity"], 'b', new_value)
            if success:
                _, new_settings = read_device_settings_params(conn["port"], conn["slave"], conn["baud"], conn["parity"], device_type)
                settings_update_queue.put(new_settings)
                root.after(0, _check_settings_queue)
                messagebox.showinfo(tr("dlg_write_success"), tr("dlg_value_written"), parent=dialog)
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
    ttk.Button(btn_frame, text=tr("dlg_apply"), command=on_ok, width=10).pack(side="left", padx=5)

    dialog.update_idletasks()
    x = root.winfo_rootx() + (root.winfo_width() - dialog.winfo_width()) // 2
    y = root.winfo_rooty() + (root.winfo_height() - dialog.winfo_height()) // 2
    dialog.geometry(f"+{x}+{y}")


def _on_change_sens_voltage():
    global settings_dialog_open
    if not conn:
        messagebox.showwarning(tr("dlg_warning"), tr("dlg_no_connection"))
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
    entry = tk.Entry(dialog, textvariable=value_var, font=("Consolas", 12), width=15)
    entry.pack(pady=5)
    entry.focus()
    entry.select_range(0, 'end')

    def on_ok():
        try:
            new_value = float(value_var.get().replace(',', '.'))
            success, msg = write_sensitivity_voltage(conn["port"], conn["slave"], conn["baud"], conn["parity"], new_value)
            if success:
                _, new_settings = read_device_settings_params(conn["port"], conn["slave"], conn["baud"], conn["parity"], device_type)
                settings_update_queue.put(new_settings)
                root.after(0, _check_settings_queue)
                messagebox.showinfo(tr("dlg_write_success"), tr("dlg_value_written"), parent=dialog)
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
    ttk.Button(btn_frame, text=tr("dlg_apply"), command=on_ok, width=10).pack(side="left", padx=5)

    dialog.update_idletasks()
    x = root.winfo_rootx() + (root.winfo_width() - dialog.winfo_width()) // 2
    y = root.winfo_rooty() + (root.winfo_height() - dialog.winfo_height()) // 2
    dialog.geometry(f"+{x}+{y}")


def _on_change_sens_current():
    global settings_dialog_open
    if not conn:
        messagebox.showwarning(tr("dlg_warning"), tr("dlg_no_connection"))
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
    entry = tk.Entry(dialog, textvariable=value_var, font=("Consolas", 12), width=15)
    entry.pack(pady=5)
    entry.focus()
    entry.select_range(0, 'end')

    def on_ok():
        try:
            new_value = float(value_var.get().replace(',', '.'))
            success, msg = write_sensitivity_current(conn["port"], conn["slave"], conn["baud"], conn["parity"], new_value)
            if success:
                _, new_settings = read_device_settings_params(conn["port"], conn["slave"], conn["baud"], conn["parity"], device_type)
                settings_update_queue.put(new_settings)
                root.after(0, _check_settings_queue)
                messagebox.showinfo(tr("dlg_write_success"), tr("dlg_value_written"), parent=dialog)
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
    ttk.Button(btn_frame, text=tr("dlg_apply"), command=on_ok, width=10).pack(side="left", padx=5)

    dialog.update_idletasks()
    x = root.winfo_rootx() + (root.winfo_width() - dialog.winfo_width()) // 2
    y = root.winfo_rooty() + (root.winfo_height() - dialog.winfo_height()) // 2
    dialog.geometry(f"+{x}+{y}")


def _on_change_decimal_places(event=None):
    global settings_dialog_open
    if not conn:
        messagebox.showwarning(tr("dlg_warning"), tr("dlg_no_connection"))
        settings_decimal_combo.set("1")
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
            settings_decimal_combo.set("1") # Сброс при ошибке
    except Exception as e:
        messagebox.showerror(tr("dlg_input_error"), str(e))
        settings_decimal_combo.set("1")
    finally:
        settings_dialog_open = False
        start_time_reader() # Запускаем поток обратно


def _on_change_tariff_periods(event=None):
    global settings_dialog_open
    if not conn:
        messagebox.showwarning(tr("dlg_warning"), tr("dlg_no_connection"))
        settings_tariff_combo.set("1")
        return
    if settings_dialog_open:
        return
    settings_dialog_open = True

    # Останавливаем поток перед записью
    stop_time_reader()
    time.sleep(0.3)
    
    try:
        value = int(settings_tariff_combo.get())
        success, msg = write_tariff_periods(conn["port"], conn["slave"], conn["baud"], conn["parity"], value)
        if success:
            _, new_settings = read_device_settings_params(conn["port"], conn["slave"], conn["baud"], conn["parity"], device_type)
            settings_update_queue.put(new_settings)
            root.after(0, _check_settings_queue)
        else:
            messagebox.showerror(tr("dlg_write_error"), msg)
            settings_tariff_combo.set("1") # Сброс при ошибке
    except Exception as e:
        messagebox.showerror(tr("dlg_input_error"), str(e))
        settings_tariff_combo.set("1")
    finally:
        settings_dialog_open = False
        start_time_reader() # Запускаем поток обратно


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
        
    if settings_max_i_b_label:
        if device_type == "single":
            settings_max_i_b_label.config(text=tr("status_disconnected") + " (N/A)")


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
    root.resizable(False, True)  # По ширине фикс, по высоте можно тянуть


def choose_device_type_from_menu():
    """Позволяет изменить тип счётчика через меню (с картинками)."""
    global device_type
    
    if conn:
        messagebox.showwarning(tr("dlg_warning"), tr("dlg_change_type_warning"))
        disconnect_device()

    win = tk.Toplevel(root)
    win.title(tr("dlg_select_type"))
    win.grab_set()
    win.resizable(False, False)

    def set_type(t):
        global device_type
        stop_time_reader()
        device_type = t
        
        # Пересоздаём вкладки под новый тип
        create_parameters_tab()
        create_settings_tab()
        create_info_tab()
        
        # Обновляем отображение типа (картинка + текст)
        update_device_type_display()
        
        win.destroy()

    tk.Label(win, text=tr("dlg_select_type_prompt"), font=("Segoe UI", 10)).pack(pady=(15, 10))

    # Контейнер для двух колонок
    container = tk.Frame(win)
    container.pack(padx=20, pady=5)

    # --- ЛЕВАЯ КОЛОНКА: ОДНОКАНАЛЬНЫЙ ---
    frame_single = tk.Frame(container)
    frame_single.pack(side="left", padx=15)
    if "single" in DEVICE_IMAGES:
        tk.Label(frame_single, image=DEVICE_IMAGES["single"]).pack(pady=5)
    tk.Button(frame_single, text=tr("dlg_single"), command=lambda: set_type("single"), width=22).pack(pady=5)

    # --- ПРАВАЯ КОЛОНКА: ДВУХКАНАЛЬНЫЙ ---
    frame_dual = tk.Frame(container)
    frame_dual.pack(side="left", padx=15)
    if "dual" in DEVICE_IMAGES:
        tk.Label(frame_dual, image=DEVICE_IMAGES["dual"]).pack(pady=5)
    tk.Button(frame_dual, text=tr("dlg_dual"), command=lambda: set_type("dual"), width=22).pack(pady=5)

    win.update_idletasks()
    x = root.winfo_x() + (root.winfo_width() - win.winfo_width()) // 2
    y = root.winfo_y() + (root.winfo_height() - win.winfo_height()) // 2
    win.geometry(f"+{x}+{y}")

# =============================================================================
# 6. Создание графического интерфейса
# =============================================================================

# Загружаем сохраненный язык
load_config()

root = tk.Tk()
root.title(tr("app_title"))
# 1. Иконка для ГЛАВНОГО окна (через ICO - работает надежно на Windows)
try:
    root.iconbitmap(resource_path("app.ico"))
except Exception:
    pass

# 2. Иконка для ВСЕХ внутренних окон (через PNG - наследуется автоматически)
# ВАЖНО: True означает "применить ко всем будущим окнам (Toplevel)"
try:
    icon_png_path = resource_path("app.png")
    if os.path.exists(icon_png_path):
        app_icon_img = tk.PhotoImage(file=icon_png_path)
        root.iconphoto(True, app_icon_img) 
except Exception:
    # Если PNG нет, программа не упадет, просто на окнах будет перышко
    pass
sv_ttk.set_theme("light")

# Загружаем картинки устройств
load_device_images()

# 1. Cоздаём notebook и вкладки
notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True)

tab_conn = tk.Frame(notebook)
notebook.add(tab_conn, text="...")
tab_info = tk.Frame(notebook)
notebook.add(tab_info, text="...")
tab_time = tk.Frame(notebook)
notebook.add(tab_time, text="...")
tab_params = tk.Frame(notebook)
notebook.add(tab_params, text="...")
tab_settings = tk.Frame(notebook)
notebook.add(tab_settings, text="...")

# 2. Статичные элементы вкладки "Соединение"
com_status_frame = tk.Frame(tab_conn)
com_status_frame.pack(pady=(12, 6), padx=10, fill="x")
lbl_com_port = tk.Label(com_status_frame, text=tr("lbl_com_port"))
lbl_com_port.pack(side="left")
port_var = tk.StringVar(value=tr("status_no_ports"))
port_menu = ttk.OptionMenu(com_status_frame, port_var, tr("status_no_ports"))
port_menu.config(width=11)
port_menu.pack(side="left", padx=(5, 10))
lbl_status = tk.Label(com_status_frame, text=tr("lbl_status"))
lbl_status.pack(side="left")
status_canvas = tk.Canvas(com_status_frame, width=16, height=16, highlightthickness=0)
status_canvas.pack(side="left", padx=(3, 0))
status_indicator = status_canvas.create_oval(2, 2, 14, 14, fill="red")

# Кнопки управления
btn_row = tk.Frame(tab_conn)
btn_row.pack(pady=(0, 8), padx=10, fill="x")
refresh_btn = ttk.Button(btn_row, text="Обновить", command=refresh_ports, width=14)
refresh_btn.pack(side="left", padx=(0, 8))
connect_btn = ttk.Button(btn_row, text="Подключиться", command=connect_scan, width=16)
connect_btn.pack(side="left", padx=8)
disconnect_btn = ttk.Button(btn_row, text="Отключиться", command=disconnect_device, state="disabled", width=16)
disconnect_btn.pack(side="left", padx=8)

# Горизонтальный разделитель
sep = tk.Frame(tab_conn, height=2, bd=1, relief="sunken")
sep.pack(fill="x", padx=10, pady=6)

# Два столбца: параметры слева, тип счётчика справа
content_frame = tk.Frame(tab_conn)
content_frame.pack(fill="both", expand=True, padx=10)

# Левая колонка: параметры устройства
left_frame = tk.Frame(content_frame)
left_frame.pack(side="left", fill="y", expand=True)
lbl_modbus_title = tk.Label(left_frame, text=tr("lbl_modbus_params"), font=("TkDefaultFont", 10, "bold"))
lbl_modbus_title.pack(anchor="w", pady=(0, 5))

# Адрес
row_addr = tk.Frame(left_frame)
row_addr.pack(fill="x", pady=2)
lbl_address = tk.Label(row_addr, text=tr("lbl_address"))
lbl_address.pack(side="left")
addr_var = tk.StringVar(value="1")
addr_combo = ttk.Combobox(row_addr, textvariable=addr_var, values=[str(i) for i in range(1, 11)], state="readonly", width=8)
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

write_btn = ttk.Button(left_frame, text="Записать", command=write_settings, state="disabled")
write_btn.pack(pady=10)

# Вертикальный разделитель
separator = tk.Frame(content_frame, width=2, bg="gray")
separator.pack(side="left", fill="y", padx=10)

# Правая колонка: тип счётчика
right_frame = tk.Frame(content_frame)
right_frame.pack(side="left", fill="y", expand=True)

# Надпись "Тип подключаемого счётчика:" — жирным
type_label_title = tk.Label(right_frame, text=tr("lbl_device_type"), font=("TkDefaultFont", 10, "bold"))
type_label_title.pack(anchor="w", pady=(10, 0))

# Контейнер для картинки и текста
type_display_container = tk.Frame(right_frame)
type_display_container.pack(pady=5)

# Метка для картинки (пока пустая)
type_image_label = tk.Label(type_display_container)
type_image_label.pack(pady=2)

# Метка типа счётчика — две строки
type_label = tk.Label(type_display_container, text="—", justify="center", font=("TkDefaultFont", 10))
type_label.pack(pady=2)

# Кнопка смены типа
change_type_btn = ttk.Button(right_frame, text=tr("btn_change_type"), command=choose_device_type_from_menu, width=22)
change_type_btn.pack(pady=5)

# 3. Статичные элементы вкладки "Дата и время"
lbl_time_title = tk.Label(tab_time, text=tr("lbl_current_time"))
lbl_time_title.pack(anchor="w", padx=10, pady=(12, 0))
time_btn_frame = tk.Frame(tab_time)
time_btn_frame.pack(padx=10, pady=(4, 10), fill="x")
current_time_value = tk.Label(time_btn_frame, text="—", font=("Consolas", 12))
current_time_value.pack(side="left")
settings_btn = ttk.Button(time_btn_frame, text="Настроить", state="disabled")
settings_btn.pack(side="left", padx=(15, 5))
sync_pc_btn = ttk.Button(time_btn_frame, text="Синхронизация с ПК🔄", state="disabled")
sync_pc_btn.pack(side="left", padx=(5, 0))

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
    stop_time_reader()
    root.destroy()


root.protocol("WM_DELETE_WINDOW", on_closing)

# Инициализация
_update_port_list()
choose_device_type_on_start()

if not user_has_chosen_device_type:
    root.destroy()
    sys.exit()

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

# ФИНАЛЬНОЕ ОБНОВЛЕНИЕ ОТОБРАЖЕНИЯ ТИПА СЧЁТЧИКА
update_device_type_display()

# Автоматическая подстройка размера окна
root.update_idletasks()
required_width = root.winfo_reqwidth()
required_height = root.winfo_reqheight()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

max_height = int(screen_height * 0.9)
actual_height = min(required_height, max_height)

root.geometry(f"{required_width}x{actual_height}")
root.resizable(False, True)

root.mainloop()
