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
        
        
def croppage(request, tinyurl, page, cropping):
    page = int(page)
    cropping = cropping or ""
    
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
    
    croppings = filter(lambda x:x, cropping.split("/"))
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


def cropimg(request, tinyurl, page, cropping):
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

    highlightrects = [ ]
    for crop in croppings:
        mhr = re.match('rect_(\d+),(\d+)_(\d+),(\d+)$', crop)
        if mhr:
            highlightrects.append((int(mhr.group(1)), int(mhr.group(2)), int(mhr.group(3)), int(mhr.group(4))))
        
    dkpercent = 70

    p1 = Image.new("RGB", (500, 500))

    pfp = Image.open(imgfile)
    swid, shig = pfp.getbbox()[2:]

    dpfp = ImageEnhance.Brightness(pfp).enhance(dkpercent / 100.0)
    ddpfp = ImageDraw.Draw(dpfp)
    for rect in highlightrects:
        srect = (rect[0] * swid / 1000, rect[1] * swid / 1000, rect[2] * swid / 1000, rect[3] * swid / 1000)
        ddpfp.rectangle(srect, (255, 255, 255))

    cpfp = ImageChops.darker(pfp, dpfp)

    imgout = cStringIO.StringIO()
    cpfp.save(imgout, "png")
    imgout.seek(0)
    return HttpResponse(imgout, mimetype='image/png')
