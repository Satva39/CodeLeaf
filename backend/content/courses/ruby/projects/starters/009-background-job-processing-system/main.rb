require "thread"
queue = Queue.new
queue << {id: "job-001", state: :queued}
job = queue.pop
puts "#{job[:id]}: #{job[:state]}"
# TODO: retries, idempotency, failure states, and graceful shutdown.
