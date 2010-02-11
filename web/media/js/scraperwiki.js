function setupCodeViewer(iLineCount){
    var oCodeEditor;
    if(iLineCount < 20){
        iLineCount = 20;
    }
    this.lineCount = iLineCount
    $(document).ready(function(){

       oCodeEditor = CodeMirror.fromTextArea("txtScraperCode", {
           parserfile: ["../contrib/python/js/parsepython.js"],
           stylesheet: "/media/CodeMirror-0.65/contrib/python/css/pythoncolors.css",

           path: "/media/CodeMirror-0.65/js/",
           textWrapping: true, 
           lineNumbers: true, 
           indentUnit: 4,
           readOnly: true,
           tabMode: "spaces", 
           autoMatchParens: true,
           width: '100%',
           height: this.lineCount + 'em',           
           parserConfig: {'pythonVersion': 2, 'strictErrors': true}

       });
      });
}

function APISetupExploreFunction(){

    //link up the call button to change a few bits of text
    $('#btnCallMethod').click(
        function(){
            $('.explorer_response h2').html('Function response');
            return true;
        }
    );

    //change the sidebar examples to links where useful
    $('#ulFormats li code').each(
        function(){
            var sText = $(this).html();
            var aLink = $('<a href="#">' + sText + '</a>');
            aLink.click(
                function (){
                    $('#format').val(sText);
                    $('#format').focus();
                    rewriteApiUrl();                    
                }
            );
            $(this).html(aLink);
        }
    );

    $('#ulScraperShortNames li code').each(
        function(){
            var sText = $(this).html();
            var aLink = $('<a href="#">' + sText + '</a>');
            aLink.click(
                function (){
                    $('#name').val(sText);
                    $('#name').focus();
                    rewriteApiUrl();
                    return false;
                }
            );
            $(this).html(aLink);
        }
    );

    //linkup the texboxes to rewrite the API url
    $('.api_arguments dl input').each(
        $(this).keyup(
            function(){
                rewriteApiUrl();
            }
        )
    );
}

function rewriteApiUrl (){
    sArgs = '?key=[your api key]';
    var aControls = $('.api_arguments dl input')
    for (var i=0; i < aControls.length; i++) {
        if($(aControls[i]).val() != ''){
            sArgs += ('&' + aControls[i].id + '=' + $(aControls[i]).val());
        }
    };
    $('#aApiLink span').html(sArgs);
    $('#aApiLink').attr('href', $('#uri').val() + sArgs);
}


function setupButtonConfirmation(sId, sMessage){
    $('#' + sId).click(
        function(){
            var bReturn = false;
            if (confirm(sMessage) == true){
                bReturn = true;
            }
            return bReturn
        }    
    );
}

function setupDataMap(){

    // Setup the map
    oNavigation = new OpenLayers.Control.Navigation();
    oNavigation.zoomWheelEnabled = false;
    oPanZoomBar = new OpenLayers.Control.PanZoomBar();
    
    oMap = new OpenLayers.Map ("divDataMap", {
          controls:[
              oNavigation,
              oPanZoomBar,
              new OpenLayers.Control.Attribution()],
          maxExtent: new OpenLayers.Bounds(-20037508.34,-20037508.34,20037508.34,20037508.34),
          maxResolution: 156543.0399,
          numZoomLevels: 10,
          units: 'm',
          projection: new OpenLayers.Projection("EPSG:900913"),
          displayProjection: new OpenLayers.Projection("EPSG:4326")
      } );


      // Add OSM tile and marker layers
      oMap.addLayer(new OpenLayers.Layer.OSM.Mapnik("Osmarender"));

      oMarkersLayer = new OpenLayers.Layer.Markers("Markers");
      oMap.addLayer(oMarkersLayer);      
      
     // Make icon
     var oIconSize = new OpenLayers.Size(21,25);
     var oIconOffset = new OpenLayers.Pixel(-(oIconSize.w/2), -oIconSize.h);
     var oIcon = new OpenLayers.Icon('http://www.openstreetmap.org/openlayers/img/marker.png',oIconSize, oIconOffset);
     
     // Get data
     var oData = eval('('+ $('#hidMapData').val() + ')');
     
     //find where the latlng field is
     var iLatLngIndex = 0;
     for (var i=0; i < oData.headings.length; i++) {
         if(oData.headings[i] == 'latlng'){
             iLatLngIndex = i;
         }
     };

     for (var i=0; i < oData.rows.length; i++) {
         
         //get the lat/lng
         iLat = oData.rows[i][iLatLngIndex].split(',')[1].replace(')', '');
         iLng = oData.rows[i][iLatLngIndex].split(',')[0].replace('(', '');         
         var oLngLat = new OpenLayers.LonLat(iLat, iLng).transform(new OpenLayers.Projection("EPSG:4326"), oMap.getProjectionObject());         

         //work out the html to show
         var sHtml = '<table>';
         for (var ii=0; ii < oData.rows[i].length; ii++) {
            sHtml += ('<tr><td>' + oData.headings[ii]   + '</td>');
            sHtml += ('<td>' + oData.rows[i][ii] + '</td></tr>');
         };
         sHtml += '</table>';

         //make the marker
         var oMarker = new OpenLayers.Marker(oLngLat,oIcon.clone())
         oMarkersLayer.addMarker(oMarker);
         oMarker.html = sHtml;
         
         oMarker.events.register("mousedown", oMarker,
            function(o, b){
                var oPopup = new OpenLayers.Popup.AnchoredBubble("item", this.lonlat, 
                    new OpenLayers.Size(350,250), this.html, this.icon, true);
                oMap.addPopup(oPopup, true);

            }
        );              
           
     };
     
     //zoom to extent of the markers
     oMap.zoomToExtent(oMarkersLayer.getDataExtent());    

}

function setupScroller(){
    
    //left right buttons
    $('.scroller a.scroll_left').click(
        function(){
            scrollScroller('left')
            return false;
        }
    );
    $('.scroller a.scroll_right').click(
        function(){
            scrollScroller('right')
            return false;
        }
    );
    
    //resize
    $(window).resize(
        function(){
            var iNewWidth = $('.scroller .scroller_wrapper').width() / 2;
            if(iNewWidth < 250){
                console.debug(iNewWidth)
               iNewWidth = 250;
            }
            $('.scroller .scroll_item').width(iNewWidth);
        }
    );
}

function scrollScroller(sDirection){

    //can scroll?
    var bCanScroll = true;
    var iCurrentLeft = parseInt($('.scroller .scroll_items').css('left'));
    //console.debug(iCurrentLeft)
    //console.debug(sDirection)
    if(sDirection == 'left' && iCurrentLeft >= 0){
        bCanScroll = false;
    }
    

    if(bCanScroll == true){
        //get the width of one item
        iWidth = $('.scroller .scroll_items :first-child').outerWidth() + 18;
        sWidth = ''
        if(sDirection == 'right'){
            sWidth = '-=' + iWidth
        }else{
            sWidth = '+=' + iWidth        
        }

        //scroll   
        $('.scroller .scroll_items').animate({
          left: sWidth
        }, 500);
    }
    
}

function setupIntroSlideshow(){
    $('.slide_show').cycle({
		fx: 'fade',
        speed:   1000, 
        timeout: 8000, 
        next:   '.slide_show', 
        pause:   1,
        pager: '.slide_nav',
        autostop: 0
	});
}