require "optparse"
options = {dry_run: false}
OptionParser.new { |parser| parser.on("--dry-run") { options[:dry_run] = true } }.parse!(ARGV)
puts options[:dry_run] ? "Preview only" : "No operation selected"
