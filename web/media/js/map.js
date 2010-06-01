
function setupDataMap(oData, sUrl){

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
      oMarkersLayer = new OpenLayers.Layer.Markers("Markers", {attribution:"<a href='" + sUrl + "' target='_parent'>ScraperWiki</a>"});
      oMap.addLayer(oMarkersLayer);      

      oMap.addLayer(new OpenLayers.Layer.OSM.Mapnik("Osmarender"));

      
     // Make icon (derived from http://www.openstreetmap.org/openlayers/img/marker.png -- could later include variations on markers)
     markers = ["red", "blue", "purple", "green", "white", "black"];
     oIcons = { }
     for (var i=0; i < markers.length; i++) {
        var oIconSize = new OpenLayers.Size(21,25);
        var oIconOffset = new OpenLayers.Pixel(-(oIconSize.w/2), -oIconSize.h);
        var oIcon = new OpenLayers.Icon('/media/images/mapmarkers/' + markers[i] + 'marker.png', oIconSize, oIconOffset);
        oIcons[markers[i]] = oIcon;
     }
     
     //find where the latlng field is
     var iLatLngIndex = -1;
     var iColourIndex = -1; 
     for (var i=0; i < oData.headings.length; i++) {
         if(oData.headings[i] == 'latlng'){
             iLatLngIndex = i;
         }
         if(oData.headings[i] == 'colour'){
             iColourIndex = i;
         }
         if(oData.headings[i] == 'chart'){
             iChartIndex = i;
         }
     };
     if (iLatLngIndex == -1)
        return; // nothing more to look for

     for (var i=0; i < oData.rows.length; i++) {
         if(oData.rows[i][iLatLngIndex] == ""){
             continue;
         }

         //get the lat/lng
         iLat = oData.rows[i][iLatLngIndex].split(',')[1].replace(')', '');
         iLng = oData.rows[i][iLatLngIndex].split(',')[0].replace('(', '');         
         var oLngLat = new OpenLayers.LonLat(iLat, iLng).transform(new OpenLayers.Projection("EPSG:4326"), oMap.getProjectionObject());         

         //work out the html to show
         var sHtml = '<table>';
         for (var ii=0; ii < oData.rows[i].length; ii++) {
            sHtml += ('<tr><td>' + oData.headings[ii] + '</td>');
            sdata = oData.rows[i][ii]
            if (sdata.substring(0, 5) == "http:") 
               sdata = ('<a href="' + sdata + '">' + sdata + '</a>');
            sHtml += ('<td>' + sdata + '</td></tr>');
         };
         sHtml += '</table>';


         //make the marker from the chart or the colour
         var icon = undefined; 
         try {
            if (iChartIndex != -1) {
                chartdata = eval('(' + oData.rows[i][iChartIndex] + ')');
                var oIconSize = new OpenLayers.Size(chartdata['Size'][0], chartdata['Size'][1]);
                var oIconOffset = new OpenLayers.Pixel(chartdata['Pixel'][0], chartdata['Pixel'][1]);
                icon = new OpenLayers.Icon(chartdata['chartimg'], oIconSize, oIconOffset);
           }
         } catch (err) { /*alert(err)*/; }

         if (icon == undefined) { 
            colour = "red"; 
            if ((iColourIndex != -1) && (oData.rows[i][iColourIndex] in oIcons))
                colour = oData.rows[i][iColourIndex];
            icon = oIcons[colour].clone(); 
         }

         var oMarker = new OpenLayers.Marker(oLngLat, icon)

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
