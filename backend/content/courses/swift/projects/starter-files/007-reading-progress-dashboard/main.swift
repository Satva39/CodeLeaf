struct ReadingBook {
    let title: String
    let pageCount: Int
    var pagesRead: Int
    var progressPercent: Double {
        // TODO: handle zero/invalid page counts and clamp impossible progress.
        return 0
    }
}

let sample = ReadingBook(title: "Swift Guide", pageCount: 200, pagesRead: 40)
print("Reading dashboard scaffold: \(sample.title)")
