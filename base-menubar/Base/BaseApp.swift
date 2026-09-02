import SwiftUI

@main
struct BaseApp: App {
    @StateObject private var viewModel = BaseViewModel()

    var body: some Scene {
        MenuBarExtra {
            MenuBarView(viewModel: viewModel)
        } label: {
            HStack(spacing: 2) {
                Image(systemName: viewModel.statusIcon)
                    .foregroundColor(viewModel.statusColor)
                Text(viewModel.menuBarLabel)
                    .font(.system(.caption, design: .rounded).monospacedDigit())
            }
        }
        .menuBarExtraStyle(.window)
    }
}
