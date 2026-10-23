// Create a package with `swift package init --type library` first.
// Move public APIs into Sources/<PackageName>/ and tests into Tests/.

public enum SwiftUtilities {
    public static func clamp<T: Comparable>(_ value: T, lower: T, upper: T) -> T {
        // TODO: define behavior when lower > upper, then clamp the value.
        return value
    }
}

print("Utilities scaffold ready; add DocC and package tests.")
