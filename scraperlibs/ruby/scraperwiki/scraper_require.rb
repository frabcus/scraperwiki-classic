require 'net/http'

Kernel.class_eval do 
  alias_method :__old_require, :require

  def require(path, *args)
    __old_require(path, *args)
  rescue LoadError
    if matches = path.match( /^scrapers?\/(?<name>.+)/ )
      name = matches[:name]
      code = fetch_code name
      eigenated = "class << self; #{code}; end"
      klass = Class.new
      begin
        klass.module_eval eigenated
      rescue SyntaxError
        raise LoadError
      end

      Object.const_set scrapername_to_class_name(name), klass
    else 
      raise
    end
  end
end

def fetch_code(scraper_name)
  uri = URI("https://scraperwiki.com/editor/raw/#{scraper_name}")
  Net::HTTP.start uri.host, uri.port, use_ssl: true do |http|
    resp = http.get(uri.request_uri)
    return resp.body
  end
end

def scrapername_to_class_name(name)
  raise "no name supplied" if name.nil?

  name[0] = name[0].capitalize
  name.enum_for(:scan, /_|-/).each do 
    i = Regexp.last_match.begin(0)+1
    name[i] = name[i].capitalize 
  end
  name.gsub! /_|-/, ''
end
