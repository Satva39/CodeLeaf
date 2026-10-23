def calculate(left, operator, right)
  case operator
  when "+" then left + right
  when "-" then left - right
  when "*" then left * right
  when "/" then raise ZeroDivisionError if right.zero?; left.to_f / right
  else raise ArgumentError, "unsupported operator"
  end
end

puts calculate(12, "+", 3)
