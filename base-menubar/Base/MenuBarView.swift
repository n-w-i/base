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
    func forecastSection(_ predictions: [Prediction]) -> some View {
        Divider()
        VStack(alignment: .leading, spacing: 4) {
            Text("Forecast")
                .font(.subheadline.bold())
            ForEach(Array(predictions.enumerated()), id: \.offset) { _, p in
                HStack {
                    Circle()
                        .fill(zoneColor(p.zone ?? "unknown"))
                        .frame(width: 8, height: 8)
                    Text(p.day ?? "")
                        .font(.caption)
                    Spacer()
                    Text("\(Int(p.predicted_recovery ?? 0))%")
                        .font(.caption.bold())
                        .foregroundColor(zoneColor(p.zone ?? "unknown"))

                    if let strain = p.predicted_strain {
                        Text(String(format: "· %.1f strain", strain))
                            .font(.caption2)
                            .foregroundColor(.secondary)
                    }

                    if let events = p.events_affecting, !events.isEmpty {
                        Text("·")
                            .foregroundColor(.secondary)
                        Text(events.map { $0.title ?? "" }.joined(separator: ", "))
                            .font(.caption2)
                            .foregroundColor(.secondary)
                            .lineLimit(1)
                    }
                }
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
