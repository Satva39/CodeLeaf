#include <iomanip>
#include <iostream>
#include <string>
#include <vector>

struct Expense {
    std::string description;
    std::string category;
    long long amount_paise{}; // Integer paise avoids binary floating-point money rounding.
};

long long total_of(const std::vector<Expense>& expenses) {
    long long total = 0;
    for (const auto& expense : expenses) total += expense.amount_paise;
    return total;
}

int main() {
    const std::vector<Expense> sample{{"Notebook", "Study", 12500},
                                      {"Bus pass", "Travel", 40000}};
    std::cout << "Expenses: " << sample.size() << '\n';
    std::cout << "Total: Rs " << std::fixed << std::setprecision(2)
              << static_cast<double>(total_of(sample)) / 100.0 << '\n';
    // TODO: Add validation, category summaries, and safe file persistence.
}
