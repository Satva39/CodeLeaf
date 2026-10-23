#include <iostream>
#include <stdexcept>

// Starter: a small working core. Extend it into a validated, repeatable menu.
double calculate(double left, char operation, double right) {
    switch (operation) {
        case '+': return left + right;
        case '-': return left - right;
        case '*': return left * right;
        case '/':
            if (right == 0.0) throw std::invalid_argument("division by zero");
            return left / right;
        default: throw std::invalid_argument("unknown operation");
    }
}

int main() {
    double left{}, right{};
    char operation{};
    std::cout << "Enter: number operator number (example: 8 * 3): ";
    if (!(std::cin >> left >> operation >> right)) {
        std::cerr << "Invalid input.\n";
        return 1;
    }
    try {
        std::cout << "Result: " << calculate(left, operation, right) << '\n';
    } catch (const std::invalid_argument& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
