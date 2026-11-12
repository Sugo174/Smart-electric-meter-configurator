"""Localized topics for the configurator help window."""

HELP_TOPICS = {
    'ru': (
        (
            'Подключение',
            'Выберите тип счётчика. Подключите адаптер USB–RS-485 и подайте питание на СКВТ. На вкладке «Соединение» нажмите «Обновить», выберите COM-порт и нажмите «Подключиться». Программа определит адрес, скорость и чётность. Статус связи виден над вкладками.\n\n'
            'Для изменения параметров Modbus выберите значения и нажмите «Записать». Рекомендуемая чётность — EVEN. Во время записи сохраняйте питание и подключение адаптера.',
        ),
        (
            'Информация о приборе',
            'На вкладке «Инфо о приборе» можно прочитать и изменить сведения о СКВТ. Серийный номер должен содержать 12 цифр. Для номеров серии 977 отображается расшифровка исполнения.\n\n'
            'Чтобы заполнить поля, нажмите «Автозаполнение», отсканируйте или введите номер, затем нажмите Enter или «Применить». Программа синхронизирует часы с ПК и записывает дату ввода номера. Если операция прервётся, часть полей может быть уже записана.',
        ),
        (
            'Дата и время',
            'Вкладка показывает время и дату счётчика. Их можно задать вручную или синхронизировать с ПК.',
        ),
        (
            'Настройки прибора',
            'Здесь задаются пороги, постоянная импульсного выхода и число знаков энергии на дисплее счётчика. Для двухканального прибора доступны настройки по каналам. Выбор значения из списка запускает запись в СКВТ.\n\n'
            'Редактор тарифного расписания читает, проверяет и записывает периоды тарифов 1–4.',
        ),
        (
            'Текущие значения',
            'На вкладке отображаются энергия, напряжение, ток, мощность и номиналы доступных каналов. «Измерить» запускает усреднение напряжения, тока и мощности. После 10 успешных отсчётов появляются средние значения. «Остановить» возвращает отображение текущих показаний.',
        ),
        (
            'Протокол поверки',
            'Нажмите «Измерить» и дождитесь 10 отсчётов. Затем нажмите «Заполнить протокол», дополните данные поверки, выберите класс точности и отметьте четыре проверки. Сохраните новый файл Excel.\n\n'
            'Для каждого канала пройдите пять точек напряжения с вводом показаний вольтметра. Затем пройдите четыре точки тока, мощности и периода. Переключайте ЭнИ вручную и вводите период с частотомера. При записи программа использует последние 10 отсчётов СКВТ. Для двухканального прибора переключите стенд на канал В по подсказке.\n\n'
            'Держите файл закрытым в Excel до конца записи. После пересчёта Excel итог будет P, если все четыре проверки пройдены и все погрешности в допуске. В остальных случаях итог — F.',
        ),
        (
            'Источник напряжения',
            'Включите панель источника через «Настройки программы». Панель появится внизу вкладки «Текущие значения». Выберите COM-порт источника и подключитесь. На панели можно задать напряжение и управлять выходом.',
        ),
        (
            'Обновления',
            'Проверку можно запустить из меню «Настройки программы». При запуске конфигуратор также проверяет наличие новой версии и предлагает перейти к загрузке.',
        ),
    ),
    'en': (
        (
            'Connection',
            'Select the meter type. Connect the USB–RS-485 adapter and power the meter. On the Connection tab, refresh the port list, select the COM port and click Connect. The program detects the address, baud rate and parity. Connection status is shown above the tabs.\n\n'
            'To change Modbus parameters, select the values and write them to the meter. EVEN parity is recommended. Keep the meter powered and the adapter connected while writing.',
        ),
        (
            'Meter information',
            'Use the meter information tab to read or edit device details. The serial number must contain 12 digits. Series 977 serial numbers are decoded on this tab.\n\n'
            'For autofill, scan or enter the serial number and press Enter or Apply. The program synchronizes the meter clock with the PC and records the date of entry. If the operation fails partway through, some fields may already have been written.',
        ),
        (
            'Date and time',
            'The tab shows the meter date and time. Set them manually or synchronize them with the PC.',
        ),
        (
            'Meter settings',
            'Set thresholds, the pulse output constant and the number of energy decimal places on the meter display. Dual-channel meters show settings for both channels. Selecting a value from a list writes it to the meter.\n\n'
            'Use the tariff schedule editor to read, validate and write periods for tariffs 1–4.',
        ),
        (
            'Live readings',
            'The tab displays energy, voltage, current, power and nominal values for the available channels. Measure starts averaging voltage, current and power. Averages appear after 10 successful readings. Stop returns to live readings.',
        ),
        (
            'Verification report',
            'Click Measure and wait for 10 readings. Open the report workflow, complete the report details, select the accuracy class and record the four checks. Save a new Excel file.\n\n'
            'For each channel, enter the voltmeter reading at five voltage points. Then complete four current, power and period points. Set the load simulator manually and enter the period from the frequency counter. The program saves averages from the last 10 meter readings. For a dual-channel meter, switch the test setup to channel B when prompted.\n\n'
            'Keep the file closed in Excel while recording points. After recalculation in Excel, the result is P if all four checks pass and all errors are within tolerance. Otherwise it is F.',
        ),
        (
            'Voltage source',
            'Enable the voltage source panel from the program settings menu. It appears below the live readings. Select the source COM port and connect. Use the panel to set the voltage and control the output.',
        ),
        (
            'Updates',
            'Check for updates from the program settings menu. The configurator also checks at startup and offers a download when a new version is available.',
        ),
    ),
    'zh': (
        (
            '连接',
            '选择电表类型，连接 USB–RS-485 转换器并给电表供电。在连接选项卡刷新端口列表，选择 COM 端口，然后连接。程序自动检测地址、波特率和校验方式。连接状态显示在选项卡上方。\n\n'
            '修改 Modbus 参数后将设置写入电表。建议使用偶校验。写入时请保持供电和通信连接。',
        ),
        (
            '电表信息',
            '在电表信息选项卡读取和修改设备信息。序列号必须为 12 位数字。界面会解析 977 系列的序列号。\n\n'
            '使用自动填写时，扫描或输入序列号，然后按 Enter 或点击应用。程序将电表时钟与电脑同步，并写入序列号录入日期。如果操作中断，部分字段可能已经写入。',
        ),
        (
            '日期和时间',
            '此选项卡显示电表的日期和时间。可以手动设置，也可以与电脑同步。',
        ),
        (
            '电表设置',
            '可设置阈值、脉冲输出常数以及电表显示的电能小数位数。双通道电表显示各通道设置。从列表中选择值后，程序会将其写入电表。\n\n'
            '费率时段编辑器可读取、校验并写入费率 1–4 的时段。',
        ),
        (
            '实时读数',
            '此选项卡显示各通道的电能、电压、电流、功率及额定值。点击测量开始对电压、电流和功率求平均，成功采集 10 次后显示平均值。点击停止可恢复显示实时读数。',
        ),
        (
            '检定记录',
            '点击测量并等待采集 10 次，打开检定记录。填写检定信息，选择准确度等级，记录四项检查结果，然后保存新的 Excel 文件。\n\n'
            '每个通道先完成五个电压点并录入电压表读数，再完成四个电流、功率和周期点。手动切换负载模拟器，并录入频率计显示的周期。写入时使用最近 10 次电表读数的平均值。双通道电表请按提示将测试设备切换至通道 B。\n\n'
            '记录数据时请关闭 Excel 中的文件。Excel 重新计算后，四项检查均通过且所有误差均在允许范围内时，结果为 P，否则为 F。',
        ),
        (
            '电压源',
            '在程序设置菜单中启用电压源面板。面板位于实时读数选项卡下方。选择电压源的 COM 端口并连接后，可设置电压并控制输出。',
        ),
        (
            '更新',
            '在程序设置菜单中检查更新。程序启动时也会检查更新，发现新版本后会提示下载。',
        ),
    ),
}
