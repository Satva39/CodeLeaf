class Book
  attr_reader :id, :title
  def initialize(id, title)
    @id, @title = id, title
  end
end

books = [Book.new(1, "Ruby Basics")]
puts books.first.title
