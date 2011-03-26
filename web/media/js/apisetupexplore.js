var prev_aName = ''; 
function rewriteApiUrl()
{
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

    var aName = $('.api_arguments dl input#name').val(); 
    if (aName == prev_aName)
        return; 

    prev_aName = aName; 
    if (aName)
    {
        $('#aScraperLink').text(aName); 
        $('#aScraperLink').attr('href', "/scrapers/"+aName); 
        $('#otherapis').text(""); 
        var aName = $('.api_arguments dl input#name').val();

        for (var i = 0; i < otherapis.length; i++)
            $('#otherapis').append('<li><a href="'+otherapis[i]+'?name='+aName+'">'+otherapis[i]+'?name='+aName+'</a></li>'); 
        $('#listtables').empty(); 
        $('#scraperdetails').show(); 
    }
    else
        $('#scraperdetails').hide(); 
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
    $('.api_arguments dl input').each(function() {$(this).keyup(rewriteApiUrl)}); 

    $('#scraperlisttables').click(function()
    {
        var aName = $('.api_arguments dl input#name').val();
        $('#listtables').html("<li>Loading...</li>"); 
        $.ajax({url:getinfourl, dataType:"jsonp", data:{name:aName, quietfields:"code|runevents|userroles"}, error: function(jq, status) { alert(status); }, success:function(v) 
        { 
            $('#listtables').empty(); 
            if (v && v[0].datasummary && v[0].datasummary.tables)
            {
                for (var tablename in v[0].datasummary.tables)
                {
                    var table = v[0].datasummary.tables[tablename]; 
                    $('#listtables').append('<li><b>'+tablename+'</b> ['+table.count+'] '+table.sql+'</li>'); 
                }
                $('#listtables li').click(function() 
                {
                    $('#tablename').val($(this).find("b").text()); 
                    $('#query').val("select * from "+$(this).find("b").text()+" limit 10"); 
                }); 
            }
            else
                $('#listtables').html("<li>No tables</li>"); 
        }}); 
    }); 

    rewriteApiUrl(); // initialize
}


