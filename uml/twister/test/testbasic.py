import unittest

def load_twister():
    # Because twister has a config file, we need to pretend that we
    # have passed --config as command line option.
    import sys
    sys.argv=['twister', '--config=/var/www/scraperwiki/uml/uml.cfg']
    import twister
    return twister

def ensure_can_load_twister():
    """Check that we can load twister as a module."""

    twister = load_twister()
