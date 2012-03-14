function slider(){
	var old_id = $('#slider .panel:visible').attr('id');
	if($('#'+old_id).index() == $('#slider .panel').length - 1){
		var new_id = $('#slider .panel:first').attr('id');
	} else {
		var new_id = $('#'+old_id).next().attr('id');
	}
	$('#'+old_id).css('z-index',0);
	$('#'+new_id).css('z-index',1).fadeIn(1000, function(){
		$('#'+old_id).hide();
	});
}



$(function(){
	if($('#slider .panel').length){
		$('#slider .panel').not('#competition').hide();
		s = setInterval(slider, 10000);
	}
	
	$('abbr').colorTip({color: 'white'});
	
});