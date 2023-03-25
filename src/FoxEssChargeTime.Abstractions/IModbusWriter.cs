using FoxEssChargeTime.Models;

namespace FoxEssChargeTime.Abstractions;

public interface IModbusWriter
{
    bool TryWriteSettings(ChargePeriod period1,  ChargePeriod period2);
}