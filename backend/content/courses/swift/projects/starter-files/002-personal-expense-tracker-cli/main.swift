import Foundation

struct Expense {
    let title: String
    let amount: Decimal
    let category: String
}

func total(for expenses: [Expense], category: String? = nil) -> Decimal {
    // TODO: filter by the optional category and sum the matching expenses.
    return 0
}

let sample = [Expense(title: "Notebook", amount: 120, category: "Study")]
print("Expense tracker scaffold: \(sample.count) sample entry; implement total() and persistence.")
