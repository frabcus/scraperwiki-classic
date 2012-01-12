require File.dirname(__FILE__) + '/helper'

WebMock.allow_net_connect!

describe Kernel do 
  context "When we include scraper_require" do
    before do
      require File.dirname(__FILE__) + '/../scraper_require'
    end

    context "When we require a scraper" do
      before do
        @scraper_name = 'require_test'
        require "scrapers/#{@scraper_name}"
      end

      it "fetches the scraper's code from ScraperWiki" do
        a_request(:get, "https://scraperwiki.com/editor/raw/#{@scraper_name}").should have_been_made
      end

      it "loads the scraper as a module" do
        RequireTest.should_not be_nil
      end
    end

    context "When we require something that is not a scraper" do
      it "loads the module if it exists" do
        require 'time'
      end

      it "raises a LoadError if it does not exist" do
        lambda { require 'bobalobablob' }.should raise_error LoadError
      end
    end
  end
end

