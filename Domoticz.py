import shelve

Devices = {}
Images = {}
DEBUG = False
dbHistory = 'climacelV4.db'


def Log(textStr):
    print(u'Log : {}'.format(textStr))


def Debug(textStr):
    if DEBUG:
        print(u'Debug : {}'.format(textStr))


def Error(textStr):
    print(u'Error : {}'.format(textStr))


def Status(textStr):
    print(u'Status : {}'.format(textStr))


def Debugging(value):
    global DEBUG
    if value == 1:
        DEBUG = True
        Log(u'debug: {}'.format(DEBUG))


def Heartbeat(value):
    pass


def UpdateDevice(num, Image=None, nValue=None, sValue=None):
    device = Devices[num]
    device.Update(Image=Image, nValue=nValue, sValue=sValue)


def Start():
    database = shelve.open(dbHistory)
    if 'Devices' in database.keys():
        Devices = database['Devices']
    database.close()


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
    def sValue(self, value):
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

    @property
    def Unit(self):
        return self._unit

    @Unit.setter
    def Unit(self, value):
        self._unit = value

    @property
    def TypeName(self):
        return self._typeName

    @TypeName.setter
    def TypeName(self, value):
        self._typeName = value

    @property
    def Type(self):
        return self._type

    @Type.setter
    def Type(self, value):
        self._type = value

    @property
    def Subtype(self):
        return self._subtype

    @Subtype.setter
    def Subtype(self, value):
        self._subtype = value

    @property
    def Options(self):
        return self._options

    @Options.setter
    def Options(self, value):
        self._options = value

    @property
    def Used(self):
        return self._used

    @Used.setter
    def Used(self, value):
        self._used = value

    def __init__(self, Name="", Unit=0, TypeName="", Used=0, Type=0, Subtype=0, Options=""):
        self._nValue = 0
        self._sValue = ''
        self._name = Name
        self._unit = Unit
        self._type = Type
        self._typeName = TypeName
        self._subtype = Subtype
        self._options = Options
        self._used = Used
        self._image = None

    def Update(self, nValue=None, sValue=None, Options=None, Image=None):
        if nValue is not None:
            self._nValue = nValue
        if (sValue is not None) and (sValue != ''):
            self._sValue = sValue
        elif self._sValue is None:
            self._sValue = ''
        if Image is not None:
            self._image = Image
        if Options is not None:
            self._options = Options
        txt2log = u'--- update unit {}\n   nValue: {}\n sValue: {}\n   image: {}'
        Debug(txt2log.format(self._unit, self._nValue, self._sValue, self._image))
        database = shelve.open(dbHistory)
        database['Devices'] = Devices
        database.close()

    def __str__(self):
        text2return = u'Name: {} Unit: {} Type: {} TypeName: {} Subtype: {} Options: {}\n'
        text2return += u'nValue: {} sValue: {} Image: {}'
        return text2return.format(self._name, self._unit, self._type, self._typeName,
                                  self._subtype, self._options,
                                  self._nValue, self._sValue, self._image)

    def Create(self):
        Devices[len(Devices)+1] = self
        database = shelve.open(dbHistory)
        dbDevices = {}
        if 'Devices' in database.keys():
            dbDevices = database['Devices']
        dbDevices[self._unit] = self
        database['Devices'] = dbDevices
        database.close()


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
