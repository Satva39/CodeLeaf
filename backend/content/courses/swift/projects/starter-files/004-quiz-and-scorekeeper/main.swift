struct Question {
    let prompt: String
    let answer: String
}

func score(questions: [Question], answers: [String]) -> Int {
    // TODO: validate answer count and compare normalized answers.
    return 0
}

let questions = [Question(prompt: "2 + 2?", answer: "4")]
print("Quiz scaffold: \(questions.count) question")
