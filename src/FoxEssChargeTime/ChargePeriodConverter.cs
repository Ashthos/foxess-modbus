using FoxEssChargeTime.Abstractions;
using FoxEssChargeTime.Models;

namespace FoxEssChargeTime
{
    public class ChargePeriodConverter : IChargePeriodConverter
    {
        public (ChargePeriod Period1, ChargePeriod Period2) ConvertFromSpan(Span<short> data)
        {
            return (new ChargePeriod
            {
                Enabled = data[0] == 1,
                Start = new TimeOnly(data[1] / 256, data[1] % 256),
                End = new TimeOnly(data[2] / 256, data[2] % 256)
            }, new ChargePeriod
            {
                Enabled = data[3] == 1,
                Start = new TimeOnly(data[4] / 256, data[4] % 256),
                End = new TimeOnly(data[5] / 256, data[5] % 256)
            });
        }

        public Span<short> ConvertToSpan(ChargePeriod period1, ChargePeriod period2)
        {
            var registers = new short[6];

            registers[0] = period1.Enabled ? (short)1 : (short)0;
            registers[1] = (short)(period1.Start.Hour * 256 + period1.Start.Minute);
            registers[2] = (short)(period1.End.Hour * 256 + period1.End.Minute);

            registers[3] = period2.Enabled ? (short)1 : (short)0;
            registers[4] = (short)(period2.Start.Hour * 256 + period2.Start.Minute);
            registers[5] = (short)(period2.End.Hour * 256 + period2.End.Minute);

            return new Span<short>(registers.ToArray());
        }
    }
}
