require  'scraperwiki/simple_html_dom.php'   ;

$html = file_get_html('http://scraperwiki.com/hello_world.html') ;
foreach ($html->find('table') as $table)
   foreach ($table->find('tr') as $tr)
      foreach ($tr->find('td') as $td)
      {  print $td->innertext . "\n" ;
         sw_data_save (array('message'), array('message' => $td->innertext)) ;
      }
