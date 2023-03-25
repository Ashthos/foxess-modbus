using FoxEssChargeTime.Models;

namespace FoxEssChargeTime.Abstractions
{
    public interface IChargePeriodConverter
    {
        (ChargePeriod Period1, ChargePeriod Period2) ConvertFromSpan(Span<short> data);

        Span<short> ConvertToSpan(ChargePeriod period1, ChargePeriod period2);
    }
}