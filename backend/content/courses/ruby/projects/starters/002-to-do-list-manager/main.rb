tasks = []
tasks << {title: "Review Ruby", complete: false}
tasks.each { |task| puts "[#{task[:complete] ? "x" : " "}] #{task[:title]}" }
# TODO: implement menu commands and persistence.
