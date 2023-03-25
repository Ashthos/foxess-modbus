using System.IO.Ports;
using FluentModbus;
using FoxEssChargeTime.Abstractions;
using FoxEssChargeTime.Models;
using Microsoft.Extensions.Logging;

namespace FoxEssChargeTime
{
    public class FoxEssModbus : IFoxEssModbus
    {
        private readonly ModbusSettings _settings;
        private readonly InverterSettings _inverterSettings;
        private readonly ILogger<FoxEssModbus> _logger;

        private ModbusRtuClient? _client;

        public FoxEssModbus(ModbusSettings settings, InverterSettings inverterSettings, ILogger<FoxEssModbus> logger)
        {
            _settings = settings ?? throw new ArgumentNullException(nameof(settings));
            _inverterSettings = inverterSettings ?? throw new ArgumentNullException(nameof(inverterSettings));
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));
        }

        private bool Connect()
        {
            var parity = Parity.None;

            switch (_settings.SerialParity)
            {
                case SerialParity.None:
                    parity = Parity.None;
                    break;

                case SerialParity.Even:
                    parity = Parity.Even;
                    break;

                case SerialParity.Odd:
                    parity = Parity.Odd;
                    break;
            }

            var stopBits = StopBits.None;

            switch (_settings.SerialStopBits)
            {
                case 0:
                    stopBits = StopBits.None;
                    break;

                case 1:
                    stopBits = StopBits.One;
                    break;

                case 2:
                    stopBits = StopBits.Two;
                    break;
            }

            _logger.LogInformation($"Serial Port: {_settings.SerialPort}, Baud: {_settings.SerialBaud}, Parity: {parity}, StopBits: {stopBits}, Timeout: r:{_settings.ReadTimeoutMs}, w:{_settings.WriteTimeoutMs}, Handshake: {_settings.Handshake}");

            // use custom COM port settings:
            _client = new ModbusRtuClient
            {
                BaudRate = _settings.SerialBaud,
                Parity = parity,
                StopBits = stopBits,
                Handshake = _settings.Handshake,
                ReadTimeout = _settings.ReadTimeoutMs,
                WriteTimeout = _settings.WriteTimeoutMs
            };
            var endian = ModbusEndianness.BigEndian;
            switch (_settings.Endian)
            {
                case ModbusEndian.Big:
                    endian = ModbusEndianness.BigEndian;
                    break;
                case ModbusEndian.Little:
                    endian = ModbusEndianness.LittleEndian;
                    break;
            }
            _logger.LogInformation($"Endianness: {endian}");

            _client.Connect(_settings.SerialPort, endian);

            if (!_client.IsConnected)
            {
                _client.Close();

                _logger.LogError("Port not connected after connect request.");
                return false;
            }

            // Attempt to set DTR for serial port
            _logger.LogInformation($"Setting Dtr: {_settings.Dtr}, Rts: {_settings.Rts}");
            _client.SetSerialPortOptions(_settings);

            return true;
        }

        public void Dispose()
        {
            if (_client != null)
            {
                if (_client.IsConnected)
                {
                    _client.Close();
                }
                _client.Dispose();
            }
        }

        public Span<short> ReadInputRegisters(int unitIdentifier, int startingAddress, int count)
        {
            if (!Connect())
            {
                return null;
            }

            var readCount = _inverterSettings.RegisterCount;

            if (_client != null)
            {
                try
                {
                    _logger.LogInformation($"Read Input Registers FC4 - Identifier: {_settings.Address}, Register: {_inverterSettings.ChargePeriodBaseAddress}, Count: {readCount}");

                    return _client.ReadInputRegisters<short>(_settings.Address, _inverterSettings.ChargePeriodBaseAddress, readCount);
                }
                catch (Exception ex)
                {
                    _logger.LogCritical(ex, "Failed during ReadInputRegisters operation.");
                }
            }

            return null;
        }

        public void WriteMultipleRegisters(int unitIdentifier, int startingAddress, short[] dataset)
        {
            if (!Connect())
            {
                return;
            }

            if (_client != null)
            {
                try
                {
                    _client.WriteMultipleRegisters(unitIdentifier, startingAddress, dataset);
                }
                catch (Exception ex)
                {
                    _logger.LogCritical(ex, "Failed during WriteMultipleRegisters operation.");
                }
            }
        }
    }
}
