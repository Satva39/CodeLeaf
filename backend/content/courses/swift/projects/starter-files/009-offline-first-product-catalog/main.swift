import Foundation

struct Product: Codable, Identifiable {
    let id: Int
    let name: String
    let price: Decimal
}

struct ProductCatalog {
    private(set) var products: [Product] = []
    mutating func replace(with products: [Product]) { self.products = products }
    func search(_ query: String) -> [Product] {
        // TODO: case-insensitive search; preserve the local data if refresh fails.
        return []
    }
}

print("Catalog scaffold ready; add decoding, caching, refresh and cancellation.")
