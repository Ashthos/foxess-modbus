# FoxEssChargeTimeAPI

.netcore application to connect via Modbus RS485 to the FoxEss H1-5.0-E Inverter. Focused on allowing updating of the Charge Times.

## Build - In powershell

From the project root directory -

linux:

`dotnet publish --configuration Release --runtime Linux-x64`

Windows:

`dotnet publish --configuration Release --runtime win-x64`

The required files will be present in the `src\FoxEssChargeTimeApi\bin\Release\net7.0\<runtime>\publish` folder

## Configuration

edit the `appsettings.json` to adjust connection settings to the Modbus RS485 device connected to the FoxEss inverter.

### Primary settings

*serialPort* - the name of the serial port to use, on Windows this is often `COM4`, or on Linux `/dev/ttyUSB0`

*urls* - Adjust the port you want the API exposed on, default port 80.

## Run

This API runs via the dotnet command line. The dotnet 7.0 runtime must be installed on the platform you wish to run this on.

use the command line `dotnet FoxEssChargeTimeApi.dll` to start the API service. 

## Usage - Raw HTTP Requests

Use an HTTP client to call the API. 

```
GET /v1 HTTP/1.1
Host: localhost
Accept: application/json

###

PUT /v1 HTTP/1.1
Host: localhost
Content-Type: application/json
Accept: application/json

{
    "enabled": true,
    "start": "00:31",
    "end": "04:29"
}

###
```

## API Response

Successful responses from either the GET or PUT endpoint are the same and look similar to

```
HTTP/1.1 200 OK
Connection: close
Content-Type: application/json; charset=utf-8
Date: Fri, 24 Mar 2023 23:30:10 GMT
Server: Kestrel
Transfer-Encoding: chunked

[
  {
    "enabled": true,
    "start": "00:31",
    "end": "04:29"
  },
  {
    "enabled": false,
    "start": "00:00",
    "end": "00:00"
  }
]
```

## Usage - Home Assistant

In home assistant `configuration.yaml` add an entry for the API under the `rest_command` section.

```
rest_command:
  set_charge_time:
    url: http://192.168.1.205/v1
    method: put
    headers:
      accept: "application/json"
    payload: '{ "enabled": true, "start": "{{ start_time }}", "end": "{{ end_time }}" }'
    content_type: 'application/json'
```

(Replace the `192.168.1.205` IP with the IP or hostname of the container or Computer where the API is running)

Call the API as per the HA guidance (https://www.home-assistant.io/integrations/rest_command/):

```
service: rest_command.set_charge_time
data: { start_time: "00:32", end_time: "04:28" }
```

## Design decisions

This API has been written to work with the developer's specific scenario. Which is:

- FoxEss H1-5.0-E Inverter.
- Solar Pannels and Battery.
- All IoT devices run locally, with no cloud connections allowed.
- A working LAN connection on the inverter that is used for retrieval of Modbus data.
- An electricity tariff which has a two distinct periods of rate. Cheap: 00:30 - 04:30, Expensive: 04:30 - 00:30.
- A USB -> RS485 device connected to the serial port of the Inverter.
- A Ubuntu 22:04 container running on Proxmox which has the USB port passed through to it. Dotnet Runtime 7 has been installed to the container.

As the LAN port on the inverter still works for collecting modbus data, the serial connection is only required to set the Charge period.

Only one charge period is required (during the cheap rate period) and the second period is always disabled and set to "00:00".

Fully charging the battery during the cheap rate to 100% is often inefficient if the following day's solar is to be wasted because the 
battery is too full to absorb excess solar power.

Using a Home Assistant solar forecasting service (Solcast), and a Python script to calculate the number of minutes of charge the battery 
needs to best use the next days, this API is called if the battery is not required to be 100% filled. The python script is run via an automation
just prior to the cheap tariff start time (around 00:25). The result of the script is then used as an input to a HTTP rest call to the API.

As a fail safe (in case the script fails to run correctly at the next invocation), the default charge times (00:30 - 04:30) are always re-written to
the inverter just after the cheap rate period ends. This is run via an automation and ensures that the battery will never be empty because
an issue with Home assistant means the charge times are not correctly calculated and a previous short charge time erroneously persists.

Calling the GET endpoint can be used to populate data into Home Assistant, I do not do this as I don't need to see this data.

## Limitations

- Doesn't attempt to replicate any of the Modbus data retrieval functionality already available in Home Assistant
- Is written to work with a USB Modbus adapter, I don't have a TCP/IP adapter to test for a TCP version
- Only sets one charge period
- Sometimes when the write has happened the returned values from the inverter still represent the pre-updated values. Subsequent calls to
the GET endpoint will correctly return the updated values.
- The API has no authentication and only very basic validation. Do NOT expose this API to the internet.
- Specifically designed to work with the FoxEss H1 inverter data format, unlikely to work with other inverter brands.

## Other considerations

- API may work with other classes of FoxEss inverters (H5?), the registers and connection properties can be customised in the `appsettings.json` file.
- The modbus library this code is based on (FluentModbus) does support TCP connections, but as I don't have a TCP device to test against no 
implementation has been done for TCP.
- It may be possible to alter the inverter's work-mode in a similar manner to the charge periods. This has not been tried and is not a personal 
requirement.
- This small, specalised component should be simple to integrate into a larger system of components. Large 'do everything' systems rarely cater for all the edge cases.

## Disclaimer

The developer takes no responsibility for any damage to hardware or loss or functionality due to this software's use. 