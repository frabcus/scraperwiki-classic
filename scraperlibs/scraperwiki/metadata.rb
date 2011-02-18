require 'uri'
require 'net/http'
require 'json'
require 'singleton'
require 'cgi'

class LocalMetadataClient
  include Singleton

  def initialize
    @metadata_local = { "title" => "Untitled Scraper", "CPU limit" => "100" }
  end
  
  def get(metadata_name, default = nil)
    value = @metadata_local[metadata_name]
    return value ? value : default
  end
  
  def save(metadata_name,value)
    puts 'The scraper has not been saved yet. Metadata will not be persisted between runs'
    @metadata_local[metadata_name] = value
    return nil
  end
end

class SW_MetadataClient
  include Singleton

  def self.create()
    if ENV["SCRAPER_GUID"]
      SW_MetadataClient.instance()
    else
      LocalMetadataClient.instance()
    end
  end

  def get_url(metadata_name)
    "http://%s/scrapers/metadata_api/%s/%s/" % [ENV["metadata_host"], ENV["SCRAPER_GUID"], CGI.escape(metadata_name)]
  end

  def get_metadata(metadata_name)
    uri = URI.parse(get_url(metadata_name))
    res = Net::HTTP.get_response(uri)
    case res
    when Net::HTTPSuccess
      return JSON.parse(res.body)
    else
      return nil
    end
  end
  
  def post_or_put(method, metadata_name, value, run_id)
    uri = URI.parse(get_url(metadata_name))
    req = (method == :post ? Net::HTTP::Post.new(uri.path) : Net::HTTP::Put.new(uri.path))
    req.set_form_data('run_id'=> run_id,'value'=>JSON.dump([value]))
    res = Net::HTTP.new(uri.host, uri.port).start {|http| http.request(req) }
    case res
    when Net::HTTPSuccess, Net::HTTPRedirection
      return nil
    else
      raise "ERROR SAVING METADATA #{res}"
    end
  end
  
  def get(metadata_name, default = nil)
    metadata = get_metadata(metadata_name)
    metadata ? JSON.parse(metadata['value'])[0] : default
  end
  
  def save(metadata_name, value)
    run_id = ENV['RUNID']
    method = get(metadata_name) ? :put : :post
    post_or_put(method, metadata_name, value,run_id)
  end
end
