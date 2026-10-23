#include <iostream>
#include <sstream>
#include <string>
#include <vector>

std::vector<std::string> split_simple_csv_row(const std::string& row) {
    // Starter only: quoted commas and escaped quotes still need proper handling.
    std::vector<std::string> fields;
    std::stringstream input(row);
    std::string field;
    while (std::getline(input, field, ',')) fields.push_back(field);
    return fields;
}

int main() {
    const auto fields = split_simple_csv_row("Ahmedabad,42,active");
    std::cout << "Parsed fields: " << fields.size() << '\n';
    // TODO: Validate headers and rows, calculate summaries, and write a report.
}
