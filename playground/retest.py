# coding=utf8
# the above tag defines encoding for this document and is for Python 2.x compatibility

import re

regex = r"^.*\[(.*)\]\((.*)\)"

test_str = ("#### MotoGP 2019 Spielberg\n"
	"---\n"
	"Gemeinsam mit Philipp war ich das ganze Wochenende in Spielberg am Red Bull Ring.  \n"
	"Wir hatten eine Menge Spaß und haben uns die Rennen angesehen. Unser Seglerfreund  \n"
	"**Sepp** Kleinowitz ist in *Judenburg* zuhause. Wir haben wir ihn mit den Rädern  \n"
	"dort besucht.\n"
	"Der GP war der erste von 2 Rennen, die im Abstand von einer Woche stattfanden.  \n"
	"Im ersten Jahr nach dem Corona-Lockdown war es Red Bull gelungen, 2 Rennen\n"
	"sowohl in der MotoGP als auch in der Formel 1 am Österreichring zu organisieren.\n\n"
	"Noch ein Satz.  \n\n"
	"- [MotoGP Steiermark 8.8.2021](/redirecturl/https://www.motogp.com/de/news/2021/11/30/motogp-ruckblick-2021-der-grand-prix-der-steiermark/186377)\n"
	"- [MotoGP Österreich 16.8.2021](https://www.redbull.com/at-de/motogp-oesterreich-spielberg-2021-bericht-und-ergebnisse)\n"
	"- [Bilder von der Reise](https://www.icloud.com/sharedalbum/#B0vJtdOXmJpNlWI)\n")

subst = "<a href=\"\\2\" target=\"_blank\">\\1</a>"

# You can manually specify the number of replacements by changing the 4th argument
result = re.sub(regex, subst, test_str, 0, re.MULTILINE)

if result:
    print (result)

# Note: for Python 2.7 compatibility, use ur"" to prefix the regex and u"" to prefix the test string and substitution.
