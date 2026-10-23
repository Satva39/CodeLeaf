#include <iostream>
#include <string>
#include <vector>

enum class TaskState { open, complete };

struct Task {
    int id{};
    std::string title;
    int priority{3}; // 1 is highest; define and validate allowed values.
    TaskState state{TaskState::open};
};

bool complete_task(Task& task) {
    if (task.state == TaskState::complete) return false;
    task.state = TaskState::complete;
    return true;
}

int main() {
    std::vector<Task> tasks{{1, "Write tests", 1, TaskState::open}};
    complete_task(tasks.front());
    std::cout << "Task count: " << tasks.size() << '\n';
    // TODO: Add commands for add/edit/delete/search and persistent storage.
}
