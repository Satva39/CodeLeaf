students = [{name: "Mina", marks: [82, 91, 77]}, {name: "Aarav", marks: [76, 88, 85]}]
students.each do |student|
  average = student[:marks].sum.to_f / student[:marks].length
  puts "#{student[:name]}: #{average.round(1)}"
end
