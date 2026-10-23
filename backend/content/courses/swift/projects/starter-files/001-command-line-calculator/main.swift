import Foundation

enum Operation { case add, subtract, multiply, divide }
enum CalculatorError: Error { case divisionByZero }

struct Calculator {
    func calculate(_ left: Double, _ operation: Operation, _ right: Double) throws -> Double {
        // TODO: implement each operation and keep division-by-zero explicit.
        switch operation {
        case .add: return left + right
        case .subtract: return left - right
        case .multiply: return left * right
        case .divide:
            guard right != 0 else { throw CalculatorError.divisionByZero }
            return left / right
        }
    }
}

print("Calculator core ready; add input parsing and a repeat-until-exit loop next.")
