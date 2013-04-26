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

def validate(xml, xmlSchema):
	if (not xmlSchema.selfTest()):
		raise ValueError("Syntax description was corrupt - regenerate the module.")
	
	# Check the config against the syntax schema from the generated schema class
	relaxNGfile = xmlSchema.fileObject()
		
	doc = etree.parse(relaxNGfile)
	rng = etree.RelaxNG(doc)
	config = etree.parse(io.StringIO(xml))
		
	return rng.validate(config)


#
#	This class handles the configuration data for the program
#
#	CONFIGURATION STORAGE
#	=====================
#
#	The class employs xml for storage, syntax checking the data against 
#	a RelaxNG compact syntax specification in the file AvastUI.rnc.
#
#	The RelaxNG syntax spec is run through trang to generate an XML doc, 
#	thence through xml2py, which serielises it and stores it as a python 
#	class. The class is subsequently available as a module import.
#
#	The default configuration is also stored as a python module.
#
#	See the makefile and xml2py for details of this process.
#
#	CONFIGURATION DATA STRUCTURES
#	=============================
#
#	engineConfig maintains the data read from a configuration file in two
#	member variables: 'XP.current' and 'XP.profile'. The 'current' variable
#	is a simple string naming the current profile.
#
#	The 'profile' variable is an associative array of profiles indexed by 
#	the profile name. 
#
#	Each profile maintains a numerically indexable list of paths.
#
# 	Each path has three attributes - type, name and action indexed 
#	by 'type'|'name' or 'action'. 
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
	
	# Return the current profile
	def currentProfile(self):
		# (if it exists)
		if (self.XP.profile[self.XP.currentProfile]):
			return self.XP.currentProfile
		else:
			# elsewise the default if that exists
			if (self.XP.profile['default']):
				self.XP.currentProfile = "default"
				return self.XP.currentProfile
			else:
				# Elsewise the key of the first profile in the array
				for K in self.XP.profile.keys():
					self.XP.currentProfile = K
					return K
		# else nar-theeng (should never happen)
		return None
			
	def getProfileList(self):
		return self.XP.profile
	
	def getProfileCount(self):
		return len(self.XP.profile)
	
	def getPathList(self, profileName):
		return self.XP.profile[profileName]
		
	def getPathCount(self, profileName):
		return len(self.XP.profile[profileName])
	
	def store(self, path):
		pass
	
	def load(self, path):
		xmlSchema = AvastUISchema.configXMLSchema()
		
		# Try to open a config file. If we can't open a config file, we use the default
		try:
			F = open(path+"/AvastUI.xml", "r")
			xml = F.read()
			F.close()		
			src = ".avastui/AvastUI.xml"
		except IOError as e:
			P = AvastProfile.configDefault()
			if (not P.selfTest()):
				raise ValueError("Module-sourced default config is corrupt - regenerate it.")
			src = "module-based default"
			xml = P.string()

		# Either way, we end up with an xml configuration that we need to syntax check
		if (not validate(xml, xmlSchema)):
			raise ValueError("Configuration file ({0:s})failed syntax check.".format(src))

		self.isvalid = True
		
		self.XP = self.xmlParser(self)
		
		# Configuration is good - let's use it
		parser = etree.XMLParser(target = self.XP)
		result = etree.XML(xml, parser)
		
		return True

						
	def __init__(self, path = os.environ["HOME"]+"/.avastui"):
		self.isvalid = False
		self.load(path)
		
