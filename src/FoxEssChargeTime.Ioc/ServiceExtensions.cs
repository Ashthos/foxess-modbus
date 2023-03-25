using FoxEssChargeTime.Abstractions;
using FoxEssChargeTime.Models;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Options;

namespace FoxEssChargeTime.Ioc
{
    public static class ServiceExtensions
    {
        public static IServiceCollection RegisterServices(this IServiceCollection services)
        {
            services.AddTransient<IModbusReader, ModbusRTUClient>();
            services.AddTransient<IModbusWriter, ModbusRTUClient>();
            services.AddTransient<IFoxEssModbus, FoxEssModbus>();
            services.AddTransient<IChargePeriodConverter, ChargePeriodConverter>();

            return services;
        }

        public static IServiceCollection RegisterAppSettings(this IServiceCollection services)
        {
            services.AddOptions<ModbusSettings>()
                .BindConfiguration("modbus")
                .ValidateDataAnnotations();
            services.AddSingleton(resolver => resolver.GetRequiredService<IOptions<ModbusSettings>>().Value);

            services.AddOptions<InverterSettings>()
                .BindConfiguration("inverter")
                .ValidateDataAnnotations();
            services.AddSingleton(resolver => resolver.GetRequiredService<IOptions<InverterSettings>>().Value);


            return services;
        }
    }
}