#include <iostream>
#include <string>
#include <vector>

struct Student {
    std::string name;
    std::vector<double> marks;
};

double average(const Student& student) {
    if (student.marks.empty()) return 0.0;
    double total = 0.0;
    for (double mark : student.marks) total += mark;
    return total / static_cast<double>(student.marks.size());
}

char grade_for(double percent) {
    // TODO: Define and document the grade boundaries with tests.
    if (percent >= 90.0) return 'A';
    if (percent >= 75.0) return 'B';
    if (percent >= 60.0) return 'C';
    if (percent >= 40.0) return 'D';
    return 'F';
}

int main() {
    const Student sample{"Sample learner", {82.0, 91.0, 76.0}};
    std::cout << sample.name << " average: " << average(sample)
              << " grade: " << grade_for(average(sample)) << '\n';
    // TODO: Read multiple students and validate each mark's range.
}
