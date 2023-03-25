namespace FoxEssChargeTime.Abstractions
{
    public interface IFoxEssModbus : IDisposable
    {
        Span<short> ReadInputRegisters(int unitIdentifier, int startingAddress, int count);

        void WriteMultipleRegisters(int unitIdentifier, int startingAddress, short[] dataset);
    }
}
