"""Localized topics for the configurator help window."""

HELP_TOPICS = {
    "ru": (
        (
            "Подключение",
            "Подключите адаптер USB–RS-485 и подайте питание на СКВТ. Обновите список COM-портов, выберите порт и нажмите «Подключиться». Поиск сначала проверяет введённый адрес с разными параметрами связи, затем перебирает адреса 1–254 по комбинациям скорости и чётности. Поиск можно отменить.\n\n"
            "Адрес Modbus можно ввести вручную. Чтобы изменить адрес, скорость или чётность на приборе, нажмите «Записать». Рекомендуемая чётность — Even. Над вкладками виден статус связи. После подключения там же отображаются серийный номер и версия ПО. Если программа не определит исполнение автоматически, выберите число каналов в открывшемся окне или нажмите «Отмена», чтобы прервать подключение.",
        ),
        (
            "Инфо о приборе",
            "Здесь можно прочитать и изменить серийный номер, производителя, тип, версию метрологического ПО и дату. Редактирование и автозаполнение доступны после подключения. При изменении серийного номера введите 12 цифр. Для номеров серии 977 отображается расшифровка исполнения.\n\n"
            "В «Автозаполнении» отсканируйте или введите номер и нажмите Enter или «Применить». Программа синхронизирует часы с ПК и запишет сведения о приборе. В поле даты записывается дата ввода номера. При сбое часть полей может быть уже записана.",
        ),
        (
            "Дата и время",
            "Вкладка показывает время и дату счётчика. Нажмите «Настроить вручную» для ручного ввода или «Синхронизировать с ПК», чтобы записать время и дату компьютера.",
        ),
        (
            "Текущие значения",
            "Вкладка показывает номиналы, электроэнергию, напряжение, ток и мощность доступных каналов. Номиналы отображаются целыми, текущие напряжение, ток и мощность — с четырьмя знаками после запятой. Разрядность энергии берётся из настройки прибора. Абсолютная энергия — сумма модулей прямой и обратной.\n\n"
            "После подключения доступна кнопка «Заполнить протокол». Усреднение запускается внутри выбранной точки поверки.",
        ),
        (
            "Настройки прибора",
            "Здесь можно изменить максимальный ток, пороги чувствительности, постоянную импульсного выхода и разрядность энергии (0, 2 или 3 знака). Максимальный ток вводится целыми амперами. Импульсная постоянная задаётся отдельно для каждого доступного канала. Выбор значения в выпадающем списке запускает запись в прибор.\n\n"
            "«Очистить значения энергии» сбрасывает накопленные показания. Для этого требуются пароль и подтверждение.",
        ),
        (
            "Тарифное расписание",
            "«Текущий тариф» рассчитывается по часам счётчика и сохранённому суточному расписанию. Если расписание пустое или данные недоступны, отображается «—».\n\n"
            "Нажмите «Настроить расписание», чтобы прочитать и отредактировать периоды тарифов 1–4. Новый период начинается с 00:00. Часы и минуты вводятся цифрами в отдельных полях. Начало каждого периода должно быть позже предыдущего. Если время повторяется или идёт в обратном порядке, редактор покажет подсказку рядом с таблицей и заблокирует запись до исправления.",
        ),
        (
            "Архивы",
            "Вкладка пока пустая. Просмотр архивов ещё недоступен.",
        ),
        (
            "Сервисное инфо",
            "Вкладка показывает техническую версию ПО и дату его компиляции. Сведения читаются при подключении счётчика.",
        ),
        (
            "Протокол поверки",
            "На вкладке «Текущие значения» нажмите «Заполнить протокол». Проверьте данные прибора, заполните сведения о поверке, выберите класс точности 0,5 или 1 и укажите результаты четырёх проверок.\n\n"
            "Для каждого канала предусмотрено пять точек напряжения и четыре точки тока, мощности и периода. Слева можно выбрать любую точку. На точках напряжения выставьте указанную уставку и введите показание внешнего вольтметра в Uэт. На точках тока оставьте напряжение на Uном, выставляйте на ЭнИ 75 → 37,5 → 22,5 → 7,5 мВ и вводите Uэт и Tизм с частотомера. В двухканальном исполнении физически переключайте стенд на нужный канал.\n\n"
            "«Измерить» запускает усреднение для выбранной точки. Когда показания стабилизируются, усреднение останавливается автоматически и становится доступен «Замер». Если показания остались нестабильными, повторите измерение. Программа определяет, введён ли период в секундах или миллисекундах, по расчётному периоду точки и показывает единицу рядом с полем. Заполните поля и нажмите «Записать точку». К записанной точке можно вернуться и сохранить исправления.\n\n"
            "Когда все точки записаны, нажмите «Сформировать протокол», подтвердите действие и выберите имя и папку файла Excel. Если Excel блокирует сохранение, закройте файл и повторите попытку. После пересчёта итог P означает, что все четыре проверки пройдены и погрешности в допуске. В остальных случаях итог F.",
        ),
        (
            "Источник питания",
            "В окне поверки панель видна постоянно. На вкладке «Текущие значения» её можно показать или скрыть через «Настройки программы». Обе панели используют один выбранный COM-порт.\n\n"
            "При выборе порта программа автоматически считывает напряжение и состояние выхода. Введите уставку и нажмите «Задать». При вводе 1000 В и выше отправляется 999,9 В. Выход можно включить или выключить кнопкой. Включение требует подтверждения.",
        ),
        (
            "Чтение выгрузки EMIS",
            "В меню настроек выберите «Чтение выгрузки EMIS». Откройте выгрузку .emis. Внутренняя сборка ЭМИС открывает выгрузки автоматически. Счётчик для просмотра не требуется. Дата, время и текущий тариф показаны на момент выгрузки.",
        ),
        (
            "Обновления",
            "Проверка выполняется при запуске. Её также можно запустить вручную через «Настройки программы». Если есть новая версия, программа предложит открыть страницу релиза. Выберите архив под свою версию Windows.",
        ),
    ),
    "en": (
        (
            "Connection",
            "Connect the USB–RS-485 adapter and power the meter. Refresh the COM port list, select a port, and click Connect. The scan checks the entered address with different connection settings first, then scans addresses 1–254 for each baud rate and parity combination. You can cancel the scan.\n\n"
            "Enter a known Modbus address manually. Use Write to change the meter address, baud rate, or parity. Even parity is recommended. Connection status appears above the tabs. Once connected, the serial number and software version appear there as well. If automatic detection fails, select the channel count in the dialog or click Cancel to stop connecting.",
        ),
        (
            "Meter information",
            "Read or edit the serial number, manufacturer, meter type, metrological firmware version, and date. Editing and auto-fill become available after connecting. Enter 12 digits when editing the serial number. The app decodes the configuration encoded in series 977 serial numbers.\n\n"
            "For auto-fill, scan or enter the serial number, then press Enter or click Apply. The app synchronizes the clock with the PC and writes the meter details. The date field records when the serial number was entered. If the operation fails, some fields may already have been written.",
        ),
        (
            "Date and time",
            "This tab displays the meter clock. Set it manually or synchronize it with the PC.",
        ),
        (
            "Live readings",
            "This tab shows nominal values, energy, voltage, current, and power for the available channels. Nominal values are displayed as whole numbers. Live voltage, current, and power use four decimal places. Energy follows the meter's decimal setting. Absolute energy is the sum of the magnitudes of forward and reverse energy.\n\n"
            "Fill in protocol becomes available once the meter connects. Averaging is started within a verification point.",
        ),
        (
            "Device settings",
            "Set maximum current, sensitivity thresholds, the pulse output constant, and energy decimal places (0, 2, or 3). Enter maximum current in whole amperes. Set the pulse constant for each available channel. Selecting a value from a settings list writes it to the meter.\n\n"
            "Clearing accumulated energy readings requires a password and confirmation.",
        ),
        (
            "Tariff schedule",
            "Current tariff is calculated from the meter clock and the stored daily schedule. A dash is displayed if the schedule is empty or the data is unavailable.\n\n"
            "Click Configure schedule to read or edit periods for tariffs 1–4. New periods start at 00:00. Enter hours and minutes as digits in separate fields. Each period must start after the previous one. If a time is repeated or out of order, the editor shows an inline hint and disables Write schedule until you fix it.",
        ),
        (
            "Archives",
            "This tab is currently empty. Archive viewing is not available yet.",
        ),
        (
            "Service info",
            "The tab shows the technical firmware version and build date. The app reads them when the meter connects.",
        ),
        (
            "Verification report",
            "On Live readings, click Fill in protocol. Check the meter details, complete the report form, select accuracy class 0.5 or 1, and enter the outcomes of the four checks.\n\n"
            "Each channel has five voltage points and four current, power, and period points. Select any point from the list on the left. For voltage points, set the specified voltage and enter the external voltmeter reading in Uэт. For current points, keep the source at nominal voltage and set the EnI calibrator to 75 → 37.5 → 22.5 → 7.5 mV. Enter the external voltmeter reading in Uэт and the frequency counter period in Tизм. For a dual-channel meter, switch the bench connections to the channel being tested.\n\n"
            "Start averaging with «Измерить» (Measure). Once the readings stabilize, averaging stops automatically and «Замер» (Capture) becomes available. If the readings remain unstable, repeat the measurement. The app uses the expected period for the point to interpret seconds or milliseconds and displays the unit next to the field. Enter the required readings and save the point. You can return to a saved point and save corrections.\n\n"
            "After saving all points, select «Сформировать протокол» (Generate report), confirm, and choose a name and folder for the Excel file. If Excel locks the file, close it and retry. After recalculation, P indicates that all four checks passed and all measurement errors are within tolerance. Otherwise the result is F.",
        ),
        (
            "Voltage source",
            "The source panel is always visible in the verification window. On Live readings, show or hide it from the program settings menu. Both panels share the selected COM port.\n\n"
            "When you select the port, the app automatically reads the voltage and output state. Enter a setpoint and apply it. Values of 1000 V or higher are sent as 999.9 V. Use the output button to switch the output on or off. Switching it on requires confirmation.",
        ),
        (
            "Read EMIS export",
            "Use Read EMIS export in the program settings menu. Select the .emis export. The internal EMIS build opens exports automatically. No meter is required. The date, time, and current tariff reflect the moment of export.",
        ),
        (
            "Updates",
            "The app checks for updates at startup. You can also check manually from the program settings menu. When a new version is available, open its release page and choose the package for your Windows version.",
        ),
    ),
    "zh": (
        (
            "连接",
            "连接 USB–RS-485 转换器并给电表供电。刷新 COM 端口列表，选择端口并连接。程序先用不同通信参数检查输入的地址，再按波特率和校验方式的组合扫描 1–254。可取消搜索。\n\n"
            "已知 Modbus 地址时可直接输入。要修改电表地址、波特率或校验方式，请执行写入。建议使用偶校验。连接状态显示在选项卡上方。连接后，同一位置还会显示序列号和软件版本。若无法自动识别电表类型，请在弹窗中选择通道数，或点击「取消」停止连接。",
        ),
        (
            "电表信息",
            "可以读取或修改序列号、制造商、电表类型、计量固件版本和日期。连接后可以修改信息或使用自动填写。修改序列号时须输入 12 位数字。界面会解析 977 系列序列号中的配置信息。\n\n"
            "自动填写时，扫描或输入序列号，然后按 Enter 或点击应用。程序将电表时钟与电脑同步，并将序列号录入日期写入日期字段。如果操作失败，部分字段可能已写入。",
        ),
        (
            "日期和时间",
            "此选项卡显示电表日期和时间。可手动设置，也可与电脑同步。",
        ),
        (
            "实时读数",
            "显示各通道的额定值、电能、电压、电流和功率。额定值显示为整数，实时电压、电流和功率显示四位小数。电能小数位数采用电表设置。绝对电能为正向与反向电能绝对值之和。\n\n"
            "电表连接后即可打开检定记录。平均值采集在所选检定点内启动。",
        ),
        (
            "电表设置",
            "可设置最大电流、灵敏度阈值、脉冲输出常数和电能小数位数（0、2 或 3 位）。最大电流以整数安培输入。各可用通道可分别设置脉冲常数。从设置列表选择值后，程序会写入电表。\n\n"
            "清除累计电能读数需要密码和确认。",
        ),
        (
            "费率时段表",
            "当前费率根据电表时钟和已保存的每日时段表计算。时段表为空或数据不可用时显示「—」。\n\n"
            "打开时段设置可读取和编辑费率 1–4 的时段。新增时段默认为 00:00。小时和分钟分别输入数字。每个时段的开始时间必须晚于上一个时段。如果时间重复或顺序有误，界面会在表格旁提示，并停用写入按钮，直到修正为止。",
        ),
        (
            "档案",
            "此选项卡暂为空白，尚不能查看档案。",
        ),
        (
            "服务信息",
            "此选项卡显示技术固件版本和编译日期。连接电表时会读取这些信息。",
        ),
        (
            "检定记录",
            "在实时读数选项卡打开检定记录。核对电表信息，填写检定数据，选择 0.5 或 1 级准确度，并填写四项检查结果。\n\n"
            "每个通道有五个电压点和四个电流、功率与周期点。可从左侧列表选择任意检定点。电压点按提示设置电压，将外部电压表读数填入 Uэт。电流点保持电压源为额定电压，将 ЭнИ 校准器依次设置为 75、37.5、22.5、7.5 mV，填入外部电压表读数 Uэт 和频率计测得的周期 Tизм。双通道电表需将试验台接线切换至正在检定的通道。\n\n"
            "点击「Измерить」开始采集平均值。读数稳定后，程序自动停止采集，此时可点击「Замер」锁定平均值。如果读数仍不稳定，请重新测量。程序根据该检定点的预期周期判断输入值使用秒还是毫秒，并在输入框旁显示单位。填写所需读数后保存检定点。可以返回已保存的点，修改后重新保存。\n\n"
            "记录所有点后，点击「Сформировать протокол」，确认后选择 Excel 文件名和保存位置。若文件被 Excel 锁定，请关闭文件后重试。Excel 重新计算后，四项检查均通过且所有测量误差均在允许范围内时显示 P，否则显示 F。",
        ),
        (
            "电压源",
            "检定窗口始终显示电压源面板。实时读数选项卡中的面板可通过程序设置菜单显示或隐藏。两个面板共享所选 COM 端口。\n\n"
            "选择端口后，程序自动读取电压和输出状态。输入设定值并应用。输入 1000 V 或更高时，程序发送 999.9 V。可用按钮开启或关闭输出，开启输出需确认。",
        ),
        (
            "读取 EMIS 导出文件",
            "在程序设置菜单中选择「读取 EMIS 导出文件」。打开 .emis 导出文件。EMIS 内部版本会自动打开导出文件。无需连接电表。日期、时间和当前费率为导出时的记录。",
        ),
        (
            "更新",
            "程序启动时会检查更新，也可从程序设置菜单手动检查。发现新版本后可打开发布页面，选择适合当前 Windows 版本的压缩包。",
        ),
    ),
}
