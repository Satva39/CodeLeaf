#include <iostream>
#include <string>
#include <vector>

struct Product { int id{}; std::string name; long long price_paise{}; int stock{}; };
struct OrderLine { int product_id{}; int quantity{}; };
struct Order { int id{}; std::vector<OrderLine> lines; };

bool valid_quantity(const Product& product, int quantity) {
    return quantity > 0 && quantity <= product.stock;
}

int main() {
    const Product notebook{1, "Notebook", 12500, 20};
    const Order order{1001, {{notebook.id, 2}}};
    std::cout << "Order " << order.id << ": " << order.lines.size()
              << " line(s); quantity valid=" << std::boolalpha
              << valid_quantity(notebook, order.lines.front().quantity) << '\n';
    // TODO: Split domain/interfaces/storage, add transactions, logging, CMake, and tests.
}
