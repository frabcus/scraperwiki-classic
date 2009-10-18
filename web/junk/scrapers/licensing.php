<?php

	require_once(dirname(__FILE__) . "/php_includes/config.php");
	require_once(dirname(__FILE__) . "/php_includes/functions.php");

	scrape_lambeth();

	//lambeth
	function scrape_lambeth(){
		
		$url = "http://www.lambeth.gov.uk/Services/Business/LicencesStreetTrading/PendingApplications.htm";
		$html = file_get_contents($url);		
		$html = remove_line_breaks($html);
		$container_regex = "/<h2 class=\"infoBox\">.*?<\/div>/";

		preg_match_all($container_regex, $html, $container_matches, PREG_PATTERN_ORDER);
		
		if(sizeof($container_matches[0]) != 1){
			error_log("error finding licensing container");
		}

		//get items
		$item_regex = "/<li>(.*?)<\/li>/";
		preg_match_all($item_regex, $container_matches[0][0], $item_matches);

		if(sizeof($item_matches) == 0){
			error_log("No licensing items found for lambeth");
		}

		foreach($item_matches[1] as $item_match){

			//link
			$link_regex = "/href=\"(.*?)\"/";
			preg_match_all($link_regex, $item_match, $link_matches);
			$link = "http://www.lambeth.gov.uk/" . $link_matches[0][0];

			//postcode
			

			//description
			$detail_regex = "/<br\/>/";
			preg_match_all($detail_regex, $item_match, $detail_matches);
			$detail = trim($detail_matches[0][1]);
			print $detail;
			
			
		}
		
	}

?>