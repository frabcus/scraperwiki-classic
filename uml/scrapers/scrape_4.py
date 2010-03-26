import urllib2
text = urllib2.urlopen('ftp://sidads.colorado.edu/DATASETS/NOAA/G02135/Jan/N_01_area.txt').read()
print text
