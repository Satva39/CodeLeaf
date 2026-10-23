#include <iostream>
#include <string>
#include <vector>

struct Book {
    int id{};
    std::string title;
    bool available{true};
};

bool borrow(Book& book) {
    if (!book.available) return false;
    book.available = false;
    return true;
}

bool return_book(Book& book) {
    if (book.available) return false;
    book.available = true;
    return true;
}

int main() {
    Book book{101, "A C++ Introduction", true};
    std::cout << "Borrow accepted: " << std::boolalpha << borrow(book) << '\n';
    std::cout << "Available after borrow: " << book.available << '\n';
    // TODO: Add members, catalog search, lending history, and saved records.
}
