# ClimacellV4 - Domoticz Python Plugin
## Features
* Create the devices Meteo: Temp, THB, Rain, UV index, Visibility, Wind, Cloud cover,Precipitation type, Solar radiation
* Create the devices Air Quality: pm10, pm25, o3, no2,co, so2, status
* Create the devices Envt Risk: Road, Fire index
Get the meteo, air quality and environmental risks in realtime and update the device status in Domoticz
## Prerequisites
* Make sure that your Domoticz supports Python plugins (https://www.domoticz.com/wiki/Using_Python_plugins)
## Installation
1. Clone repository into your domoticz plugins folder
```
cd domoticz/plugins
git clone https://github.com/afer92/domotiz-plugin-climacellV4.git
```
2. Restart domoticz
3. Make sure that "Accept new Hardware Devices" is enabled in Domoticz settings
4. Go to "Hardware" page and add new item with type "Climacell (Weather Lookup) v4"
## Testing without Domoticz
1. Clone repository
```
cd scripts/tests
git clone https://github.com/afer92/domotiz-plugin-climacellV4.git
```
2. Edit TestCode.py
```
API_key = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' # Your api key from Climacell
LATITUDE = '47.111111' # Your location
LONGITUDE = '2.222222
```
3. Run test
```
python3 plugin.py
```
