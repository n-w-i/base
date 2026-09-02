import SwiftUI
import Combine

struct WhoopToday: Codable {
    let cycle: CycleData?
    let recovery: RecoveryData?
    let sleep: SleepData?
    let workouts: [WorkoutData]?
}

struct CycleData: Codable {
    let score: CycleScore?
}

struct CycleScore: Codable {
    let strain: Double?
    let kilojoule: Double?
    let average_heart_rate: Int?
    let max_heart_rate: Int?
}

struct RecoveryData: Codable {
    let score: RecoveryScore?
}

struct RecoveryScore: Codable {
    let recovery_score: Double?
    let resting_heart_rate: Double?
    let hrv_rmssd_milli: Double?
    let spo2_percentage: Double?
    let skin_temp_celsius: Double?
}

struct SleepData: Codable {
    let score: SleepScore?
}

struct SleepScore: Codable {
    let stage_summary: StageSummary?
    let sleep_needed: SleepNeeded?
    let sleep_performance_percentage: Double?
    let sleep_efficiency_percentage: Double?
    let respiratory_rate: Double?
}

struct StageSummary: Codable {
    let total_in_bed_time_milli: Int?
    let total_slow_wave_sleep_time_milli: Int?
    let total_rem_sleep_time_milli: Int?
    let total_light_sleep_time_milli: Int?
    let total_awake_time_milli: Int?
    let disturbance_count: Int?
    let sleep_cycle_count: Int?
}

struct SleepNeeded: Codable {
    let baseline_milli: Int?
    let need_from_sleep_debt_milli: Int?
    let need_from_recent_strain_milli: Int?
    let need_from_recent_nap_milli: Int?
}

struct WorkoutData: Codable {
    let sport_name: String?
    let score: WorkoutScore?
}

struct WorkoutScore: Codable {
    let strain: Double?
    let average_heart_rate: Int?
}

struct ForecastResult: Codable {
    let current: CurrentState?
    let predictions: [Prediction]?
    let calendar_connected: Bool?
}

struct CurrentState: Codable {
    let recovery: Double?
    let hrv: Double?
    let avg_recovery_14d: Double?
    let trend: String?
}

struct Prediction: Codable {
    let day: String?
    let date: String?
    let predicted_recovery: Double?
    let zone: String?
    let events_affecting: [EventImpact]?
}

struct EventImpact: Codable {
    let title: String?
    let category: String?
    let impact: Double?
}

@MainActor
class BaseViewModel: ObservableObject {
    @Published var today: WhoopToday?
    @Published var forecast: ForecastResult?
    @Published var lastUpdated: Date?
    @Published var error: String?

    private var timer: Timer?
    private let whoopCoreURL = "http://localhost:9120"
    private let forecastURL = "http://localhost:9122"

    var recoveryScore: Double? { today?.recovery?.score?.recovery_score }
    var zone: String {
        guard let s = recoveryScore else { return "unknown" }
        if s >= 67 { return "green" }
        if s >= 34 { return "yellow" }
        return "red"
    }

    var statusIcon: String {
        switch zone {
        case "green": return "heart.fill"
        case "yellow": return "heart.fill"
        case "red": return "heart.fill"
        default: return "heart"
        }
    }

    var statusColor: Color {
        switch zone {
        case "green": return .green
        case "yellow": return .yellow
        case "red": return .red
        default: return .gray
        }
    }

    var menuBarLabel: String {
        if let score = recoveryScore {
            return "\(Int(score))%"
        }
        return "--"
    }

    init() {
        refresh()
        timer = Timer.scheduledTimer(withTimeInterval: 300, repeats: true) { [weak self] _ in
            Task { await self?.refresh() }
        }
    }

    func refresh() {
        Task {
            await fetchToday()
            await fetchForecast()
            lastUpdated = Date()
        }
    }

    private func fetchToday() async {
        guard let url = URL(string: "\(whoopCoreURL)/today") else { return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            today = try JSONDecoder().decode(WhoopToday.self, from: data)
            error = nil
        } catch {
            self.error = "whoop-core not reachable"
        }
    }

    private func fetchForecast() async {
        guard let url = URL(string: "\(forecastURL)/predict?days=3") else { return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            forecast = try JSONDecoder().decode(ForecastResult.self, from: data)
        } catch {
            // forecast is optional
        }
    }

    func msToTimeString(_ ms: Int?) -> String {
        guard let ms = ms else { return "--" }
        let hours = ms / 3_600_000
        let minutes = (ms % 3_600_000) / 60_000
        return "\(hours)h \(minutes)m"
    }
}
