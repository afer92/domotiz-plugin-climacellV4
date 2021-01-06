# Basic Python Plugin Example
#
# Author: Alain Meunier
#
#!/usr/bin/python
"""
<plugin key="Climacell" name="Climacell (Weather Lookup) v4" author="Alain Meunier" version="0.0.2" wikilink="http://www.domoticz.com/wiki/plugins/plugin.html" externallink="https://www.climacell.com/">
    <description>
    <h2>Plugin Météo Climacell V4</h2><br/>
        Devices will be created in the Devices Tab only and will be made active.<br/><br/>
    <h3>Features</h3>
    <ul style="list-style-type:square">
        <li>Create the devices Meteo: Temp, THB, Rain, UV index, Visibility, Wind, Cloud cover,Precipitation type, Solar radiation</li>
        <li>Create the devices Air Quality: pm10, pm25, o3, no2,co, so2, status</li>
        <li>Create the devices Envt Risk: Road, Fire index</li>
        <li>Get the meteo, air quality and environmental risks in realtime and update the device status in Domoticz</li>
    </ul>
    <h3>Configuration</h3>
        Configuration options...
    </description>
    <params>
        <param field="Mode1" label="Clé d'API:" width="200px" required="true" default=""/>
        <param field="Mode2" label="Localisation : latitude,longitude" width="200px" required="true" default=""/>
        <param field="Mode3" label="Update Meteo every x seconds" width="200px" required="true" default="300"/>
        <param field="Mode4" label="Update Air Quality every x seconds" width="200px" required="true" default="1800"/>
        <param field="Mode5" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal"  default="true" />
            </options>
        </param>
    </params>
</plugin>
"""


import sys
sys.path.append('/home/pi/.local/lib/python3.7/site-packages')


import Domoticz
import datetime
import os
import time
from datetime import datetime
from datetime import timedelta
import pytz


import requests

import json
import string

API_BASE_REALTIME_URL = 'https://data.climacell.co/v4/timelines?'

thumidity_status = {
        "3": (60, 100),
        "2": (40, 60),
        "1": (30, 40),
        "0": (0, 30)
        }

tprecipitation_type = {
    0: "",
    1: "Rain",
    2: "Snow",
    3: "Freezing Rain",
    4: "Ice Pellets"}

#   List of weather conditions
#   0 - Stable
#   1 - Clear/Sunny
#   2 - Cloudy/Rain
#   3 - Not stable
#   4 - Thunderstorm
#   5 - Unknown
tweather_code = {
    4201:   ("Heavy Rain", 4),
    4001:   ("Rain", 2),
    4200:   ("Light Rain", 2),
    6201:   ("Heavy Freezing Rain", 4),
    6001:   ("Freezing Rain", 4),
    6200:   ("Light Freezing Rain", 3),
    6000:   ("Freezing Drizzle", 3),
    4000:   ("Drizzle", 2),
    7101:   ("Heavy Ice Pellets", 4),
    7000:   ("Ice Pellets", 4),
    7102:   ("Light Ice Pellets", 4),
    5101:   ("Heavy Snow", 4),
    5000:   ("Snow", 4),
    5100:   ("Light Snow", 3),
    5001:   ("Flurries", 3),
    8000:   ("Thunderstorm", 4),
    2100:   ("Light Fog", 3),
    2000:   ("Fog", 3),
    1001:   ("Cloudy", 3),
    1102:   ("Mostly Cloudy", 3),
    1101:   ("Partly Cloudy", 2),
    1100:   ("Mostly Clear", 2),
    1000:   ("Clear, Sunny", 1)}

tepa_health_concern = {
    0: "Good",
    1: "Moderate",
    2: "Unhealthy for Sensitive Groups",
    3: "Unhealthy",
    4: "Very Unhealthy",
    5: "Hazardous"}

quadrants = ["NNE", "NE", "ENE", "E", "ESE", "SE",
             "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]

icons = {
    "Climacell_air_quality": "Climacell_air_quality icons.zip",
    "Climacell_co2": "Climacell_co2 icons.zip",
    "Climacell_co": "Climacell_co icons.zip",
    "Climacell_so2": "Climacell_so2 icons.zip",
    "Climacell_no2": "Climacell_no2 icons.zip",
    "Climacell_o3": "Climacell_o3 icons.zip",
    "Climacell_pm10": "Climacell_pm10 icons.zip",
    "Climacell_pm25": "Climacell_pm25 icons.zip",
    "Climacell_cloud_cover": "Climacell_cloud_cover icons.zip"}

# fields to collect
tcsMeteoFields = [
                  u'temperature',
                  u'temperatureApparent',
                  u'dewPoint',
                  u'humidity',
                  u'windSpeed',
                  u'windDirection',
                  u'windGust',
                  u'pressureSurfaceLevel',
                  u'pressureSeaLevel',
                  u'precipitationIntensity',
                  u'precipitationProbability',
                  u'precipitationType',
                  u'solarGHI',
                  u'visibility',
                  u'cloudCover',
                  u'cloudBase',
                  u'cloudCeiling',
                  u'weatherCode'
                  ]

tcsAirQualityFields = [
                u'particulateMatter25',
                u'particulateMatter10',
                u'pollutantO3',
                u'pollutantNO2',
                u'pollutantCO',
                u'pollutantSO2',
                u'epaIndex',
                u'epaPrimaryPollutant',
                u'epaHealthConcern'
                ]


class BasePlugin:

    def __init__(self):
        self.enabled = False
        self.debug = False
        self.started = False
        self.tsBeginPolling = datetime.now()    # datetime beginning polling
        self.tsEndPolling = datetime.now()  # datetime end polling
        self.API_key = None
        self.Latitude = None
        self.Longitude = None
        self.runCounterUpdateMeteo = 0
        self.runCounterUpdateAirQuality = 0
        self.UpdateCycleMeteo = 0
        self.UpdateCycleAirQuality = 0
        return

    def debugMessage(self, szMessage):
        if self.debug:
            ts = time.time()
            timestamp = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
            Domoticz.Debug(szMessage + " at : " + str(timestamp))

    def statusMessage(self, szMessage):
        if self.debug:
            ts = time.time()
            timestamp = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
            Domoticz.Status(szMessage + " at : " + str(timestamp))

    def errorMessage(self, szMessage):
        ts = time.time()
        timestamp = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        Domoticz.Error(szMessage + " at : " + str(timestamp))

    def get_humidity_status(self, humidity):
        global thumidity_status
        humidity_status = "2"
        for key, levels in thumidity_status.items():
            if humidity > levels[0] and humidity <= levels[1]:
                humidity_status = key
                break
        return humidity_status

    def get_precipitation_type(self, precipitation_type):
        global tprecipitation_type
        szprecipitation_type = ""
        for key, precipitation_types in tprecipitation_type.items():
            if key == precipitation_type:
                szprecipitation_type = precipitation_types
                break
        return szprecipitation_type

    def get_weather_condition(self, weather_code):
        global tweather_code
        weather_condition = 5
        weather_szcondition = "unkbown"
        for key, weather_conditions in tweather_code.items():
            if key == weather_code:
                weather_szcondition = weather_conditions[0]
                weather_condition = weather_conditions[1]
                break
        return {'weather_condition': weather_condition, 'weather_szcondition': weather_szcondition}

    def get_epa_health_concern(self, epa_health_concern):
        global tepa_health_concern
        szepa_health_concern = ""
        for key, epa_health_concerns in tepa_health_concern.items():
            if key == epa_health_concern:
                szepa_health_concern = epa_health_concerns
                break
        return szepa_health_concern

    def get_quadrants(self, degrees):
        global quadrants
        if degrees is None:
            return "no wind"
        if degrees > 348.75 or degrees <= 11.25:
            return "N"
        else:
            index = int((degrees - 11.25) / 22.5)
            return quadrants[index]

    def get_climacell_data(self, tFields, comment):

        tdataVals = []  # data table
        # build Url
        requestUrl = API_BASE_REALTIME_URL + "location=" + self.Latitude + "," + self.Longitude
        requestUrl = requestUrl + "&fields=" + u",".join(tFields)
        local_tz = pytz.timezone('Europe/Paris')
        target_tz = pytz.timezone('UTC')
        ts = time.time()+120
        endTime = datetime.fromtimestamp(ts)
        endTime_local = local_tz.localize(endTime)
        endTime_utc = target_tz.normalize(endTime_local)
        requestUrl = requestUrl + "&endTime=" + endTime_utc.strftime('%Y-%m-%dT%H:%M:%S') + "Z&timesteps=1m"
        requestUrl = requestUrl + "&apikey=" + self.API_key
        #  send request
        try:
            r = requests.get(requestUrl, timeout=(2, 5))
        except requests.ConnectionError as e:
            self.errorMessage(comment + " not available : " + "connection error " + str(e))
            return (False, None)
        except requests.Timeout as e:
            self.errorMessage(comment + " not available : " + "timeout error" + str(e))
            return (False, None)
        except requests.RequestException as e:
            self.errorMessage(comment + " not available : " + "general error" + str(e))
            return (False, None)
        try:
            rresult = r.json()
        except Exception as e:
            self.errorMessage(comment + " not available : " + e.message + " doc : " + e.__doc__)
            return (False, None)
        if r.status_code != 200 and r.status_code != 206:
            self.errorMessage(comment + " not available : status_code = " + str(r.status_code))
            return (False, None)

        #  validate data structure
        if u'data' not in rresult.keys():
            self.errorMessage(comment + " : No data in response")
            return (False, None)

        data = rresult[u'data']
        if u'timelines' not in data.keys():
            self.errorMessage(comment + " : No timelines in data")
            return (False, None)
        timelines = data['timelines']

        for timeline in timelines:
            for key, value in timeline.items():
                if key == u'intervals':
                    for interval in value:
                        if u'values' not in interval.keys():
                            self.errorMessage(comment + " : No values in interval")
                            continue
                        if u'startTime' not in interval.keys():
                            self.errorMessage(comment + " : No startTime in interval")
                            continue
                        vals = {}
                        vals[u'startTime'] = interval['startTime']
                        for key1, value1 in interval['values'].items():
                            vals[key1] = value1
                            Domoticz.Debug(u'{} {}: {}'.format(key, key1, value1))
                        tdataVals.append(vals)
        if len(tdataVals) > 0:
            return (True, tdataVals)
        else:
            return (False, None)

    def onStart(self):
        global icons
        Domoticz.Debug("onStart called - Begin")
        Domoticz.Debugging(0)
        self.debug = False
        if Parameters["Mode5"] == "Debug":
            Domoticz.Debugging(1)
            self.debug = True

        # load custom images
        for key, value in icons.items():
            if key not in Images:
                Domoticz.Image(Filename=value).Create()
                Domoticz.Debug("Added icon: " + key + " from file " + value)
            else:
                Domoticz.Debug("Icon " + str(Images[key].ID) + " " + Images[key].Name)
        Domoticz.Debug("Number of icons loaded = " + str(len(Images)))
        for image in Images:
            Domoticz.Debug("Icon " + str(Images[image].ID) + " " + Images[image].Name + " " + Images[image].Base)

        if (len(Devices) == 0):
            Domoticz.Device(Name="Temp", Unit=1, TypeName="Temperature", Used=1).Create()
            Domoticz.Device(Name="THB", Unit=2, TypeName="Temp+Hum+Baro", Used=1).Create()
            Domoticz.Device(Name="Rain", Unit=3, Type=85, Subtype=113, Used=1).Create()   # Type 85 rain, Subtype 0x71 RAINByRate CF Darksky
            Domoticz.Device(Name="UVIndex", Unit=4, TypeName="UV", Used=1).Create()
            Domoticz.Device(Name="Visibility", Unit=5, TypeName="Visibility", Used=1).Create()
            Domoticz.Device(Name="Wind", Unit=6, TypeName="Wind+Temp+Chill", Used=1).Create()
            Domoticz.Device(Name="Cloud %", Unit=7, Type=243, Subtype=31, Options={"Custom": "1;%"},  Used=1).Create()
            Domoticz.Device(Name="Precipitation Type", Unit=8, TypeName="Text", Used=1).Create()
            Domoticz.Device(Name="Solar Radiation", Unit=9, TypeName="Solar Radiation", Used=1).Create()
            Domoticz.Device(Name="pm10", Unit=10, Type=243, Subtype=31, Options={"Custom": "1;ug/m3"}, Used=1).Create()
            Domoticz.Device(Name="pm25", Unit=11, Type=243, Subtype=31, Options={"Custom": "1;ug/m3"}, Used=1).Create()
            Domoticz.Device(Name="o3", Unit=12, Type=243, Subtype=31, Options={"Custom": "1;ppb"}, Used=1).Create()
            Domoticz.Device(Name="no2", Unit=13, Type=243, Subtype=31, Options={"Custom": "1;ppb"}, Used=1).Create()
            Domoticz.Device(Name="co", Unit=14, Type=243, Subtype=31, Options={"Custom": "1;ppm"}, Used=1).Create()
            Domoticz.Device(Name="so2", Unit=15, Type=243, Subtype=31, Options={"Custom": "1;ppb"}, Used=1).Create()
            Domoticz.Device(Name="Air Quality Status", Unit=16, Type=243, Subtype=31, Options={"Custom": "1;"}, Used=1).Create()
            Domoticz.Device(Name="Observation_Time", Unit=17, TypeName="Text", Used=1).Create()
            Domoticz.Status("Device created.")
        DumpConfigToLog()
        Domoticz.Heartbeat(10)
        self.API_key = Parameters["Mode1"]
        Localisation = Parameters["Mode2"]
        x = Localisation.split(",")
        self.Latitude = x[0]
        self.Longitude = x[1]
        self.runCounterUpdateMeteo = 1
        self.runCounterUpdateAirQuality = 1
        self.UpdateCycleMeteo = int(Parameters["Mode3"])
        self.UpdateCycleAirQuality = int(Parameters["Mode4"])

        UpdateDevice(7, Image=Images["Climacell_cloud_cover"].ID)
        UpdateDevice(10, Image=Images["Climacell_pm10"].ID)
        UpdateDevice(11, Image=Images["Climacell_pm25"].ID)
        UpdateDevice(12, Image=Images["Climacell_o3"].ID)
        UpdateDevice(13, Image=Images["Climacell_no2"].ID)
        UpdateDevice(14, Image=Images["Climacell_co"].ID)
        UpdateDevice(15, Image=Images["Climacell_so2"].ID)
        UpdateDevice(16, Image=Images["Climacell_air_quality"].ID)

        self.started = True

        Domoticz.Debug("onStart called - End")

    def onStop(self):
        Domoticz.Debug("onStop called - Begin")
        Domoticz.Debug("onStop called - End")

    def onConnect(self, Connection, Status, Description):
        Domoticz.Debug("onConnect called - Begin")
        Domoticz.Debug("onConnect called - End")

    def onMessage(self, Connection, Data):
        Domoticz.Debug("onMessage called - Begin " + Connection.Name + ": " + str(Data))
        Domoticz.Debug("onMessage called - End")

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level)+" H= "+str(Hue) + " - Begin")
        Domoticz.Debug("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level)+" H= "+str(Hue) + " - End")

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Debug("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Debug("onDisconnect called for connection '"+Connection.Name+"'.")

    def onHeartbeat(self):

        Domoticz.Debug("onHeartBeat called - Begin")
        if self.started is False:
            Domoticz.Debug("onHeartBeat called - Plugin not started")
            Domoticz.Debug("onHeartBeat called - End")
            return
        Domoticz.Debug("Climacell v4 Meteo Polling in " + str(self.runCounterUpdateMeteo-1) + " heartbeats.")
        self.runCounterUpdateMeteo = self.runCounterUpdateMeteo - 1
        while self.runCounterUpdateMeteo <= 0:
            self.runCounterUpdateMeteo = self.UpdateCycleMeteo/10

            # Rain update first in order to reset the Rain value at midnight
            OldValue = Devices[3].sValue
            if OldValue == "":
                OldValue = "0;0"
            OldValueSplitted = OldValue.rsplit(";")
            OldRainRate = OldValueSplitted[0]
            OldRainTotal = OldValueSplitted[1]
            NewRainTotal = float(OldRainTotal) + self.UpdateCycleMeteo*float(OldRainRate)/10000/3600
            now = datetime.now()
            Domoticz.Debug("Climacell Now - day : " + str(now.day) + " all :" + now.strftime("%c"))
            previous_date = now
            previous_date = previous_date-timedelta(days=0, seconds=self.UpdateCycleMeteo, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0)
            Domoticz.Debug("Climacell Previous_date - day : " + str(previous_date.day) + " all :" + previous_date.strftime("%c"))
            if now.day != previous_date.day:  # a minuit on remet le compteur total à zéro
                NewRainTotal = 0
            Rain = OldRainRate + ";" + str(NewRainTotal)
            Domoticz.Debug("Climacell Rain: " + Rain)
            Devices[3].Update(nValue=0, sValue=Rain)

            # get the Climacell Data
            (crdu, datas) = self.get_climacell_data(tcsMeteoFields, "Climacell Meteo Server")
            if crdu is False:
                break
            FirstInterval = datas[0]

            if 'temperature' not in FirstInterval.keys():
                self.errorMessage("Climacell Meteo Server not available : found when reading Temperature ")
                Domoticz.Error("Climacell v4 value: " + str(FirstInterval))
                break
            try:
                Temp = int(FirstInterval['temperature']*100)
            except Exception as e:
                self.errorMessage("Climacell Meteo Server not available : " + str(type(e)) + " " + str(e.args) + " found when reading Temperature ")
                break
            if (Devices[1].nValue != Temp):
                Domoticz.Debug("Climacell New Temp value: " + "{value:.1f}".format(value=Temp / 100))
                Devices[1].Update(nValue=Temp, sValue="{value:.1f}".format(value=Temp / 100))

            # THB='' ..temp.. ' C;' .. humidity .. ' %;'..humidity_status..';'.. pressionAtm..
            # ' hPa;' ..weather_condition..'' --Temperature;Humidity;Humidity Status;Barometer;Forecast
            try:
                humidity = FirstInterval['humidity']
                baro_pressure = FirstInterval['pressureSeaLevel']
                weather_code = FirstInterval['weatherCode']
            except Exception as e:
                self.errorMessage("Climacell Meteo Server not available : " + str(type(e)) + " " + str(e.args) + " found when reading THB")
                break
            THB = Devices[2].sValue
            if (humidity is not None and baro_pressure is not None and weather_code is not None and Temp is not None):
                humidity_status = self.get_humidity_status(humidity)
                result = self.get_weather_condition(weather_code)
                weather_condition = result['weather_condition']
                THB = "{valueTemp:.1f}".format(valueTemp=Temp / 100) + ";" +\
                      "{valueHumidity:.1f}".format(valueHumidity=humidity) + ";" + humidity_status + ";" + str(baro_pressure) + ";" + str(weather_condition)
            if (Devices[2].sValue != THB):
                Domoticz.Debug("Climacell THB value: " + THB)
                Devices[2].Update(nValue=0, sValue=THB)

            # Rain rate
            try:
                RainRate = str(FirstInterval['precipitationIntensity']*10000)
            except Exception as e:
                self.errorMessage("Climacell Meteo Server not available : " + str(type(e)) + " " + str(e.args) + " found when reading RainRate")
                break
            if RainRate is None:
                RainRate = OldRainRate
            Rain = RainRate + ";" + str(NewRainTotal)
            Domoticz.Debug("Climacell Rain: " + Rain)
            Devices[3].Update(nValue=0, sValue=Rain)

            UV_Index = 0
            if (Devices[4].nValue != int(UV_Index)):
                Domoticz.Debug("Climacell UV Index: " + str(UV_Index))
                Devices[4].Update(nValue=int(UV_Index), sValue=str(UV_Index) + ";" + str(Temp))

            try:
                Visibility = int(FirstInterval['visibility']*10)
            except Exception as e:
                self.errorMessage("Climacell Meteo Server not available : " + str(type(e)) + " " + str(e.args) + " found when reading Visibility")
                break
            if (Devices[5].nValue != Visibility):
                Domoticz.Debug("Climacell Visibility value: " + "{value:.1f}".format(value=Visibility/10))
                Devices[5].Update(nValue=Visibility, sValue="{value:.1f}".format(value=Visibility/10))

            try:
                feels_like = FirstInterval['temperatureApparent']
                wind_speed = FirstInterval['windSpeed']
                wind_gust = FirstInterval['windGust']
                wind_direction = int(FirstInterval['windDirection'])
                # https://fr.wikipedia.org/wiki/Temp%C3%A9rature_ressentie
                feels_like = 13.12 + 0.6215 * Temp / 100 + (0.3965 * Temp / 100-11.37) * pow(wind_speed * 3600 / 1000, 0.16)

            except Exception as e:
                self.errorMessage("Climacell Meteo Server not available : " +
                                  str(type(e)) + " " + str(e.args) + " found when reading Wind_speed, Wind_gust,Wind_direction")
                break
            wind = Devices[6].sValue
            if (feels_like is not None and wind_speed is not None and wind_gust is not None and wind_direction is not None):
                direction = self.get_quadrants(wind_direction)
                wind = str(wind_direction) + ";" + direction + ";" + "{valueSpeed:.1f}".format(valueSpeed=wind_speed*10) +\
                    ";" + "{valueGust:.1f}".format(valueGust=wind_gust*10) + ";" +\
                    "{valueTemp:.1f}".format(valueTemp=Temp/100) + ";" + "{valuefeels_like:.1f}".format(valuefeels_like=feels_like)
            if (Devices[6].sValue != wind):
                Domoticz.Debug("Climacell wind value: " + wind)
                Devices[6].Update(nValue=0, sValue=wind)

            try:
                cloud_cover = int(FirstInterval['cloudCover'])
            except Exception as e:
                self.errorMessage("Climacell Meteo Server not available : " + str(type(e)) + " " + str(e.args) + " found when reading Cloud_cover")
                break
            if (Devices[7].nValue != cloud_cover):
                Domoticz.Debug("Climacell cloud_cover value: " + "{value:.1f}".format(value=cloud_cover))
                Devices[7].Update(nValue=cloud_cover, sValue="{value:.1f}".format(value=cloud_cover),
                                  Options={"Custom": "1;%"}, Image=Images["Climacell_cloud_cover"].ID)

            try:
                precipitation_type = int(FirstInterval['precipitationType'])
            except Exception as e:
                self.errorMessage("Climacell Meteo Server not available : " + str(type(e)) + " " + str(e.args) + " found when reading Precipitation type")
                break
            szprecipitation_type = Devices[8].sValue
            if precipitation_type is not None:
                szprecipitation_type = self.get_precipitation_type(precipitation_type)
                Domoticz.Debug("Climacell Precipitation_Type value : " + szprecipitation_type)
            if (Devices[8].sValue != szprecipitation_type):
                Domoticz.Debug("Climacell Precipitation_Type value: " + szprecipitation_type)
                Devices[8].Update(nValue=0, sValue=szprecipitation_type)

            try:
                surface_shortwave_radiation = int(FirstInterval['solarGHI'])
            except Exception as e:
                self.errorMessage("Climacell Meteo Server not available : " +
                                  str(type(e)) + " " + str(e.args) + " found when reading surface_shortwave_radiation")
                break
            if (Devices[9].nValue != surface_shortwave_radiation):
                Domoticz.Debug("Climacell surface_shortwave_radiation value: " + "{value:.1f}".format(value=surface_shortwave_radiation))
                Devices[9].Update(nValue=surface_shortwave_radiation,  sValue="{value:.1f}".format(value=surface_shortwave_radiation))

            try:
                observation_time = FirstInterval['startTime']
            except Exception as e:
                self.errorMessage("Climacell Meteo Server not available : " + str(type(e)) + " " + str(e.args) + " found when reading observation_time")
                break
            if (observation_time is not None and Devices[17].sValue != observation_time):
                Domoticz.Debug("Climacell observation_time : " + observation_time)
                Devices[17].Update(nValue=0, sValue=observation_time)

        Domoticz.Debug("Climacell v4 Air Quality Polling in " + str(self.runCounterUpdateAirQuality-1) + " heartbeats.")
        self.runCounterUpdateAirQuality = self.runCounterUpdateAirQuality - 1
        while self.runCounterUpdateAirQuality <= 0:
            # get the Climacell Data
            self.runCounterUpdateAirQuality = self.UpdateCycleAirQuality/10
            (crdu, datas) = self.get_climacell_data(tcsAirQualityFields, "Climacell Air Quality Server")
            if crdu is False:
                break
            FirstInterval = datas[0]

            if 'particulateMatter10' not in FirstInterval.keys():
                self.errorMessage("Climacell AirQuality not available : " + str(type(e)) + " " + str(e.args) + " found when reading pm10")
                Domoticz.Error("Climacell v4 value: " + str(FirstInterval))
                break

            try:
                pm10 = int(FirstInterval['particulateMatter10']*100)
            except Exception as e:
                self.errorMessage("Climacell AirQuality not available : " + str(type(e)) + " " + str(e.args) + " found when reading pm10")
                break
            if (Devices[10].nValue != pm10):
                Domoticz.Debug("Climacell New pm10 value: " + "{value:.1f}".format(value=pm10/100))
                Devices[10].Update(nValue=pm10, sValue="{value:.1f}".format(value=pm10/100))

            try:
                pm25 = int(FirstInterval['particulateMatter25']*100)
            except Exception as e:
                self.errorMessage("Climacell AirQuality not available : " + str(type(e)) + " " + str(e.args) + " found when reading pm25")
                break
            if (Devices[11].nValue != pm25):
                Domoticz.Debug("Climacell pm25 value: " + "{value:.1f}".format(value=pm25/100))
                Devices[11].Update(nValue=pm25, sValue="{value:.1f}".format(value=pm25/100))

            try:
                o3 = int(FirstInterval['pollutantO3']*100)
            except Exception as e:
                self.errorMessage("Climacell AirQuality not available : " + str(type(e)) + " " + str(e.args) + " found when reading o3")
                break
            if (Devices[12].nValue != o3):
                Domoticz.Debug("Climacell o3 value: " + "{value:.1f}".format(value=o3/100))
                Devices[12].Update(nValue=o3, sValue="{value:.1f}".format(value=o3/100))

            try:
                no2 = int(FirstInterval['pollutantNO2']*100)
            except Exception as e:
                self.errorMessage("Climacell AirQuality not available : " + str(type(e)) + " " + str(e.args) + " found when reading no2")
                break
            if (Devices[13].nValue != no2):
                Domoticz.Debug("Climacell no2 value: " + "{value:.1f}".format(value=no2/100))
                Devices[13].Update(nValue=no2, sValue="{value:.1f}".format(value=no2/100))

            try:
                co = int(FirstInterval['pollutantCO']*100)
            except Exception as e:
                self.errorMessage("Climacell AirQuality not available : " + str(type(e)) + " " + str(e.args) + " found when reading co")
                break
            if (Devices[14].nValue != co):
                Domoticz.Debug("Climacell co value: " + "{value:.2f}".format(value=co/100))
                Devices[14].Update(nValue=co, sValue="{value:.2f}".format(value=co/100))

            try:
                so2 = int(FirstInterval['pollutantSO2']*100)
            except Exception as e:
                self.errorMessage("Climacell AirQuality not available : " + str(type(e)) + " " + str(e.args) + " found when reading so2")
                break
            if (Devices[15].nValue != so2):
                Domoticz.Debug("Climacell so2 value: " + "{value:.2f}".format(value=so2/100))
                Devices[15].Update(nValue=so2, sValue="{value:.2f}".format(value=so2/100))

            try:
                epa_health_concern = FirstInterval['epaHealthConcern']
            except Exception as e:
                self.errorMessage("Climacell AirQuality not available : " + str(type(e)) + " " + str(e.args) + " found when reading epa_health_concern")
                break
            szepa_health_concern = Devices[16].sValue
            if epa_health_concern is not None:
                szepa_health_concern = self.get_epa_health_concern(epa_health_concern)
            if (Devices[16].sValue != szepa_health_concern):
                Domoticz.Debug("Climacell epa_health_concern value: " + szepa_health_concern)
                Option = "1;" + szepa_health_concern  # texte dans les unités pour l'affichage
                Devices[16].Update(nValue=0, sValue=szepa_health_concern,
                                   Options={"Custom": Option}, Image=Images["Climacell_air_quality"].ID)

        Domoticz.Debug("onHeartBeat called - End")


global _plugin
_plugin = BasePlugin()


def UpdateDevice(Unit, **kwargs):
    if Unit in Devices:
        # check if kwargs contain an update for nValue or sValue... if not, use the existing one(s)
        if "nValue" in kwargs:
            nValue = kwargs["nValue"]
        else:
            nValue = Devices[Unit].nValue
        if "sValue" in kwargs:
            sValue = kwargs["sValue"]
        else:
            sValue = Devices[Unit].sValue

        # build the arguments for the call to Device.Update
        update_args = {"nValue": nValue, "sValue": sValue}
        change = False
        if nValue != Devices[Unit].nValue or sValue != Devices[Unit].sValue:
            change = True
        for arg in kwargs:
            if arg == "TimedOut":
                if kwargs[arg] != Devices[Unit].TimedOut:
                    change = True
                    update_args[arg] = kwargs[arg]
                Domoticz.Debug("TimedOut = {}".format(kwargs[arg]))
            if arg == "BatteryLevel":
                if kwargs[arg] != Devices[Unit].BatteryLevel:
                    change = True
                    update_args[arg] = kwargs[arg]
                Domoticz.Debug("BatteryLevel = {}".format(kwargs[arg]))
            if arg == "Color":
                try:
                    if kwargs[arg] != Devices[Unit].Color:
                        change = True
                except:
                    change = True
                finally:
                    if change:
                        update_args[arg] = kwargs[arg]
                Domoticz.Debug("Color = {}".format(kwargs[arg]))
            if arg == "Image":
                if kwargs[arg] != Devices[Unit].Image:
                    change = True
                    update_args[arg] = kwargs[arg]
            if arg == "Forced":
                change = change or kwargs[arg]
        Domoticz.Debug("Change in device {} = {}".format(Unit, change))
        if change:
            Devices[Unit].Update(**update_args)


def onStart():
    global _plugin
    _plugin.onStart()


def onStop():
    global _plugin
    _plugin.onStop()


def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)


def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)


def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)


def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)


def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)


def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

# Generic helper functions


def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug("'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:   " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:   '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name: '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:" + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return


if __name__ == "__main__":
    from Domoticz import Device
    from Domoticz import Parameters
    from TestCode import runtest
    from TestCode import Devices
    from TestCode import Images

    runtest(BasePlugin())
    exit(0)
