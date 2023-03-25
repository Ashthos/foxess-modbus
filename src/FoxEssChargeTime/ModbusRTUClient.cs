using FoxEssChargeTime.Models;
using FoxEssChargeTime.Abstractions;
using Microsoft.Extensions.Logging;

namespace FoxEssChargeTime
{
    public class ModbusRTUClient : IModbusReader, IModbusWriter
    {
        private readonly ModbusSettings _settings;
        private readonly InverterSettings _inverterSettings;
        private readonly IChargePeriodConverter _chargePeriodConverter;
        private readonly ILogger<ModbusRTUClient> _logger;
        private readonly IFoxEssModbus _foxEssModbus;

        public ModbusRTUClient(ModbusSettings settings, InverterSettings inverterSettings, IChargePeriodConverter chargePeriodConverter, ILogger<ModbusRTUClient> logger, IFoxEssModbus foxEssModbus)
        {
            _settings = settings ?? throw new ArgumentNullException(nameof(settings));
            _inverterSettings = inverterSettings ?? throw new ArgumentNullException(nameof(inverterSettings));
            _chargePeriodConverter = chargePeriodConverter ?? throw new ArgumentNullException(nameof(chargePeriodConverter));
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));
            _foxEssModbus = foxEssModbus ?? throw new ArgumentNullException(nameof(foxEssModbus));
        }
        
        public bool TryGetCurrentSetting(out (ChargePeriod Period1, ChargePeriod Period2) result)
        {
            var readCount = _inverterSettings.RegisterCount;

            using (_foxEssModbus)
            {
                var values = _foxEssModbus.ReadInputRegisters(_settings.Address, _inverterSettings.ChargePeriodBaseAddress, readCount);
                var decoded = _chargePeriodConverter.ConvertFromSpan(values);

                result = decoded;
                return true;
            }
            
            result = (ChargePeriod.Blank, ChargePeriod.Blank);
            return false;
        }

        public bool TryWriteSettings(ChargePeriod period1, ChargePeriod period2)
        {
            var registers = _chargePeriodConverter.ConvertToSpan(period1, period2);

            using (_foxEssModbus)
            {
                _foxEssModbus.WriteMultipleRegisters(_settings.Address, _inverterSettings.ChargePeriodBaseAddress,
                    registers.ToArray());
            }
            
            return true;
        }
    }
}
