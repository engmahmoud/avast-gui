AvastUISchema.py: AvastUI.rnc xml2py
	trang AvastUI.rnc AvastUI.rng
	./xml2py -i AvastUI.rng -o - -v configXMLSchema >AvastUISchema.py
