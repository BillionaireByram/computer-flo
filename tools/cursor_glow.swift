import AppKit
import CoreGraphics

final class GlowView: NSView {
    var color = NSColor(calibratedRed: 0.0, green: 0.72, blue: 1.0, alpha: 1.0)

    override var isOpaque: Bool { false }

    override func draw(_ dirtyRect: NSRect) {
        NSColor.clear.setFill()
        dirtyRect.fill()

        guard let ctx = NSGraphicsContext.current?.cgContext else { return }
        let center = CGPoint(x: bounds.midX, y: bounds.midY)

        ctx.saveGState()
        ctx.setBlendMode(.plusLighter)

        // Outer electric glow rings.
        for i in 0..<5 {
            let radius = CGFloat(10.0 + Double(i) * 4.5)
            let alpha = CGFloat(0.22 - Double(i) * 0.035)
            ctx.setStrokeColor(color.withAlphaComponent(alpha).cgColor)
            ctx.setLineWidth(CGFloat(3.5 - Double(i) * 0.35))
            ctx.strokeEllipse(in: CGRect(x: center.x - radius, y: center.y - radius, width: radius * 2, height: radius * 2))
        }

        // Futuristic triangular cursor / pointer.
        let path = CGMutablePath()
        path.move(to: CGPoint(x: center.x - 1.5, y: center.y + 15.5))
        path.addLine(to: CGPoint(x: center.x + 11.5, y: center.y - 12.5))
        path.addLine(to: CGPoint(x: center.x + 1.5, y: center.y - 8.0))
        path.addLine(to: CGPoint(x: center.x - 5.5, y: center.y - 18.0))
        path.closeSubpath()

        ctx.setShadow(offset: .zero, blur: 9, color: color.withAlphaComponent(0.95).cgColor)
        ctx.setFillColor(NSColor(calibratedRed: 0.02, green: 0.08, blue: 0.16, alpha: 0.88).cgColor)
        ctx.addPath(path)
        ctx.fillPath()

        ctx.setShadow(offset: .zero, blur: 5, color: color.withAlphaComponent(1.0).cgColor)
        ctx.setStrokeColor(color.cgColor)
        ctx.setLineWidth(1.4)
        ctx.addPath(path)
        ctx.strokePath()

        // Core dot and crosshair ticks.
        ctx.setShadow(offset: .zero, blur: 6, color: color.cgColor)
        ctx.setFillColor(NSColor.white.withAlphaComponent(0.92).cgColor)
        ctx.fillEllipse(in: CGRect(x: center.x - 1.5, y: center.y - 1.5, width: 3, height: 3))

        ctx.setStrokeColor(color.withAlphaComponent(0.75).cgColor)
        ctx.setLineWidth(1.5)
        let tick: CGFloat = 6.5
        let gap: CGFloat = 3.5
        ctx.move(to: CGPoint(x: center.x - tick, y: center.y))
        ctx.addLine(to: CGPoint(x: center.x - gap, y: center.y))
        ctx.move(to: CGPoint(x: center.x + gap, y: center.y))
        ctx.addLine(to: CGPoint(x: center.x + tick, y: center.y))
        ctx.move(to: CGPoint(x: center.x, y: center.y - tick))
        ctx.addLine(to: CGPoint(x: center.x, y: center.y - gap))
        ctx.move(to: CGPoint(x: center.x, y: center.y + gap))
        ctx.addLine(to: CGPoint(x: center.x, y: center.y + tick))
        ctx.strokePath()

        ctx.restoreGState()
    }
}

final class AppDelegate: NSObject, NSApplicationDelegate {
    var window: NSWindow!
    var timer: Timer!
    let size = NSSize(width: 75, height: 75)
    var hideSystemCursor = CommandLine.arguments.contains("--hide-system")

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.accessory)

        let mouse = NSEvent.mouseLocation
        window = NSWindow(
            contentRect: NSRect(x: mouse.x - size.width / 2, y: mouse.y - size.height / 2, width: size.width, height: size.height),
            styleMask: [.borderless],
            backing: .buffered,
            defer: false
        )
        window.isOpaque = false
        window.backgroundColor = .clear
        window.hasShadow = false
        window.ignoresMouseEvents = true
        window.level = .screenSaver
        window.collectionBehavior = [.canJoinAllSpaces, .stationary, .ignoresCycle]
        window.contentView = GlowView(frame: NSRect(origin: .zero, size: size))
        window.orderFrontRegardless()

        if hideSystemCursor { NSCursor.hide() }

        timer = Timer.scheduledTimer(withTimeInterval: 1.0 / 60.0, repeats: true) { [weak self] _ in
            self?.followMouse()
        }
        RunLoop.main.add(timer, forMode: .common)
    }

    func followMouse() {
        let mouse = NSEvent.mouseLocation
        window.setFrameOrigin(NSPoint(x: mouse.x - size.width / 2, y: mouse.y - size.height / 2))
        window.contentView?.needsDisplay = true
    }

    func applicationWillTerminate(_ notification: Notification) {
        if hideSystemCursor { NSCursor.unhide() }
    }
}

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.run()
