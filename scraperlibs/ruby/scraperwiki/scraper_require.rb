Kernel.class_eval do 
  alias_method :__old_require, :require
  def require(path, *args)
    __old_require(path, *args)
  rescue LoadError
    if path.match /^scrapers?\// 
      Object.const_set(:Test, Module.new)
    else 
      raise
    end
  end
end

