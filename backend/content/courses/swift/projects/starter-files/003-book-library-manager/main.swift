struct Book {
    let id: Int
    let title: String
    var borrower: String? = nil
    var isAvailable: Bool { borrower == nil }
}

struct Library {
    private(set) var books: [Book] = []
    mutating func add(_ book: Book) { books.append(book) }
    func search(_ query: String) -> [Book] {
        // TODO: implement a case-insensitive title search.
        return []
    }
}

var library = Library()
library.add(Book(id: 1, title: "Swift Basics"))
print("Library scaffold ready")
