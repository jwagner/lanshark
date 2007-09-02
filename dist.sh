mkdir dist/lanshark
cp -R setup.py dist/lanshark
cp -R src dist/lanshark
cp -R share dist/lanshark
cp CHANGELOG INSTALL README HACKING LICENSE dist/lanshark
cd dist
tar -cjf lanshark-0.0.0.tar.bz2 lanshark/
rm -rf lanshark
