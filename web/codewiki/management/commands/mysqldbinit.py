#! /usr/bin/env python
# David Jones, ScraperWiki Limited
# 2011-11-16

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

import MySQLdb as db

import logging
logging.basicConfig()

class Command(BaseCommand):
    def handle(self, *args_, **kwargs_):
        return
        # TODO: add option to pass along MySQL root password.

        conn = db.connect(user='root', passwd='')
        cursor = conn.cursor()
        cursor.execute("""
          CREATE DATABASE %(NAME)s CHARACTER SET utf8;
          CREATE USER %(USER)r@'localhost' IDENTIFIED BY %(PASSWORD)r;
          GRANT ALL ON %(NAME)s.* TO %(USER)r@'localhost';
          """ % settings.DATABASES['default'])
        cursor.close()
        conn.close()

