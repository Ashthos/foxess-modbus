using System.IO.Ports;

namespace FoxEssChargeTime.Models
{
    public class ModbusSettings
    {
        public string SerialPort { get; set; }

        public int SerialBaud { get; set; }

        public SerialParity SerialParity { get; set; }

        public int SerialStopBits { get; set; }
        
        public int Address { get; set; }

        public int ReadTimeoutMs { get; set; }

        public int WriteTimeoutMs { get; set; }

        public ModbusEndian Endian { get; set; }

        public Handshake Handshake { get; set; }

        public bool Dtr { get; set; }

        public bool Rts { get; set; }
    }
}
