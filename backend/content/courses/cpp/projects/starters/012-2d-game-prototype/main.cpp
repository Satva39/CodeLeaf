#include <iostream>

struct Vec2 { float x{}; float y{}; };
struct Player { Vec2 position{}; Vec2 velocity{}; };

void update(Player& player, float delta_seconds) {
    // Keep this model update deterministic; render/input are separate adapters.
    player.position.x += player.velocity.x * delta_seconds;
    player.position.y += player.velocity.y * delta_seconds;
}

int main() {
    Player player{{0.0F, 0.0F}, {3.0F, 1.5F}};
    update(player, 0.5F);
    std::cout << "Player position: (" << player.position.x << ", "
              << player.position.y << ")\n";
    // TODO: Add input, collision rules, game state, and a chosen graphics backend.
}
