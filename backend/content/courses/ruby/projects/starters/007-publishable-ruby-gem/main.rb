module CodeLeafText
  def self.slug(value)
    value.downcase.strip.gsub(/[^a-z0-9]+/, "-").gsub(/\A-| -\z/, "")
  end
end
puts CodeLeafText.slug("Hello Ruby")
