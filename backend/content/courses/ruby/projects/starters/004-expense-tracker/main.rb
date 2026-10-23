require "csv"
rows = CSV.parse("date,category,amount\n2026-10-01,books,250\n2026-10-02,travel,90\n", headers: true)
puts rows.sum { |row| Float(row["amount"]) }
