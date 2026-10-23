#include <iostream>
#include <optional>
#include <utility>
#include <vector>

template <class T>
class Stack {
public:
    void push(T value) { values_.push_back(std::move(value)); }
    [[nodiscard]] bool empty() const noexcept { return values_.empty(); }
    [[nodiscard]] std::size_t size() const noexcept { return values_.size(); }
    std::optional<T> pop() {
        if (values_.empty()) return std::nullopt;
        T value = std::move(values_.back());
        values_.pop_back();
        return value;
    }
private:
    std::vector<T> values_;
};

int main() {
    Stack<int> stack;
    stack.push(10);
    if (auto value = stack.pop()) std::cout << *value << '\n';
    // TODO: Document exception guarantees and add tests for empty and move-only types.
}
