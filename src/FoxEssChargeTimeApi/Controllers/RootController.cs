using FoxEssChargeTime.Abstractions;
using FoxEssChargeTimeApi.Dtos;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.ModelBinding;
using System.Net.Mime;
using FoxEssChargeTime.Models;
using FoxEssChargeTimeApi.Converters;

namespace FoxEssChargeTimeApi.Controllers
{
    [Route("v1/")]
    [ApiController]
    [Consumes(MediaTypeNames.Application.Json)]
    [Produces(MediaTypeNames.Application.Json)]
    public class RootController : ControllerBase
    {
        private readonly ILogger<RootController> _logger;
        private readonly IModbusReader _reader;
        private readonly IModbusWriter _writer;
        private readonly ChargeSettingConverter _converter;

        public RootController(ILogger<RootController> logger, IModbusReader reader, IModbusWriter writer, ChargeSettingConverter converter)
        {
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));
            _reader = reader ?? throw new ArgumentNullException(nameof(reader));
            _writer = writer ?? throw new ArgumentNullException(nameof(writer));
            _converter = converter ?? throw new ArgumentNullException(nameof(converter));
        }

        [HttpGet(Name = "GetChargeSettings")]
        [ProducesResponseType(typeof(IEnumerable<ChargeSetting>), StatusCodes.Status200OK)]
        [ProducesResponseType(StatusCodes.Status500InternalServerError)]
        public IActionResult Get()
        {
            if (_reader.TryGetCurrentSetting(out var results))
            {
                var dto = new[]
                {
                    _converter.FromPeriod(results.Period1),
                    _converter.FromPeriod(results.Period2),
                };

                return Ok(dto);
            }

            return StatusCode(StatusCodes.Status500InternalServerError);
        }

        [HttpPut(Name = "SetChargeSettings")]
        [ProducesResponseType(typeof(IEnumerable<ChargeSetting>), StatusCodes.Status200OK)]
        [ProducesResponseType(StatusCodes.Status400BadRequest)]
        [ProducesResponseType(StatusCodes.Status500InternalServerError)]
        public IActionResult Put([FromBody] ChargeSetting body)
        {
            if (!ModelState.IsValid)
            {
                var errors = ModelState.SelectMany(x => x.Value != null ? x.Value.Errors : new ModelErrorCollection()).Select(x => x.ErrorMessage);
                return BadRequest(errors);
            }

            var newSetting = _converter.ToPeriod(body);

            if (newSetting == null)
            {
                return BadRequest();
            }

            if (_writer.TryWriteSettings(newSetting, ChargePeriod.Blank))
            {
                // Wait 1 second to allow registers to update for reading.
                Thread.Sleep(1000);

                if (_reader.TryGetCurrentSetting(out var results))
                {
                    var dto = new[]
                    {
                        _converter.FromPeriod(results.Period1),
                        _converter.FromPeriod(results.Period2),
                    };

                    return Ok(dto);
                }
            }

            return StatusCode(StatusCodes.Status500InternalServerError);
        }
    }
}