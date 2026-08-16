import Foundation
import Vision
import AppKit

let args = CommandLine.arguments
guard args.count > 1 else {
    print("usage: ocr <image>...")
    exit(1)
}

for path in args.dropFirst() {
    guard let image = NSImage(contentsOfFile: path),
          let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
        print("===== \(path) =====\nERROR: cannot load image")
        continue
    }

    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.recognitionLanguages = ["zh-Hans", "en-US"]
    request.usesLanguageCorrection = true

    let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
    do {
        try handler.perform([request])
    } catch {
        print("===== \(path) =====\nERROR: \(error)")
        continue
    }

    print("===== \(path) =====")
    if let observations = request.results {
        let lines = observations
            .sorted { $0.boundingBox.midY > $1.boundingBox.midY }
            .compactMap { obs -> String? in
                guard let candidate = obs.topCandidates(1).first else { return nil }
                let bb = obs.boundingBox
                return String(
                    format: "%.3f\t%.3f\t%.3f\t%.3f\t%@",
                    bb.origin.x, bb.origin.y, bb.size.width, bb.size.height,
                    candidate.string
                )
            }
        print(lines.joined(separator: "\n"))
    }
}
