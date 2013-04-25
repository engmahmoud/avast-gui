all: AvastUISchema.py AvastUI.py AvastDefault.py

clean:
	rm -f AvastUISchema.py AvastUI.py AvastDefault.py

#############################################################
#
# The syntax for the configuration data for this program is 
# specified as a RelaxNG compact syntax description.
#
# The compact syntax file is translated to XML via 'trang'
# and the XML file is then compress, base64 encoded,
# wrapped in a named python class and written to disk as 
# a basic python module. The class validates the stored 
# data before restoring it and returning it as an ioString 
# memory file or alternatively, a simple python string.
#
# The target below regenerates the module whenever the 
# syntax description is altered.
#
#############################################################

AvastUISchema.py: AvastUI.rnc xml2py
	trang AvastUI.rnc AvastUI.rng
	./xml2py -i AvastUI.rng -o - -v configXMLSchema >AvastUISchema.py

#############################################################
#
# This target regenerates the user interface code if the 
# base user interface description xml is altered
#
#############################################################

AvastUI.py: Avast.ui
	pyuic4 Avast.ui -o AvastUI.py

#############################################################
#
# This target encodes a default profile as a python class
#
#############################################################

AvastDefault.py: AvastDefault.xml xml2py
	./xml2py -i AvastDefault.xml -o - -v configDefault >AvastDefault.py
