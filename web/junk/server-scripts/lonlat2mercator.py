#!/usr/bin/python
import math

def deg_rad(ang):
  return ang*(math.pi/180.0)

def merc_x(lon):
  r_major=6378137.000
  return r_major*deg_rad(lon)

def merc_y(lat):
  if lat>89.5:lat=89.5
  if lat<-89.5:lat=-89.5
  r_major=6378137.000
  r_minor=6356752.3142
  temp=r_minor/r_major
  es=1-(temp*temp)
  eccent=math.sqrt(es)
  phi=(lat*math.pi)/180
  sinphi=math.sin(phi)
  con=eccent*sinphi
  com=.5*eccent
  con=math.pow(((1.0-con)/(1.0+con)),com)
  ts=math.tan(.5*((math.pi*0.5)-phi))/con
  y=0-r_major*math.log(ts)
  return y

def merc_y(lat):
    llat = math.log(math.tan((90 + lat) * math.pi / 360)) / (math.pi / 180);
    llat = llat * 20037508.34 / 180;
    return llat

