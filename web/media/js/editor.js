$(document).ready(function() {

function showPopup(sId){

    //show or hide the relivant block
    $('#popups div.popup_item').each(function (i) {
      if (this.id == sId) {
          popupStatus = 1;
          //show
          $(this).css({
              // display:'block',
          		height:$(window).height()-200,
          		position:'absolute'
          	});
          $(this).fadeIn("fast")
          
          //add background
         $('#popups #overlay').css({
          		width: $(window).width(),
          		height:$(window).height(),
          	});
         $('#popups #overlay').fadeIn("fast")
         
      } else {
          this.style.display = "none";
      }
    });
}

$(document).keypress(function(e){  
  if(e.keyCode==27 && popupStatus==1){  
    hidePopup();  
  }  
});

$('.popupClose').click(function() {
  hidePopup();
})

$('#overlay').click(function() {
  hidePopup();
})

function hidePopup(){
     // Hide popups
    $('#popups div.popup_item').each(function (i) {
        $(this).fadeOut("fast")
      });        
    
    // Hide overlay
    $('#popups #overlay').fadeOut("fast")      
    popupStatus = 0;   
}


// auto save a draft
setInterval(function() {
  $.ajax({
    type : 'POST',
    URL : window.location.pathname,
    data: ({
      title : $('#id_title').val(),
      code : codeeditor.getCode(),
      action : 'save',
      }),
    dataType: "html",
    success: function(){
            // Attempt at niceish notification, it needs work though ;)
             $('#notifications').fadeOut(800, function() {
               $('#notifications').html('Draft Auto Saved');
               $('#notifications').fadeIn(800);                       
               // wirteToConsole('Auto Saved')
             });
             
          }
    })
}, 60000);


// Meta form
$('#meta_fields_mini').appendTo($('#meta_form'))
$('#meta_fields_mini').attr('id', 'meta_fields')
$('#id_title').after('<a href="" id="meta_form_edit">Edit scraper info</a>')

$('#meta_form_edit').click(function() {
  // Only add the save button if it's not there already
  if (!$('#meta_form #save').length) {    
    $('#save').clone().appendTo($('#meta_form'))
  }
  showPopup('meta_form')
  return false
});


// clear console
$('#clear').click(function() {
  c = $('body', $('#console').contents())
  c.fadeOut("fast", function() {
    $('body', $('#console').contents()).html('')    
  })
  c.fadeIn()
});


// Diff button
$('.editor_controls #notifications').before('<input type="button" value="Diff committed version" name="diff" id="diff" />');
$('.editor_controls #diff').click(function() {      
  $.ajax({
    type : 'POST',
    url : '/editor/diff/'+short_name,
    data: ({
      code : codeeditor.getCode(),
      }),
    dataType: "html",
    success: function(diff){
      $('#diff pre').text(diff);
      showPopup('diff');                 
    }
    });
  });



// Run button
$('.editor_controls #notifications').before('<input type="button" value="Run" name="run" id="run" />');
$('.editor_controls #run').click(function() { 
  if (run_type == 'firestarter_apache') {
      
      $('#editor').bind('form-pre-serialize', null, function(foo, options) {
        $('#editor #id_code').text(codeeditor.getCode())
        
      })
      
      $('#editor').ajaxSubmit({
          target: '#console',
          action: '/editor/run_code',
      });

      
      return false; // <-- important!
  } else {
    $.ajax({
      type : 'POST',
      url : '/editor/run_code',
      data: ({
        code : codeeditor.getCode(),
        guid : scraper_guid,        
        }),
      dataType: "html",
      success: function(code){
        wirteToConsole(code);          
      }
      });    
  }    

  });

});
