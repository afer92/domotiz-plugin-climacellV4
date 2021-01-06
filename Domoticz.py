
Parameters = {"Mode5": "Debug"}
Devices = {}
Images = {}

def Debug(textStr):
    print(u'Debug : {}'.format(textStr))

def Error(textStr):
    print(u'Error : {}'.format(textStr))

def Status(textStr):
    print(u'Status : {}'.format(textStr))

def Debugging(value):
    pass

def Heartbeat(value):
    pass

def UpdateDevice(num, Image='', nValue=0, sValue=''):
    pass

class Device:

    @property
    def nValue(self):
        return self._nValue

    @nValue.setter
    def nValue(self, value):
        self._nValue = value

    @property
    def sValue(self):
        return self._sValue

    @sValue.setter
    def nValue(self, value):
        self._sValue = value

    @property
    def ID(self):
        return self._sValue

    @ID.setter
    def ID(self, value):
        self._sValue = value

    @property
    def Typename(self):
        return self._typeName

    @Typename.setter
    def ID(self, value):
        self._typeName = value

    @property
    def Name(self):
        return self._name

    @Name.setter
    def ID(self, value):
        self._name = value

    @property
    def LastLevel(self):
        return 0

    @property
    def Image(self):
        return self._image

    @Image.setter
    def ID(self, value):
        self._image = value

    def __init__(self, Name="", Unit=0, TypeName="", Used=0, Type=0, Subtype=0, Options=""):
        self._nValue = 0
        self._sValue = ''
        self._name = Name
        self._unit = Unit
        self._typeName = TypeName
        self._used = Used
        self._image = None

    def Update(self, nValue=0, sValue='', Options='', Image=None):
        self._nvalue = nValue
        self._svalue = sValue
        self._image = Image

    def __str__(self):
        return "0"

    def Create(self):
        Devices[len(Devices)+1] = self

class Image:

    @property
    def Name(self):
        return self._name

    @Name.setter
    def ID(self, value):
        self._name = value

    @property
    def Base(self):
        return self._base

    @Base.setter
    def ID(self, value):
        self._base = value

    @property
    def ID(self):
        return self._filename

    @ID.setter
    def ID(self, value):
        self._filename = value

    def __init__(self, Filename=""):
        self._filename = Filename
        self._name = Filename
        self._base = Filename

    def Create(self):
        Images[self._filename.split(u' ')[0]] = self
