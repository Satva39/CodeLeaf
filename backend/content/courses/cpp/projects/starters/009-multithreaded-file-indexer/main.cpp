#include <atomic>
#include <filesystem>
#include <iostream>
#include <thread>
#include <vector>

namespace fs = std::filesystem;

int main(int argc, char* argv[]) {
    const fs::path root = argc > 1 ? argv[1] : ".";
    std::atomic<std::size_t> visited{0};
    // Baseline traversal first. Add bounded workers only after correctness tests.
    try {
        for (const auto& entry : fs::recursive_directory_iterator(root)) {
            if (entry.is_regular_file()) ++visited;
        }
        std::cout << "Files discovered: " << visited.load() << '\n';
    } catch (const fs::filesystem_error& error) {
        std::cerr << "Traversal error: " << error.what() << '\n';
        return 1;
    }
    // TODO: Add filtering, a bounded work queue, cancellation, and synchronized results.
}
