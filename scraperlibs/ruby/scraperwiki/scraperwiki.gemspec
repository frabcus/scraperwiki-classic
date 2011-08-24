# -*- encoding: utf-8 -*-
$:.push File.expand_path("../lib", __FILE__)
require "scraperwiki/version"

Gem::Specification.new do |s|
  s.name        = "scraperwiki"
  s.version     = ScraperWiki::VERSION
  s.platform    = Gem::Platform::RUBY
  s.authors     = ["Francis Irving"]
  s.email       = ["francis@scraperwiki.com"]
  s.homepage    = "http://scraperwiki.com"
  s.summary     = %q{ScraperWiki client library for Ruby}
  s.description = %q{Ruby code used for accessing}

  s.files         = `hg locate -f -I .`.split("\n")
  s.require_paths = ["lib"]
end