using FluentModbus;
using System.IO.Ports;
using System.Reflection;
using FoxEssChargeTime.Models;

namespace FoxEssChargeTime
{
    public static class ModbusRTUExtensions
    {
        public static void SetSerialPortOptions(this FluentModbus.ModbusRtuClient client, ModbusSettings settings)
        {
            var _field = client.GetType().GetField("_serialPort", BindingFlags.Instance | BindingFlags.NonPublic);
            if (_field != null)
            {
                var _value = _field.GetValue(client);
                if (_value != null)
                {
                    var sp = (ValueTuple<IModbusRtuSerialPort, bool>)_value;
                    if (sp.Item1 != null)
                    {
                        var modbusSerialPort = (ModbusRtuSerialPort)sp.Item1;

                        var serialPortField = typeof(ModbusRtuSerialPort).GetField("_serialPort",
                            BindingFlags.Instance | BindingFlags.NonPublic);

                        if (serialPortField != null)
                        {
                            var serialPortValue = serialPortField.GetValue(modbusSerialPort);

                            if (serialPortValue != null)
                            {
                                var serialPort = (SerialPort)serialPortValue;

                                serialPort.DtrEnable = settings.Dtr;
                                serialPort.RtsEnable = settings.Rts;
                            }
                        }
                    }
                }
            }
        }
    }
}
