/*

This file should be used to inject messages about our products/services into archived Classic pages.

There are three placeholders into which you can inject content:
 - #archive_placeholder_top appears between the nav bar and the blue page header
 - #archive_placeholder_middle appears between the blue page header and the white content area
 - #archive_placeholder_bottom appears below the white content area

The placeholders are hidden by default. You will need to use .show() to reveal them.

The placeholders have a white background and grey border by default. #archive_placeholder_top
and #archive_placeholder_bottom can be made transparent by adding a class of "transparent".

You add a coloured background to any placeholder by adding a class of "yellow", "orange",
"green" or "blue".

You can add rounded buttons to your messages using <a class="archive_button"></a>. Buttons
are blue by default. You can add a class of "green" or "orange" to change their colour.

*/

var code_in_browser_url = 'https://scraperwiki.com/tools/code-in-browser'
var scraping_docs_url = 'https://github.com/frabcus/code-scraper-in-browser-tool/wiki'
var professional_services_url = 'https://scraperwiki.com/professional'

var archive_messages = {
  docs_api: function(){
    $('#archive_placeholder_top')
      .addClass('yellow')
      .html('<h3>The ScraperWiki Classic Web API has been retired.</h3><p>This page has been retained for posterity. New users should try our <a href="' + code_in_browser_url + '">Code in your browser</a> tool.</p>')
      .show()
  },
  docs_home: function(){
    $('#archive_placeholder_top')
      .addClass('orange')
      .html('<h3>ScraperWiki Classic has been retired.</h3><p>This documentation has moved to a <a href="' + scraping_docs_url + '">wiki on Github</a>.</p>')
      .show()
  },
  docs_general: function(){
    $('#archive_placeholder_top')
      .addClass('yellow')
      .html('<h3>ScraperWiki Classic has been retired.</h3><p>Why not try our new <a href="' + code_in_browser_url + '">Code in your browser</a> tool? It&rsquo;s free and awesome!</p>')
      .show()
  },
  browse: function(){
    $('#archive_placeholder_top')
      .addClass('yellow')
      .html('<p><strong>ScraperWiki has moved.</strong> <a href="' + code_in_browser_url + '" class="archive_button orange">Create a new scraper</a> with our new online editor, or contact our <a href="' + professional_services_url + '" class="archive_button orange">Professional Services team</a></p>')
      .show()
  }
}

var url_matches = function(regexp){
  return regexp.test(window.location.pathname)
}

$(function(){
  if (url_matches(/^[/]docs[/]api/)) {
    archive_messages.docs_api()
  } else if (url_matches(/^[/]docs[/](python|ruby|php)[/]?$/)) {
    archive_messages.docs_home()
  } else if (url_matches(/^[/]docs[/]/)) {
    archive_messages.docs_general()
  } else if (url_matches(/^[/]browse[/](scrapers|views)[/]?$/)){
    archive_messages.browse()
  }
})
