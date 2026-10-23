#include <iostream>
#include <numeric>
#include <optional>

bool is_prime(int value) {
    if (value < 2) return false;
    for (int divisor = 2; divisor <= value / divisor; ++divisor) {
        if (value % divisor == 0) return false;
    }
    return true;
}

std::optional<unsigned long long> factorial(unsigned int n) {
    unsigned long long result = 1;
    for (unsigned int value = 2; value <= n; ++value) {
        if (result > (~0ULL) / value) return std::nullopt;
        result *= value;
    }
    return result;
}

int main() {
    std::cout << "Prime check for 29: " << std::boolalpha << is_prime(29) << '\n';
    if (const auto result = factorial(5)) std::cout << "5! = " << *result << '\n';
    // TODO: Add GCD/LCM, digit operations, menu commands, and input checks.
}
