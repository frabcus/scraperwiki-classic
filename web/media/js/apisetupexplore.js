function rewriteApiUrl (){
    sArgs = '?';
    var aControls = $('.api_arguments dl input')
    for (var i=0; i < aControls.length; i++) {
        if($(aControls[i]).val() != ''){
	        if (i > 0) {
            	sArgs += ('&');
        	}
            sArgs += (aControls[i].id + '=' + $(aControls[i]).val());
        }
    };
    $('#aApiLink span').html(sArgs);
    $('#aApiLink').attr('href', $('#uri').val() + sArgs);
}


function APISetupExploreFunction(){
    //change the sidebar examples to links where useful
    $('#ulFormats li code').each(
        function(){
            var sText = $(this).html();
            var aLink = $('<a>' + sText + '</a>');
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

    $('#ulScraperShortNames li code').each(function()
    {
        var sText = $(this).html();
        var aLink = $('<a>' + sText + '</a>');
        aLink.click(function ()
        {
            $('#name').val(sText);
            $('#name').focus();
            rewriteApiUrl();
            return false;
        });
        $(this).html(aLink);
    });

    $('#ulUserNames li code').each(function()
    {
        var sText = $(this).html();
        var aLink = $('<a>' + sText + '</a>');
        aLink.click(function ()
        {
            $('#username').val(sText);
            $('#username').focus();
            rewriteApiUrl();
            return false;
        });
        $(this).html(aLink);
    });

    $('#ulApiKeys li code').each(
        function(){
            var sText = $(this).html();
            var aLink = $('<a>' + sText + '</a>');
            aLink.click(
                function (){
                    $('#key').val(sText);
                    $('#key').focus();
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


