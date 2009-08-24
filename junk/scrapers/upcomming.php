<?php

require_once(dirname(__FILE__) . "/php_includes/config.php");
require_once(dirname(__FILE__) . "/php_includes/functions.php");

	$base_url = "http://upcoming.yahoo.com/syndicate/v2/search_all/?search_placeid=";
	$cities = array(".2P4je.dBZgMyQ");

	//loop through cities
	foreach ($cities as $city) {
		
		print "scraping location " . $city;
		
		$xml = file_get_contents($base_url . $cities);
		$xml = str_replace("\r\n","", $xml);
		$xml = str_replace("\n","", $xml);		

		// get items
		$item_regex = "/<item>(.*?)<\/item>/";
		preg_match_all($item_regex, $xml, $item_matches, PREG_PATTERN_ORDER);

		foreach ($item_matches[0] as $item_match){

			//title
			$title_regex = "/<title>(.*?)<\/title>/";
			preg_match_all($title_regex, $item_match, $title_matches, PREG_PATTERN_ORDER);
			$title = str_replace('<title>', "", $title_matches[0][0]);
			$title = str_replace('</title>', "", $title);

			//link
			$link_regex = "/<link>(.*?)<\/link>/";
			preg_match_all($link_regex, $item_match, $link_matches, PREG_PATTERN_ORDER);
			$link = str_replace('<link>', "", $link_matches[0][0]);
			$link = str_replace('</link>', "", $link);

			//detail
			$detail_regex = "/<description>(.*?)<\/description>/";
			preg_match_all($detail_regex, $item_match, $detail_matches, PREG_PATTERN_ORDER);
			$detail = str_replace('<description>', "", $detail_matches[0][0]);
			$detail = str_replace('</description>', "", $detail);	
			$detail = str_replace('</description>', "", $detail);
			$detail = str_replace('<![CDATA[', "", $detail);			
			$detail = str_replace(']]>', "", $detail);			
			$detail = strip_tags($detail);			

			//location
			$lat_regex = "/<geo:lat>(.*?)<\/geo:lat>/";
			preg_match_all($lat_regex, $item_match, $lat_matches, PREG_PATTERN_ORDER);
			$lat = str_replace('<lat>', "", $lat_matches[0][0]);
			$lat = str_replace('</lat>', "", $lat);
			
			$lng_regex = "/<geo:lng>(.*?)<\/geo:lng>/";
			preg_match_all($lng_regex, $item_match, $lng_matches, PREG_PATTERN_ORDER);
			$lng = str_replace('<lng>', "", $lng_matches[0][0]);
			$lng = str_replace('</lng>', "", $lng);

			//add event
			addEvent(NETTWITCHER_API_KEY, 'events', $title, $lng, $lat, $detail, $link, $link);
						
		}
		
	}

?>