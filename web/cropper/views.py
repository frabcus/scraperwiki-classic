from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
import re, os, urlparse, urllib, cStringIO
import Image, ImageDraw, ImageEnhance, ImageChops
import tempfile, shutil


"""Creator:        TOSHIBA e-STUDIO520
Producer:       MFPImgLib V1.0
CreationDate:   Wed May 20 08:17:33 2009
Tagged:         no
Pages:          48
Encrypted:      no
File size:      1100938 bytes
Optimized:      no
PDF version:    1.3"""

def pdfinfo(pdffile):
    cmd = 'pdfinfo "%s"' % pdffile
    result = { }
    for line in os.popen(cmd).readlines():
        try:
            c = line.index(':')
        except ValueError:
            continue
        key = line[:c].replace(" ", "")
        value = line[c+1:].strip()
        if key == "Pages":
            value = int(value)
        result[key] = value
    return result
        
        
def ParseSortCropping(cropping):
    if not cropping:
        cropping = ""
    croppings = [ ]
    clippings = [ ]
    for crop in cropping.split("/"):
        mhr = re.match('(rect|clip)_(\d+),(\d+)_(\d+),(\d+)$', crop)
        if mhr:
            if mhr.group(1) == "rect":
                croppings.append(crop)
            else:
                clippings.append(crop)
    if len(clippings) >= 2:
        del clippings[:-1]
    croppings = croppings + clippings
    newcropping = "/".join(croppings)
    if newcropping:
        newcropping += '/'
    return croppings, newcropping
        
        
def croppage(request, tinyurl, page, cropping):
    page = int(page)
    croppings, cropping = ParseSortCropping(cropping)
    
    # download file if it doesn't exist
    pdffile = os.path.join(settings.CROPPER_SOURCE_DIR, "%s.pdf" % tinyurl)
    if not os.path.isfile(pdffile):
        url = urlparse.urljoin("http://tinyurl.com/", tinyurl)
        tpdffile = tempfile.NamedTemporaryFile(suffix='.pdf')
        filename, headers = urllib.urlretrieve(url, tpdffile)
        if headers.subtype != 'pdf':
            return HttpResponse("%s is not pdf type" % url)
        shutils.copy(tpdffile.name, pdffile)
    
    data = { "page":int(page), "tinyurl":tinyurl, "cropping":cropping }
    data.update(pdfinfo(pdffile))
    
    data["losecroppings"] = [ ]
    if len(croppings) > 1:
        for i, lcropping in enumerate(croppings):
            data["losecroppings"].append(("%d"%(i+1), '/'.join([ llcropping  for llcropping in croppings  if llcropping != lcropping ])+'/'))
    if len(croppings) > 0:
            data["losecroppings"].append(("All", ""))
    
    if page > 1:
        data["prevpage"] = min(page-1, data["Pages"])
    if page < data["Pages"]:
        data["nextpage"] = max(page+1, 1)
    
    return render_to_response('cropper/cropperpage.html', data, context_instance=RequestContext(request))



def cropimg(request, format, tinyurl, page, cropping):
    page = int(page)
    cropping = cropping or ""
    
    imgfile = os.path.join(settings.CROPPER_IMG_DIR, "%s_%04d.png" % (tinyurl, page))
    if not os.path.isfile(imgfile):
        pdffile = os.path.join(settings.CROPPER_SOURCE_DIR, "%s.pdf" % tinyurl)
        imgpixwidth = 800
        cmd = 'convert -quiet -density 192 %s[%d] -resize %d %s > /dev/null 2>&1' % (pdffile, page-1, imgpixwidth, imgfile)
        os.system(cmd)
    
    croppings = filter(lambda x:x, cropping.split("/"))
    if not croppings:
        return HttpResponse(open(imgfile, "rb"), mimetype='image/png')

    pfp = Image.open(imgfile)
    swid, shig = pfp.getbbox()[2:]

    highlightrects = [ ]
    clip = None
    for crop in croppings:
        mhr = re.match('(rect|clip)_(\d+),(\d+)_(\d+),(\d+)$', crop)
        if mhr:
            dim = (int(mhr.group(2))*swid/1000, int(mhr.group(3))*swid/1000, int(mhr.group(4))*swid/1000, int(mhr.group(5))*swid/1000)
            if mhr.group(1) == "rect":
                highlightrects.append(dim)
            if mhr.group(1) == "clip":
                clip = dim
        
        
    # build the mask
    if highlightrects:
        dkpercent = 70
        dpfp = ImageEnhance.Brightness(pfp).enhance(dkpercent / 100.0)
        ddpfp = ImageDraw.Draw(dpfp)
        for rect in highlightrects:
            ddpfp.rectangle(rect, (255, 255, 255))
        cpfp = ImageChops.darker(pfp, dpfp) # makes darker of the two
    else:
        cpfp = pfp

    if clip:
        if format == "pngprev":
            p1 = Image.new("RGB", (swid, shig))
            dp1 = ImageDraw.Draw(p1)
            dp1.rectangle((0,0,swid,shig), (155, 10, 10))
            dp1.rectangle(clip, (255, 255, 255))
            cpfp = ImageChops.darker(p1, cpfp) # makes darker of the two
        else:
            cpfp = cpfp.crop(clip)
    
    imgout = cStringIO.StringIO()
    cpfp.save(imgout, "png")
    imgout.seek(0)
    return HttpResponse(imgout, mimetype='image/png')
