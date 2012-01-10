require File.dirname(__FILE__) + '/helper'

describe Kernel do 
  context "When we include scraper_require" do
    before do
      require File.dirname(__FILE__) + '/../scraper_require'
    end

    context "When we require a scraper" do
      it "loads the scraper as a module" do
        lambda { require 'scrapers/test' }.should_not raise_error
        Test.should_not be_nil
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

