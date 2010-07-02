$(function(){
    var parts = Array();
    parts.push('<div id="langDialog" title="Choose a language">');
    parts.push('Please choose a language to write the scraper in');
    parts.push('<ul>');
    parts.push('<li><input type="radio" name="languages" value="Python" checked>Python<br></li>');
    parts.push('<li><input type="radio" name="languages" value="PHP">PHP<br></li>');
    parts.push('</ul>');
    parts.push('<br/>');
    parts.push('<input type="button" id="languageOK" value="OK" class="button"/>&nbsp;&nbsp;<input type="button" id="languageClose" value="Cancel" class="button"/>');
    parts.push('</div>');
    $('body').append(parts.join(''));
    $('#langDialog').dialog({autoOpen: false, draggable: false, resizable: false});
    $('a.editor').click(function(){
        if(!$('#langDialog').dialog('isOpen')){
          $('#langDialog').dialog('open');
        }
        return false;
    });
    $('#languageClose').click(function(){
        $('#langDialog').dialog('close');
    });
    $('#languageOK').click(function(){
        window.location.replace('/editor/new/' + $("input[name='languages']:checked").val());
    });
});
