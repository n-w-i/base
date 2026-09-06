import SwiftUI

struct MenuBarView: View {
    @ObservedObject var viewModel: BaseViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Header
            HStack {
                Text("Base")
                    .font(.headline)
                Spacer()
                if let last = viewModel.lastUpdated {
                    Text(last, style: .relative)
                        .font(.caption2)
                        .foregroundColor(.secondary)
                }
            }

            Divider()

            // Recovery
            if let recovery = viewModel.today?.recovery?.score {
                recoverySection(recovery)
            } else if let err = viewModel.error {
                Label(err, systemImage: "exclamationmark.triangle")
                    .foregroundColor(.orange)
                    .font(.caption)
            }

            // Sleep
            if let sleep = viewModel.today?.sleep?.score {
                sleepSection(sleep)
            }

            // Strain
            if let cycle = viewModel.today?.cycle?.score {
                strainSection(cycle)
            }

            // Workouts
            if let workouts = viewModel.today?.workouts, !workouts.isEmpty {
                workoutsSection(workouts)
            }

            // Strength (Hevy exercise breakdown, if a recent workout was logged)
            if let hevy = viewModel.hevyToday, let exercises = hevy.exercises, !exercises.isEmpty {
                strengthSection(hevy, exercises)
            }

            // Forecast
            if let predictions = viewModel.forecast?.predictions, !predictions.isEmpty {
                forecastSection(predictions)
            }

            Divider()

            HStack {
                Button("Refresh") { viewModel.refresh() }
                    .buttonStyle(.borderless)
                Spacer()
                Button("Quit") { NSApplication.shared.terminate(nil) }
                    .buttonStyle(.borderless)
                    .foregroundColor(.secondary)
            }
        }
        .padding()
        .frame(width: 300)
    }

    @ViewBuilder
    func recoverySection(_ score: RecoveryScore) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Circle()
                    .fill(viewModel.statusColor)
                    .frame(width: 10, height: 10)
                Text("Recovery")
                    .font(.subheadline.bold())
                Spacer()
                Text("\(Int(score.recovery_score ?? 0))%")
                    .font(.system(.title2, design: .rounded).bold())
                    .foregroundColor(viewModel.statusColor)
            }

            HStack(spacing: 16) {
                metricPill("HRV", value: String(format: "%.0f", score.hrv_rmssd_milli ?? 0), unit: "ms")
                metricPill("RHR", value: "\(Int(score.resting_heart_rate ?? 0))", unit: "bpm")
                if let spo2 = score.spo2_percentage {
                    metricPill("SpO2", value: String(format: "%.0f", spo2), unit: "%")
                }
            }
        }
    }

    @ViewBuilder
    func sleepSection(_ score: SleepScore) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Image(systemName: "moon.fill")
                    .foregroundColor(.indigo)
                Text("Sleep")
                    .font(.subheadline.bold())
                Spacer()
                Text("\(Int(score.sleep_performance_percentage ?? 0))%")
                    .font(.system(.body, design: .rounded).bold())
            }

            if let stages = score.stage_summary {
                HStack(spacing: 12) {
                    miniStat("In bed", viewModel.msToTimeString(stages.total_in_bed_time_milli))
                    miniStat("Deep", viewModel.msToTimeString(stages.total_slow_wave_sleep_time_milli))
                    miniStat("REM", viewModel.msToTimeString(stages.total_rem_sleep_time_milli))
                }
                .font(.caption)
            }
        }
    }

    @ViewBuilder
    func strainSection(_ score: CycleScore) -> some View {
        HStack {
            Image(systemName: "flame.fill")
                .foregroundColor(.orange)
            Text("Strain")
                .font(.subheadline.bold())
            Spacer()
            Text(String(format: "%.1f", score.strain ?? 0))
                .font(.system(.body, design: .rounded).bold())
            Text("/ 21")
                .font(.caption)
                .foregroundColor(.secondary)
        }
    }

    @ViewBuilder
    func workoutsSection(_ workouts: [WorkoutData]) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text("Workouts")
                .font(.subheadline.bold())
            ForEach(Array(workouts.enumerated()), id: \.offset) { _, w in
                HStack {
                    Text(w.sport_name?.capitalized ?? "Unknown")
                        .font(.caption)
                    Spacer()
                    if let strain = w.score?.strain {
                        Text(String(format: "%.1f strain", strain))
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
            }
        }
    }

    @ViewBuilder
    func strengthSection(_ workout: HevyWorkout, _ exercises: [HevyExercise]) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(workout.title ?? "Strength")
                .font(.subheadline.bold())
            ForEach(Array(exercises.enumerated()), id: \.offset) { _, exercise in
                HStack {
                    Text(exercise.title ?? "Exercise")
                        .font(.caption)
                    Spacer()
                    Text(workingSetSummary(exercise.sets ?? []))
                        .font(.caption2)
                        .foregroundColor(.secondary)
                }
            }
        }
    }

    func workingSetSummary(_ sets: [HevySet]) -> String {
        let working = sets.filter { $0.type != "warmup" }
        guard !working.isEmpty else { return "0 sets" }
        var summary = "\(working.count) sets"
        if let top = working.max(by: { ($0.weight_kg ?? 0) < ($1.weight_kg ?? 0) }) {
            var bits: [String] = []
            if let w = top.weight_kg { bits.append(String(format: "top %.0fkg", w)) }
            if let r = top.reps { bits.append("x\(Int(r))") }
            if let rpe = top.rpe { bits.append(String(format: "@RPE %.1f", rpe)) }
            if !bits.isEmpty { summary += ", " + bits.joined(separator: " ") }
        }
        return summary
    }

    @ViewBuilder
    func forecastSection(_ predictions: [Prediction]) -> some View {
        Divider()
        VStack(alignment: .leading, spacing: 8) {
            Text("Forecast")
                .font(.subheadline.bold())
            ForEach(Array(predictions.enumerated()), id: \.offset) { index, p in
                forecastDay(p)
                if index < predictions.count - 1 {
                    Divider()
                }
            }
        }
    }

    @ViewBuilder
    func forecastDay(_ p: Prediction) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            HStack {
                Circle()
                    .fill(zoneColor(p.zone ?? "unknown"))
                    .frame(width: 8, height: 8)
                Text(p.day ?? "")
                    .font(.caption.bold())
                Spacer()
                Text("\(Int(p.predicted_recovery ?? 0))%")
                    .font(.caption.bold())
                    .foregroundColor(zoneColor(p.zone ?? "unknown"))
                if let strain = p.predicted_strain {
                    Text(String(format: "%.1f strain", strain))
                        .font(.caption2)
                        .foregroundColor(.secondary)
                }
            }

            if let summary = p.summary {
                Text(summary)
                    .font(.caption)
                    .foregroundColor(.primary)
            }

            if let freshness = p.freshness {
                let state = freshness >= 0 ? "fresh" : "fatigued"
                Text(String(format: "Freshness %+.1f (%@) — fitness %.1f, fatigue %.1f", freshness, state, p.fitness ?? 0, p.fatigue ?? 0))
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }

            if let events = p.events_affecting, !events.isEmpty {
                ForEach(Array(events.enumerated()), id: \.offset) { _, e in
                    let sign = (e.impact ?? 0) >= 0 ? "+" : ""
                    Text("\(e.title ?? "") — \(sign)\(Int(e.impact ?? 0)) recovery")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                }
            } else if let delta = p.recovery_delta, delta != 0 {
                Text(String(format: "Calendar impact: %+.0f", delta))
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }

            if let sleepQuality = p.sleep_quality_estimate {
                Text(String(format: "Estimated sleep quality: %.0f%%", sleepQuality))
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }

            if let base = p.base_recovery, let delta = p.recovery_delta,
               let fresh = p.freshness_adjustment, let sleep = p.sleep_bonus,
               let result = p.predicted_recovery {
                Text(String(format: "Recovery: %.0f base %+.0f cal %+.1f fresh %+.1f sleep = %.0f%%", base, delta, fresh, sleep, result))
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }

            if let base = p.base_strain, let load = p.strain_load,
               let rev = p.strain_reversion, let result = p.predicted_strain {
                Text(String(format: "Strain: %.1f base %+.1f planned %+.1f revert = %.1f", base, load, rev, result))
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
        }
    }

    func metricPill(_ label: String, value: String, unit: String) -> some View {
        VStack(spacing: 1) {
            Text(label)
                .font(.caption2)
                .foregroundColor(.secondary)
            HStack(spacing: 1) {
                Text(value)
                    .font(.caption.bold())
                Text(unit)
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
        }
    }

    func miniStat(_ label: String, _ value: String) -> some View {
        VStack(alignment: .leading, spacing: 1) {
            Text(label)
                .foregroundColor(.secondary)
            Text(value)
                .bold()
        }
    }

    func zoneColor(_ zone: String) -> Color {
        switch zone {
        case "green": return .green
        case "yellow": return .yellow
        case "red": return .red
        default: return .gray
        }
    }
}
