namespace FoxEssChargeTime.Models
{
    public class ChargePeriod
    {
        public static ChargePeriod Blank = new() { Enabled = false, Start = TimeOnly.MinValue, End = TimeOnly.MinValue };

        public bool Enabled { get; set; }

        public TimeOnly Start { get; set; }

        public TimeOnly End { get; set; }
    }
}