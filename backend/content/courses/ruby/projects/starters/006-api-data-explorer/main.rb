require "uri"
uri = URI("https://example.com/data")
puts "Host to configure: #{uri.host}"
# TODO: request through a bounded-timeout client and parse JSON.
