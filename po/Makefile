all: mo
mo: *.po
	msgfmt --output-file=../share/locale/en_US/LC_MESSAGES/lanshark.mo en_US.po
	msgfmt --output-file=../share/locale/de/LC_MESSAGES/lanshark.mo de.po
	msgfmt --output-file=../share/locale/bg/LC_MESSAGES/lanshark.mo bg.po
	msgfmt --output-file=../share/locale/es/LC_MESSAGES/lanshark.mo es.po
	msgfmt --output-file=../share/locale/ru/LC_MESSAGES/lanshark.mo ru.po
*.po: lanshark.pot
	 msgmerge -U de.po lanshark.pot
	 msgmerge -U bg.po lanshark.pot
	 msgmerge -U es.po lanshark.pot
	 msgmerge -U ru.po lanshark.pot
lanshark.pot: ../src/lansharkgui
	xgettext --language=Python --keyword=_ --output=lanshark.pot ../src/lansharkgui
