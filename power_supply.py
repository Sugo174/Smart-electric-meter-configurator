from decimal import Decimal, InvalidOperation

from device import make_instrument


VOLTAGE_REGISTER = 0
OUTPUT_REGISTER = 4
VOLTAGE_SCALE = 10
MAX_VOLTAGE = Decimal("999.9")


def _exchange(port, slave, write=None):
    instrument = make_instrument(port, slave, 9600, "N")
    try:
        if write is not None:
            register, value = write
            instrument.write_register(register, value, functioncode=6)
        voltage = instrument.read_register(VOLTAGE_REGISTER, functioncode=3)
        output = instrument.read_register(OUTPUT_REGISTER, functioncode=3)
        return {"voltage_v": voltage / VOLTAGE_SCALE, "output_raw": output}
    finally:
        instrument.serial.close()


def read_power_supply(port: str, slave: int):
    """Читает напряжение и код состояния выхода источника."""
    return _exchange(port, slave)


def voltage_to_register(voltage_text: str) -> int:
    """Проверяет ввод и кодирует напряжение с шагом 0,1 В."""
    try:
        voltage = Decimal(voltage_text.strip().replace(",", "."))
    except InvalidOperation:
        raise ValueError("Invalid voltage") from None

    if not voltage.is_finite() or not 0 <= voltage <= MAX_VOLTAGE:
        raise ValueError("Voltage outside 0–999.9 V")

    if voltage != voltage.quantize(Decimal("0.1")):
        raise ValueError("Voltage must use 0.1 V increments")
    return int(voltage * VOLTAGE_SCALE)


def set_power_supply_voltage(port: str, slave: int, voltage_text: str):
    raw = voltage_to_register(voltage_text)
    return _exchange(port, slave, (VOLTAGE_REGISTER, raw))


def set_power_supply_output(port: str, slave: int, enabled: bool):
    if not isinstance(enabled, bool):
        raise ValueError("Output state must be on or off")
    state = int(enabled)
    result = _exchange(port, slave, (OUTPUT_REGISTER, state))
    if result["output_raw"] != state:
        raise RuntimeError("Power supply did not confirm the output state")
    return result
