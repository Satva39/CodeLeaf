import Foundation

struct StudyLesson: Identifiable {
    let id: String
    let title: String
    var isComplete: Bool
}
struct StudyCourse: Identifiable {
    let id: String
    let title: String
    var lessons: [StudyLesson]
    var completedCount: Int { lessons.filter(\.isComplete).count }
}

let sample = StudyCourse(id: "swift", title: "Swift", lessons: [StudyLesson(id: "one", title: "First program", isComplete: false)])
print("\(sample.title): \(sample.completedCount)/\(sample.lessons.count) lessons complete")
// TODO: add persistence, validation, observable app state, navigation and optional API integration.
