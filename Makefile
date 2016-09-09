# Makefile for a PyQGIS plugin

all: compile

dist: package

install: copy2qgis

PY_FILES = oauth_settings.py OAuthServer.py __init__.py
UI_FILES =
RESOURCE_FILES =

compile: $(UI_FILES) $(RESOURCE_FILES)

%.py : %.qrc
	pyrcc4 -o $@ $<

%.py : %.ui
	pyuic4 -o $@ $<



clean:
	find ./ -name "*.pyc" -exec rm -rf \{\} \;
	rm -f ../OAuthServer.zip

package:
	cd .. && find OAuthServer/  -print|grep -v Make | grep -v zip | grep -v .git | grep -v .pyc| grep -v .env | grep -v 'run_test' |zip OAuthServer.zip -@

localrepo:
	cp ../OAuthServer.zip ~/public_html/qgis/OAuthServer.zip

copy2qgis: package
	unzip -o ../OAuthServer.zip -d ~/.qgis/python/plugins

check test:
	@echo "Sorry: not implemented yet."
