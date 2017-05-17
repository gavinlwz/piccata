'''
Copyright (c) 2012 Maciej Wasilak <http://sixpinetrees.blogspot.com/>
              2017 Robert Lubos
'''
import collections
import struct
from itertools import chain
from abc import ABCMeta, abstractmethod

from constants import *

class Options(object):
    """Represent CoAP Header Options."""

    def __init__(self):
        self._options = {}

    def decode(self, rawdata):
        """Decode all options in message from raw binary data."""
        option_number = 0
        while len(rawdata) > 0:
            if ord(rawdata[0]) == 0xFF:
                return rawdata[1:]
            dllen = ord(rawdata[0])
            delta = (dllen & 0xF0) >> 4
            length = (dllen & 0x0F)
            rawdata = rawdata[1:]
            (delta, rawdata) = self.readExtendedFieldValue(delta, rawdata)
            (length, rawdata) = self.readExtendedFieldValue(length, rawdata)
            option_number += delta
            option = option_formats.get(option_number, OpaqueOption)(option_number)
            option.decode(rawdata[:length])
            self.addOption(option)
            rawdata = rawdata[length:]
        return ''

    def encode(self):
        """Encode all options in option header into string of bytes."""
        data = []
        current_opt_num = 0
        option_list = self.optionList()
        for option in option_list:
            delta, extended_delta = self.writeExtendedFieldValue(option.number - current_opt_num)
            length, extended_length = self.writeExtendedFieldValue(option.length)
            data.append(chr(((delta & 0x0F) << 4) + (length & 0x0F)))
            data.append(extended_delta)
            data.append(extended_length)
            data.append(option.encode())
            current_opt_num = option.number
        return (''.join(data))

    def addOption(self, option):
        """Add option into option header."""
        self._options.setdefault(option.number, []).append(option)

    def deleteOption(self, number):
        """Delete option from option header."""
        if number in self._options:
            self._options.pop(number)

    def getOption (self, number):
        """Get option with specified number."""
        return self._options.get(number)

    def optionList(self):
        return chain.from_iterable(sorted(self._options.values(), key=lambda x: x[0].number))

    def getUriPathAsString(self):
        return '/' + '/'.join(self.uri_path)

    def _setUriPath(self, segments):
        """Convenience setter: Uri-Path option"""
        if isinstance(segments, basestring): #For Python >3.1 replace with isinstance(segments,str)
            raise ValueError("URI Path should be passed as a list or tuple of segments")
        self.deleteOption(number=URI_PATH)
        for segment in segments:
            self.addOption(StringOption(number=URI_PATH, value=str(segment)))

    def _getUriPath(self):
        """Convenience getter: Uri-Path option"""
        segment_list = []
        uri_path = self.getOption(number=URI_PATH)
        if uri_path is not None:
            for segment in uri_path:
                segment_list.append(segment.value)
        return segment_list

    uri_path = property(_getUriPath, _setUriPath)

    def _setUriQuery(self, segments):
        """Convenience setter: Uri-Query option"""
        if isinstance(segments, basestring): #For Python >3.1 replace with isinstance(segments,str)
            raise ValueError("URI Query should be passed as a list or tuple of segments")
        self.deleteOption(number=URI_QUERY)
        for segment in segments:
            self.addOption(StringOption(number=URI_QUERY, value=str(segment)))

    def _getUriQuery(self):
        """Convenience getter: Uri-Query option"""
        segment_list = []
        uri_query = self.getOption(number=URI_QUERY)
        if uri_query is not None:
            for segment in uri_query:
                segment_list.append(segment.value)
        return segment_list

    uri_query = property(_getUriQuery, _setUriQuery)

    def _setBlock2(self, block_tuple):
        """Convenience setter: Block2 option"""
        self.deleteOption(number=BLOCK2)
        self.addOption(BlockOption(number=BLOCK2, value=block_tuple))

    def _getBlock2(self):
        """Convenience getter: Block2 option"""
        block2 = self.getOption(number=BLOCK2)
        if block2 is not None:
            return block2[0].value
        else:
            return None

    block2 = property(_getBlock2, _setBlock2)

    def _setBlock1(self, block_tuple):
        """Convenience setter: Block1 option"""
        self.deleteOption(number=BLOCK1)
        self.addOption(BlockOption(number=BLOCK1, value=block_tuple))

    def _getBlock1(self):
        """Convenience getter: Block1 option"""
        block1 = self.getOption(number=BLOCK1)
        if block1 is not None:
            return block1[0].value
        else:
            return None

    block1 = property(_getBlock1, _setBlock1)

    def _setContentFormat(self, content_format):
        """Convenience setter: Content-Format option"""
        self.deleteOption(number=CONTENT_FORMAT)
        self.addOption(UintOption(number=CONTENT_FORMAT, value=content_format))

    def _getContentFormat(self):
        """Convenience getter: Content-Format option"""
        content_format = self.getOption(number=CONTENT_FORMAT)
        if content_format is not None:
            return content_format[0].value
        else:
            return None

    content_format = property(_getContentFormat, _setContentFormat)

    def _setETag(self, etag):
        """Convenience setter: ETag option"""
        self.deleteOption(number=ETAG)
        if etag is not None:
            self.addOption(OpaqueOption(number=ETAG, value=etag))

    def _getETag(self):
        """Convenience getter: ETag option"""
        etag = self.getOption(number=ETAG)
        if etag is not None:
            return etag[0].value
        else:
            return None

    etag = property(_getETag, _setETag, None, "Access to a single ETag on the message (as used in responses)")

    def _setETags(self, etags):
        self.deleteOption(number=ETAG)
        for tag in etags:
            self.addOption(OpaqueOption(number=ETAG, value=tag))

    def _getETags(self):
        etag = self.getOption(number=ETAG)
        return [] if etag is None else [tag.value for tag in etag]

    etags = property(_getETags, _setETags, None, "Access to a list of ETags on the message (as used in requests)")

    def _setObserve(self, observe):
        self.deleteOption(number=OBSERVE)
        if observe is not None:
            self.addOption(UintOption(number=OBSERVE, value=observe))

    def _getObserve(self):
        observe = self.getOption(number=OBSERVE)
        if observe is not None:
            return observe[0].value
        else:
            return None

    observe = property(_getObserve, _setObserve)

    def _setAccept(self, accept):
        self.deleteOption(number=ACCEPT)
        if accept is not None:
            self.addOption(UintOption(number=ACCEPT, value=accept))

    def _getAccept(self):
        accept = self.getOption(number=ACCEPT)
        if accept is not None:
            return accept[0].value
        else:
            return None

    accept = property(_getAccept, _setAccept)

    def _setLocationPath(self, segments):
        """Convenience setter: Location-Path option"""
        if isinstance(segments, basestring): #For Python >3.1 replace with isinstance(segments,str)
            raise ValueError("Location Path should be passed as a list or tuple of segments")
        self.deleteOption(number=LOCATION_PATH)
        for segment in segments:
            self.addOption(StringOption(number=LOCATION_PATH, value=str(segment)))

    def _getLocationPath(self):
        """Convenience getter: Location-Path option"""
        segment_list = []
        location_path = self.getOption(number=LOCATION_PATH)
        if location_path is not None:
            for segment in location_path:
                segment_list.append(segment.value)
        return segment_list

    location_path = property(_getLocationPath, _setLocationPath)

    @staticmethod
    def readExtendedFieldValue(value, rawdata):
        """Used to decode large values of option delta and option length
        from raw binary form."""
        if value >= 0 and value < 13:
            return (value, rawdata)
        elif value == 13:
            return (ord(rawdata[0]) + 13, rawdata[1:])
        elif value == 14:
            return (struct.unpack('!H', rawdata[:2])[0] + 269, rawdata[2:])
        else:
            raise ValueError("Value out of range.")

    @staticmethod
    def writeExtendedFieldValue(value):
        """Used to encode large values of option delta and option length
        into raw binary form.
        In CoAP option delta and length can be represented by a variable
        number of bytes depending on the value."""
        if value >= 0 and value < 13:
            return (value, '')
        elif value >= 13 and value < 269:
            return (13, struct.pack('!B', value - 13))
        elif value >= 269 and value < 65804:
            return (14, struct.pack('!H', value - 269))
        else:
            raise ValueError("Value out of range.")


class Option:
    __metaclass__ = ABCMeta

    @abstractmethod
    def encode(self):
        pass

    @abstractmethod
    def decode(self):
        pass

    @abstractmethod
    def _length(self):
        pass


class OpaqueOption(Option):
    """Opaque CoAP option - used to represent opaque options.
       This is a default option type."""

    def __init__(self, number, value=""):
        self.value = value
        self.number = number

    def encode(self):
        rawdata = self.value
        return rawdata

    def decode(self, rawdata):
        self.value = rawdata  # if rawdata is not None else ""

    def _length(self):
        return len(self.value)
    length = property(_length)


class StringOption(Option):
    """String CoAP option - used to represent string options."""

    def __init__(self, number, value=""):
        self.value = value
        self.number = number

    def encode(self):
        rawdata = self.value
        return rawdata

    def decode(self, rawdata):
        self.value = rawdata  # if rawdata is not None else ""

    def _length(self):
        return len(self.value)
    length = property(_length)


class UintOption(Option):
    """Uint CoAP option - used to represent uint options."""

    def __init__(self, number, value=0):
        self.value = value
        self.number = number

    def encode(self):
        rawdata = struct.pack("!L", self.value)  # For Python >3.1 replace with int.to_bytes()
        return rawdata.lstrip(chr(0))

    def decode(self, rawdata):  # For Python >3.1 replace with int.from_bytes()
        value = 0
        for byte in rawdata:
            value = (value * 256) + ord(byte)
        self.value = value
        return self

    def _length(self):
        if self.value > 0:
            return (self.value.bit_length() - 1) // 8 + 1
        else:
            return 0
    length = property(_length)


class BlockOption(Option):
    """Block CoAP option - special option used only for Block1 and Block2 options.
       Currently it is the only type of CoAP options that has
       internal structure."""
    BlockwiseTuple = collections.namedtuple('BlockwiseTuple', ['num', 'm', 'szx'])

    def __init__(self, number, value=(0, None, 0)):
        self.value = self.BlockwiseTuple._make(value)
        self.number = number

    def encode(self):
        as_integer = (self.value[0] << 4) + (self.value[1] * 0x08) + self.value[2]
        rawdata = struct.pack("!L", as_integer)  # For Python >3.1 replace with int.to_bytes()
        return rawdata.lstrip(chr(0))

    def decode(self, rawdata):
        as_integer = 0
        for byte in rawdata:
            as_integer = (as_integer * 256) + ord(byte)
        self.value = self.BlockwiseTuple(num=(as_integer >> 4), m=bool(as_integer & 0x08), szx=(as_integer & 0x07))

    def _length(self):
        return ((self.value[0].bit_length() + 3) / 8 + 1)
    length = property(_length)

option_formats = {3:  StringOption,     # If-Match
                  6:  UintOption,       # Observe
                  7:  UintOption,       # Uri-Port
                  8:  StringOption,     # Location-Path
                  11: StringOption,     # Uri-Path
                  12: UintOption,       # Content-Format
                  14: UintOption,       # Max-Age
                  15: StringOption,     # Uri-Query
                  17: UintOption,       # Accept
                  20: StringOption,     # Location-Query
                  23: BlockOption,      # Block2
                  27: BlockOption,      # Block1
                  28: UintOption,       # Size2
                  35: StringOption,     # Proxy-Uri
                  39: StringOption,     # Proxy-Scheme
                  60: UintOption}       # Size1
"""Dictionary used to assign option type to option numbers."""
