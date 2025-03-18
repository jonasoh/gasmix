import minimalmodbus
from pymodbus.client import ModbusTcpClient, ModbusSerialClient
from pymodbus.exceptions import ModbusException


# minimalmodbus is nice to work with but lacks tcp support,
# so we use it for serial but pymodbus for tcp
class BlueVCount(minimalmodbus.Instrument):
    def get_vol(self):
        try:
            return self.read_float(1, byteorder=minimalmodbus.BYTEORDER_LITTLE)
        except minimalmodbus.ModbusException:
            return float("nan")

    def get_temp(self):
        try:
            return self.read_float(9, byteorder=minimalmodbus.BYTEORDER_LITTLE)
        except minimalmodbus.ModbusException:
            return float("nan")

    def get_pressure(self):
        try:
            return self.read_float(5, byteorder=minimalmodbus.BYTEORDER_LITTLE)
        except minimalmodbus.ModbusException:
            return float("nan")


# return 'U' for unknown values to be compatible with rrdtool
class BlueVary(ModbusTcpClient):
    def check_connection(self):
        if not self.connected:
            self.connect()

    def get_co2(self):
        """CO2 sensor is always channel 1."""
        self.check_connection()
        try:
            val = self.read_holding_registers(0, 2, slave=2)
            return self.convert_from_registers(
                [val.registers[1], val.registers[0]], data_type=self.DATATYPE.FLOAT32
            )
        except:
            return float("nan")

    def get_h2(self):
        """Assume a H2 sensor on channel 2."""
        self.check_connection()
        try:
            val = self.read_holding_registers(0, 2, slave=3)
            return self.convert_from_registers(
                [val.registers[1], val.registers[0]], data_type=self.DATATYPE.FLOAT32
            )
        except:
            return float("nan")

    def get_humidity(self):
        """Absolute humidity"""
        self.check_connection()
        try:
            val = self.read_holding_registers(0, 2, slave=4)
            return self.convert_from_registers(
                [val.registers[1], val.registers[0]], data_type=self.DATATYPE.FLOAT32
            )
        except:
            return float("nan")


# bluevcount = BlueVCount('/dev/tty.usbserial-AU05SI5H', slaveaddress=1)
# bluevcount.serial.baudrate = 38400
# bluevcount.serial.stopbits = 2

# bluevary = BlueVary('/dev/tty.usbserial-AU051E3B', slaveaddress=1)
# bluevary.serial.baudrate = 19200
# bluevary.serial.stopbits = 1

# bluevary = BlueVary('192.168.10.250')
# bluevary.connect()
