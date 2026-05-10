import AppKit
import CoreGraphics

final class GlowView: NSView {
    private let core = NSColor(calibratedRed: 0.50, green: 0.91, blue: 1.0, alpha: 1.0)
    private let neon = NSColor(calibratedRed: 0.00, green: 0.63, blue: 1.0, alpha: 1.0)
    private let deep = NSColor(calibratedRed: 0.00, green: 0.28, blue: 1.0, alpha: 1.0)

    override var isOpaque: Bool { false }

    private func cursorPath() -> CGMutablePath {
        // Hollow neon pointer based on the supplied reference image.
        // Coordinates are in a regular-cursor-sized 48x48 overlay window. The arrow tip is
        // also the mouse hot spot, so the visual pointer tracks the real target.
        let path = CGMutablePath()
        path.move(to: CGPoint(x: 12.5, y: 35.5))   // sharp upper-left tip / hot spot
        path.addLine(to: CGPoint(x: 16.0, y: 9.5))
        path.addLine(to: CGPoint(x: 22.0, y: 16.5))
        path.addLine(to: CGPoint(x: 31.0, y: 7.5))
        path.addLine(to: CGPoint(x: 35.0, y: 11.0))
        path.addLine(to: CGPoint(x: 26.0, y: 21.0))
        path.addLine(to: CGPoint(x: 35.5, y: 22.5))
        path.closeSubpath()
        return path
    }

    override func draw(_ dirtyRect: NSRect) {
        NSColor.clear.setFill()
        dirtyRect.fill()

        guard let ctx = NSGraphicsContext.current?.cgContext else { return }
        let path = cursorPath()

        ctx.saveGState()
        ctx.setBlendMode(.plusLighter)
        ctx.setLineJoin(.round)
        ctx.setLineCap(.round)

        // Soft blue halo, like a neon cursor tube blooming on a black background.
        for layer in 0..<4 {
            ctx.saveGState()
            let blur = CGFloat(9.5 - Double(layer) * 1.5)
            let alpha = CGFloat(0.22 + Double(layer) * 0.055)
            ctx.setShadow(offset: .zero, blur: blur, color: deep.withAlphaComponent(alpha).cgColor)
            ctx.setStrokeColor(deep.withAlphaComponent(alpha).cgColor)
            ctx.setLineWidth(CGFloat(5.2 - Double(layer) * 1.0))
            ctx.addPath(path)
            ctx.strokePath()
            ctx.restoreGState()
        }

        // Saturated middle neon stroke.
        ctx.saveGState()
        ctx.setShadow(offset: .zero, blur: 4.8, color: neon.withAlphaComponent(0.85).cgColor)
        ctx.setStrokeColor(neon.withAlphaComponent(0.86).cgColor)
        ctx.setLineWidth(2.6)
        ctx.addPath(path)
        ctx.strokePath()
        ctx.restoreGState()

        // Crisp cyan-white core line. No fill: the interior remains transparent.
        ctx.saveGState()
        ctx.setShadow(offset: .zero, blur: 2.0, color: core.withAlphaComponent(0.9).cgColor)
        ctx.setStrokeColor(core.cgColor)
        ctx.setLineWidth(1.15)
        ctx.addPath(path)
        ctx.strokePath()
        ctx.restoreGState()

        ctx.restoreGState()
    }
}

final class AppDelegate: NSObject, NSApplicationDelegate {
    var window: NSWindow!
    var timer: Timer!
    let size = NSSize(width: 48, height: 48)
    let hotSpot = NSPoint(x: 12.5, y: 35.5)
    var hideSystemCursor = CommandLine.arguments.contains("--hide-system")

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.accessory)

        let mouse = NSEvent.mouseLocation
        window = NSWindow(
            contentRect: NSRect(x: mouse.x - hotSpot.x, y: mouse.y - hotSpot.y, width: size.width, height: size.height),
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
        window.setFrameOrigin(NSPoint(x: mouse.x - hotSpot.x, y: mouse.y - hotSpot.y))
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
