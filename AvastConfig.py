"""
Copyright (c) 2013, Sarah Addams All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

Redistributions of source code must retain the above copyright notice, this list
of conditions and the following disclaimer.

Redistributions in binary form must reproduce the above copyright notice, this 
list of conditions and the following disclaimer in the documentation and/or 
other materials provided with the distribution.
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED 
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES 
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY 
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING 
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation are those 
of the authors and should not be interpreted as representing official policies, 
either expressed or implied, of the FreeBSD Project.
"""

from lxml import etree
import AvastUISchema
import AvastDefault
import stat
import sys
import os
import io

#############################################################################
#
#	This class handles the configuration data for the program
#
#############################################################################
class engineConfig:
	def valid(self):
		return self.isvalid
	
	def pathType(self, path):
		pathType=None
		statbuf = os.lstat(path)
		if (statbuf == None):
			self.reason = "'"+path+"' not found."
			return None		
		if (stat.S_ISDIR(statbuf.st_mode)):
			pathType = "folder"
		else:
			if (stat.S_ISREG(statbuf.st_mode)):
				pathType = "file"
			else:
				if (stat.S_ISBLK(statbuf.st_mode)):
					pathType = "blockdev"
		if pathType:
			return pathType
		self.reason = "'"+path+"' type not supported."
		return None
	
	def canRead(self, path):
		statbuf = os.lstat(path)
		if (statbuf):
			return ((stat.S_IMODE(statbuf.st_mode) & (stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)) != 0)
		self.reason = "'"+path+"' not found."
		return None
	
	def canWrite(self, path):
		statbuf = os.lstat(path)
		if (statbuf):
			return ((stat.S_IMODE(statbuf.st_mode) & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)) != 0)
		self.reason = "'"+path+"' not found."
		return None
	
	#
	#	This class interfaces with the XML configuration file
	#
	class xmlParser:
		def __init__(self, parent):
			self.current = None
			self.profile = {}
			self.thisProfile = None
			self.lastProfile = None
			self.parent = parent
			
		def start(self, tag, attrib):
			# print("start: {0:s}; attrib {1:s}".format(tag, attrib))
			if (tag == "current"):
				self.currentProfile = attrib['name']
			else:
				if (tag == "profile"):
					self.thisProfile = attrib['name']
					
					if (self.thisProfile != self.lastProfile):
						self.profile[self.thisProfile] = []
						self.lastProfile = self.thisProfile
				else:
					if (tag == "path"):
						A = attrib
						A['type'] = self.parent.pathType(attrib['name'])
						
						# We do NOT mess with block devices
						if ( A['type'] == "blockdev" ):
							if (A['action'] != "stop"):
								if (A['action'] != 'continue'):
									A['action'] = "continue"
						self.profile[self.thisProfile].append(A)
		
		def end(self, tag):
			# print("end: {0:s}".format(tag))
			pass
		
		def data(self, data):
			# print("data: '{0:s}'".format(data))
			pass
		
		def comment(self, text):
			pass
		
		def close(self):
			# print("close called")
			pass
	
	def currentProfile(self):
		return self.XP.currentProfile
		
	def getProfileList(self):
		return self.XP.profile
	
	def getProfileCount(self):
		return len(self.XP.profile)
	
	def getPathList(self, profileName):
		return self.XP.profile[profileName]
		
	def getPathCount(self, profileName):
		return len(self.XP.profile[profileName])
	
	def load(self, path):
		self.xmlSchema = AvastUISchema.configXMLSchema()
		if (not self.xmlSchema.selfTest()):
			raise ValueError("Configuration syntax description is corrupt - regenerate it")
		
		# Check the config against the syntax schema from the generated schema class
		relaxNGfile = self.xmlSchema.fileObject()
		try:
			F = open(path+"/AvastUI.xml", "r")
			xml = F.read()
			F.close()		
		except IOError as e:
			# raise ValueError("Can't open configuration file.")
			P = AvastProfile.configProfile()
			xml = P.string()

		doc = etree.parse(relaxNGfile)
		rng = etree.RelaxNG(doc)
		config = etree.parse(io.StringIO(xml))

		if (not rng.validate(config)):
			raise ValueError("Can't validate configuration file.")

		self.isvalid = True
		
		self.XP = self.xmlParser(self)
		
		# Configuration is good - let's use it
		parser = etree.XMLParser(target = self.XP)
		result = etree.XML(xml, parser)
		
		return True

						
	def __init__(self, path = os.environ["HOME"]+"/.avastui"):
		self.isvalid = False
		self.load(path)
		
