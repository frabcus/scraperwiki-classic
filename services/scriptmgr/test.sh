#!/bin/bash
curl -H "Content-Length: 53"  -d "code=print 1-2&run_id=1&scrapername=test&scraper_id=2" http://127.0.0.1:8001/run
