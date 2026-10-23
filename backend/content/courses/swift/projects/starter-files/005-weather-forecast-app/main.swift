import Foundation

struct WeatherSnapshot: Codable {
    let location: String
    let temperatureCelsius: Double
    let condition: String
}

enum LoadState<Value> {
    case idle, loading, loaded(Value), failed(String)
}

let sample = WeatherSnapshot(location: "Ahmedabad", temperatureCelsius: 31, condition: "Clear")
print("\(sample.location): \(sample.condition)")
// TODO: isolate URLSession/API mapping and model loading, empty, error, cache, and cancellation states.
