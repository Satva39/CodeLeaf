import Foundation

func transform(_ value: Int) async -> Int { value * value }

func run() async {
    // TODO: use a task group, enforce a concurrency limit and preserve errors/cancellation.
    let sample = await transform(4)
    print("Single result: \(sample)")
}

await run()
