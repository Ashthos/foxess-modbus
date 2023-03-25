using FoxEssChargeTime.Models;
using FoxEssChargeTimeApi.Dtos;

namespace FoxEssChargeTimeApi.Converters
{
    public class ChargeSettingConverter
    {
        public ChargeSetting FromPeriod(ChargePeriod data)
        {
            return new ChargeSetting
            {
                Enabled = data.Enabled,
                Start = data.Start.ToString(),
                End = data.End.ToString()
            };
        }

        public ChargePeriod? ToPeriod(ChargeSetting data)
        {
            if (TimeOnly.TryParse(data.Start, out var startTime) &&
                TimeOnly.TryParse(data.End, out var endTime))
            {
                return new ChargePeriod
                {
                    Enabled = data.Enabled,
                    Start = startTime,
                    End = endTime
                };
            }

            return null;
        }
    }
}
