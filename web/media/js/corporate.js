function slider(){
	var id = $('#slider .panel:visible').attr('id');
	console.log(id);
	if($('#'+id).index() == $('#slider .panel').length){
		$('#slider .panel:first').show();
		$('#'+id).hide();
	} else {
		$('#'+id).next().show();
		$('#'+id).hide();
	}
}

$(function(){
	if($('#slider .panel').length){
		$('#slider .panel').not('#competition').hide();
		s = setInterval(slider, 10000);
	}
});