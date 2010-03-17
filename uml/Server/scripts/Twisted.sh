#!/bin/sh

cd /var/www/scraperwiki/uml
. /var/www/scraperwiki/bin/activate
exec ./Server/scripts/Twisted.py $*
