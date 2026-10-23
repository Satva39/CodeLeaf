#include <cstdint>
#include <iostream>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

// Protocol exercise only: this file does not open sockets or provide encryption.
std::vector<std::uint8_t> encode_frame(std::string_view payload) {
    if (payload.size() > 65535) return {};
    const auto size = static_cast<std::uint16_t>(payload.size());
    std::vector<std::uint8_t> frame{
        static_cast<std::uint8_t>((size >> 8) & 0xff),
        static_cast<std::uint8_t>(size & 0xff)};
    for (unsigned char c : payload) frame.push_back(c);
    return frame;
}

int main() {
    const auto frame = encode_frame("hello");
    std::cout << "Encoded frame bytes: " << frame.size() << '\n';
    // TODO: Add a strict decoder and tests for truncated/oversized messages.
    // Keep platform socket code in a separate, reviewed adapter.
}
