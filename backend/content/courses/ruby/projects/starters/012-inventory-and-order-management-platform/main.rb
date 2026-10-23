module Inventory
  Product = Data.define(:sku, :name, :quantity)
  Order = Data.define(:id, :state, :items)
end
puts Inventory::Product.new("PEN-01", "Pen", 12)
# TODO: add persistence, transactions, API/CLI, tests, and release operations.
