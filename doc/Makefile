all: ../README ../INSTALL ../HACKING ../CHANGELOG
clean:
	rm ../README ../INSTALL ../HACKING ../CHANGELOG
../README: README.in HEADER format.py
	./format.py README.in ../README
../INSTALL: INSTALL.in HEADER format.py
	./format.py INSTALL.in ../INSTALL
../HACKING: HACKING.in HEADER format.py
	./format.py HACKING.in ../HACKING
../CHANGELOG: CHANGELOG.in HEADER format.py
	./format.py CHANGELOG.in ../CHANGELOG
