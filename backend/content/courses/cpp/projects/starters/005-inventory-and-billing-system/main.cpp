#include <iostream>
#include <string>
#include <vector>

struct Product {
    int id{};
    std::string name;
    int stock{};
    long long unit_price_paise{};
};

bool sell(Product& product, int quantity) {
    if (quantity <= 0 || quantity > product.stock) return false;
    product.stock -= quantity;
    return true;
}

long long line_total(const Product& product, int quantity) {
    return product.unit_price_paise * quantity;
}

int main() {
    Product item{1, "Notebook", 20, 12500};
    if (sell(item, 2)) {
        std::cout << item.name << " remaining=" << item.stock
                  << " line-total-paise=" << line_total(item, 2) << '\n';
    }
    // TODO: Add searching, cart validation, bill summaries, and persistence.
}
