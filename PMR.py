# -*- coding: utf-8 -*-

"""PMRReader by DJFio.

This module demonstrates reading the PMR type of files - well known as AVID database files

.. MDV website:
   http://djfio.ru/mdv/

     """
import urllib2  # the lib that handles the url stuff
from binascii import hexlify
from struct import unpack
from xml.etree.cElementTree import Element, Comment #, SubElement, tostring
from xml.etree import ElementTree
from xml.dom import minidom


__version__ = '0.0.1'
""" Module Version
"""
__module_encodind__ = 'iso8859_5'
"""encoding to use in the name decoder
"""

class PMRreader(object):
    """
    Base class for reading .PMR type files
    """
    def __init__(self, fileurl):
        """
        Args:
            fileurl -  name of the target PMR file in URL format
        """
        pmr_header_len = 12
        self.file = urllib2.urlopen(fileurl)
        self.position = 0
        self.ispmr = False
        self.intelbyteorder = True # Little-Endian
        self.uuidlength = 0
        self.numberofitemsinpmr = 0
        self.datalength = 0
        self.currentitem = 0
        header = self.file.read(pmr_header_len)
        if header == "":
            self.file.close()
            return
        magicbytes = hexlify(header[0:4])
        if magicbytes != 'a9070000':
            if magicbytes == '000007a9': # Big-Endian
                self.intelbyteorder = False
            else:
                self.file.close()
                return
        self.ispmr = True
        if self.intelbyteorder:
            self.uuidlength = unpack("<L", header[4:8])[0] * 4
            self.numberofitemsinpmr = unpack("<L", header[8:12])[0]
        else:
            self.uuidlength = unpack(">L", header[4:8])[0] * 4
            self.numberofitemsinpmr = unpack(">L", header[8:12])[0]
        #reading entire file (assuming that it is not too big)
        self.data = self.file.read()
        self.datalength = len(self.data)
        self.file.close()

    def resetposition(self):
        """
        resets current position to the beginning of the data
        """
        self.currentitem = 0
        self.position = 0
    def validatecurrenstate(self):
        """
        test the validity to read next item
        returns boolean
        """
        if not self.ispmr:
            return False  # file must be opened

        if self.position >= self.datalength-self.uuidlength*2+4:
            return False # position must be in range 2xUID + 2x2bytes

        # sometimes pmr consists of two chunks. don't know how to deal with that.
        newchunk_test = hexlify(self.data[self.position:self.position+4])
        if newchunk_test == "10000000":
            print "Found newchunk in pmr. Unsupported.\n"
            return False

        if self.currentitem >= self.numberofitemsinpmr:
            return False # number of items set in file header and can not be more

        return True

    def readnextitem(self):
        """
        Looks up for the next item in PMR data section
            returning list contains
            materialPackageUID, Name, Project, physicalSourcePackageUID, Date
        """
        #  the data in data section of pmr file is strored in the following form
        #  8 or 32 bytes - materialPackageUID
        #  2 bytes - Clip Name length X
        #  X bytes - Clip Name
        #  2 bytes - Project Name length Y
        #  Y bytes - Project Name
        #  8 or 32 bytes  - physicalSourcePackageUID
        #  4 bytes - timestamp
        # result = [None, None, None, None, None]
        result = [None, None, None, None, None]

        if not self.validatecurrenstate():
            return result

        clipnamelen = 0
        projnamelen = 0
        curposeof = False

        curpos = self.position
        result = [None, None, None, None, None]

        # because of validatecurrenstate() is True 
        # we can read at least one UID + 1 short without eof test

        # read 1st UUID
        result[0] = hexlify(self.data[curpos:curpos+self.uuidlength])
        curpos += self.uuidlength

        #read clip name len
        if self.intelbyteorder:
            clipnamelen = unpack("<H", self.data[curpos:curpos+2])[0]
        else:
            clipnamelen = unpack(">H", self.data[curpos:curpos+2])[0]
        curpos += 2

        #reading Clip Name
        # and now we have to test if we out of data bounds
        if curpos + clipnamelen <= self.datalength:                 # safety check
            if clipnamelen != 0:           # may be 0 in some cases . Database Error?
                result[1] = str(self.data[curpos:curpos + clipnamelen])
                curpos += clipnamelen
            else:
                result[1] = 'MDVx::NullClipName'
        else:
            curposeof = True

        #read project name len
        if not curposeof:
            if curpos + 2 <= self.datalength:                           #safety check
                if self.intelbyteorder:
                    projnamelen = unpack("<H", self.data[curpos:curpos+2])[0]
                else:
                    projnamelen = unpack(">H", self.data[curpos:curpos+2])[0]
                curpos += 2
            else:
                curposeof = True

        #read project name
        if not curposeof:
            if curpos + projnamelen <= self.datalength:                 #safety check
                if projnamelen != 0:           # may be 0 in some cases . Not specified ?
                    result[2] = str(self.data[curpos:curpos + projnamelen])
                    curpos += projnamelen
                else:
                    result[2] = 'MDVx::UNMANAGED_FILES'
            else:
                curposeof = True

        #read the 2nd UUID
        if not curposeof:
            if curpos + self.uuidlength <= self.datalength:             #safety check
                result[3] = hexlify(self.data[curpos:curpos+self.uuidlength])
                curpos += self.uuidlength
            else:
                curposeof = True

        #read timestamp
        if not curposeof:
            if curpos + 4 <= self.datalength:                           #safety check
                result[4] = hexlify(self.data[curpos:curpos+4])
                curpos += 4
            else:
                curposeof = True

        self.position = curpos
        self.currentitem += 1

        if curposeof:
            result = [None, None, None, None, None]
        return result

    def outprintable(self):
        """
        Returns tab separated string with all the items found
        """
        self.resetposition()
        result = self.readnextitem()
        printabledata = "materialPackageUID\t"
        printabledata += "Clip Name\t"
        printabledata += "Project\t"
        printabledata += "physicalSourcePackageUID\t"
        printabledata += "Date\t"
        printabledata += "ItmNo\n"
        while result[0] != None:
            temp = []
            temp.append(result[0])
            temp.append("\t")
            temp.append(result[1])
            temp.append("\t")
            temp.append(result[2])
            temp.append("\t")
            temp.append(result[3])
            temp.append("\t")
            temp.append(result[4])
            temp.append("\t")
            temp.append(str(self.currentitem))
            temp.append("\n")
            joined = "".join(temp)
            printabledata += joined
            result = self.readnextitem()
        return printabledata

    def outxml(self):
        """
        Returns XML with all the items found
        """
        self.resetposition()
        result = self.readnextitem()
        xmlroot = Element("PMRdata")
        xmlroot.set('version', __version__)
        xmlroot.set('generator', 'MDVx:PMRReader')
        xmlroot.append(Comment("Generated with MDVx by DJFio[DB] http://djfio.ru/mdv/"))

        while result[0] != None:
            item = Element('item')
            item.set('matUUID', unicode(result[0]))
            item.set('name', unicode(result[1].decode(__module_encodind__)))
            item.set('project', unicode(result[2].decode(__module_encodind__)))
            item.set('srcUUID', unicode(result[3]))
            item.set('date', unicode(result[4]))
            xmlroot.append(item)
            result = self.readnextitem()
        return xmlroot

def prettify(elem):
    """Returns a pretty-printed XML string for the Element.
    """
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")
