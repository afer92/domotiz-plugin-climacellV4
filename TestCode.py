
from Domoticz import Device
from Domoticz import Devices
from Domoticz import Images
import Domoticz

# your params

API_key = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' # Your api key from Climacell
LATITUDE = '47.111111' # Your location
LONGITUDE = '2.222222'


Parameters = {}
Parameters['Mode1'] = API_key
Parameters['Mode2'] = u"{},{}".format(LATITUDE, LONGITUDE)
Parameters['Mode3'] = 300  # UpdateCycleMeteo
Parameters['Mode4'] = 1800  # UpdateCycleAirQuality
Parameters['Mode5'] = 'Debug'  # Debug or Normal


def runtest(plugin):

    Domoticz.Start()
    plugin.onStart()
    plugin.onHeartbeat()
    plugin.onHeartbeat()
    plugin.onStop()
