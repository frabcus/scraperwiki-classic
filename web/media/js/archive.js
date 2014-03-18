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

*/

var archive_messages = {
  docs_api: function(){
    $('#archive_placeholder_top')
      .addClass('yellow')
      .html('<p style="font-weight:bold">The ScraperWiki Classic Web API has been retired.</p><p>This page has been retained for posterity. New users should try our <a href="https://scraperwiki.com/tools/code-in-browser">Code in your browser</a> tool.</p>')
      .show()
  }
}

$(function(){
  if(/docs[/]api/.test(window.location.pathname)){
    archive_messages.docs_api()
  }
})
