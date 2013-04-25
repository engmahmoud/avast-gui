all: AvastUISchema.py AvastUI.py

clean:
	rm -f AvastUISchema.py AvastUI.py

AvastUISchema.py: AvastUI.rnc xml2py
	trang AvastUI.rnc AvastUI.rng
	./xml2py -i AvastUI.rng -o - -v configXMLSchema >AvastUISchema.py

AvastUI.py: Avast.ui
	pyuic4 Avast.ui -o AvastUI.py
