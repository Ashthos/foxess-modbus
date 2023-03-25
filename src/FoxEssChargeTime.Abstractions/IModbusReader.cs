using FoxEssChargeTime.Models;

namespace FoxEssChargeTime.Abstractions
{
    public interface IModbusReader
    {
        bool TryGetCurrentSetting(out (ChargePeriod Period1, ChargePeriod Period2) values);
    }
}