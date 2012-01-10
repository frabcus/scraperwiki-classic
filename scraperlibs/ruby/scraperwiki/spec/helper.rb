$LOAD_PATH.unshift File.dirname(__FILE__) + '/..'
 
require 'rspec'
require 'scraperwiki'

RSpec.configure do |c|
	#c.mock_framework = :mocha
end

