import Foundation

struct Note: Identifiable {
    let id: UUID
    var title: String
    var body: String
    var tags: Set<String>
}

func search(_ notes: [Note], query: String) -> [Note] {
    // TODO: search title/body/tags; keep data and presentation separate.
    return []
}

print("Knowledge manager scaffold ready; add persistence and import/export.")
