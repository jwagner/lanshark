all: mo
mo: *.po
	msgfmt --output-file=../share/locale/en_US/LC_MESSAGES/lanshark.mo en_US.po
	msgfmt --output-file=../share/locale/de/LC_MESSAGES/lanshark.mo de.po
	msgfmt --output-file=../share/locale/bg/LC_MESSAGES/lanshark.mo bg.po
	msgfmt --output-file=../share/locale/es/LC_MESSAGES/lanshark.mo es.po
	msgfmt --output-file=../share/locale/ru/LC_MESSAGES/lanshark.mo ru.po
	msgfmt --output-file=../share/locale/fr/LC_MESSAGES/lanshark.mo fr.po
	msgfmt --output-file=../share/locale/he/LC_MESSAGES/lanshark.mo he.po
	msgfmt --output-file=../share/locale/hu/LC_MESSAGES/lanshark.mo hu.po
	msgfmt --output-file=../share/locale/ja/LC_MESSAGES/lanshark.mo ja.po
	msgfmt --output-file=../share/locale/nl/LC_MESSAGES/lanshark.mo nl.po
	msgfmt --output-file=../share/locale/pt_BR/LC_MESSAGES/lanshark.mo pt_BR.po
	msgfmt --output-file=../share/locale/sk/LC_MESSAGES/lanshark.mo sk.po
	msgfmt --output-file=../share/locale/sv/LC_MESSAGES/lanshark.mo sv.po
	msgfmt --output-file=../share/locale/uk/LC_MESSAGES/lanshark.mo uk.po
*.po: lanshark.pot
	 msgmerge -U de.po lanshark.pot
	 msgmerge -U bg.po lanshark.pot
	 msgmerge -U es.po lanshark.pot
	 msgmerge -U ru.po lanshark.pot
	 msgmerge -U fr.po lanshark.pot
	 msgmerge -U he.po lanshark.pot
	 msgmerge -U hu.po lanshark.pot
	 msgmerge -U ja.po lanshark.pot
	 msgmerge -U nl.po lanshark.pot
	 msgmerge -U pt_BR.po lanshark.pot
	 msgmerge -U sk.po lanshark.pot
	 msgmerge -U sv.po lanshark.pot
	 msgmerge -U uk.po lanshark.pot
lanshark.pot: ../src/lansharkgui
	xgettext --language=Python --keyword=_ --output=lanshark.pot ../src/lansharkgui
