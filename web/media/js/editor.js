$(document).ready(function() {
       //setup dragging
       $("#resizebar").bind("mousedown", startDrag);   // see below
    });

// dragging of middle bar code -- could move into own javascript library
var staticOffset;  
var iLastMousePos = 0;
var draggedWindow; 

function mouseY(e) { 
  return e.clientY + document.documentElement.scrollTop; 
};

function startDrag(e){
  iLastMousePos = mouseY(e);
  draggedWindow = $("#id_code").next().children(":first"); // this gets you to the iframe that you need to be resizing!!
  staticOffset = draggedWindow.height() - iLastMousePos;
  $(document).mousemove(performDrag).mouseup(endDrag);
}

function performDrag(e) {        
  var iThisMousePos = mouseY(e);
  var iMousePos = staticOffset + iThisMousePos;
  if (iLastMousePos >= (iThisMousePos)) 
      iMousePos -= 5;
  iLastMousePos = iThisMousePos;
  //$("#Dout").text("mouse drag: " + iThisMousePos)
  iMousePos = Math.max(60, iMousePos);
  draggedWindow.height(iMousePos + 'px');
  return false;

  //TODO: scrollbars should never appear on this page - the output section
  //should be squished, and dragging stopped when only the buttons are visible
}

function endDrag(e) {
  $(document).unbind('mousemove', performDrag).unbind('mouseup', endDrag);
  staticOffset = null;
  iLastMousePos = 0;
  draggedWindow = null; 
}

function showPopup(sId){

    //show or hide the relivant block
    $('#popups div.popup_item').each(function (i) {
      if (this.id == sId) {

          //show
          $(this).css({
          		display:'block',
          		height:$(window).height(),
          		position:'absolute'
          	});

          //add background
         $('#popups #overlay').css({
          		display:'block',
          		width: $(window).width(),
          		height:$(window).height(),
          	});

      } else {
          this.style.display = "none";
      }
    });
}

function hidePopup(){
    
    //hide overlay
    $('#popups #overlay').css({
     		display:'none'
     });
     
     //hide popups
    $('#popups div.popup_item').each(function (i) {
        $(this).css({
        		display:'none'
        	});
    });        
         
}