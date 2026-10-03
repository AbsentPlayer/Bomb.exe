from PIL import Image, ImageDraw


def make_icon(size=512):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    s = size

    # bomb body (dark sphere)
    cx, cy, r = s * 0.5, s * 0.55, s * 0.30
    # main sphere (dark)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(30, 30, 40, 255))
    # darker bottom shading
    d.ellipse([cx - r, cy, cx + r, cy + r], fill=(18, 18, 26, 255))
    # top-left light shading
    d.ellipse([cx - r + int(r * 0.35), cy - r, cx + int(r * 0.45), cy - int(r * 0.2)],
              fill=(70, 72, 92, 255))
    # specular highlight (bright)
    d.ellipse([cx - int(r * 0.42), cy - int(r * 0.62), cx - int(r * 0.25), cy - int(r * 0.28)],
              fill=(200, 205, 225, 255))
    d.ellipse([cx - int(r * 0.42), cy - int(r * 0.62), cx - int(r * 0.25), cy - int(r * 0.28)],
              fill=(255, 255, 255, 235))

    # fuse: curve from top of bomb going up-right
    def fusa(x, y, r2):
        d.ellipse([x - r2, y - r2, x + r2, y + r2], fill=(80, 70, 60, 255))
    # fuse points
    fx0, fy0 = cx + int(r * 0.42), cy - int(r * 0.75)
    fx1, fy1 = cx + int(r * 0.72), cy - int(r * 1.02)
    fx2, fy2 = cx + int(r * 0.98), cy - int(r * 1.18)
    fw = int(s * 0.045)
    d.line([fx0, fy0, fx1, fy1], fill=(70, 60, 50, 255), width=fw)
    d.line([fx1, fy1, fx2, fy2], fill=(70, 60, 50, 255), width=fw)
    d.ellipse([fx0 - fw, fy0 - fw, fx0 + fw, fy0 + fw], fill=(70, 60, 50, 255))
    d.ellipse([fx1 - fw, fy1 - fw, fx1 + fw, fy1 + fw], fill=(70, 60, 50, 255))
    d.ellipse([fx2 - fw, fy2 - fw, fx2 + fw, fy2 + fw], fill=(70, 60, 50, 255))
    # fuse highlights (dots)
    for f in [((fx0 + fx1) / 2, (fy0 + fy1) / 2), ((fx1 + fx2) / 2, (fy1 + fy2) / 2)]:
        d.ellipse([f[0] - s * 0.02, f[1] - s * 0.02, f[0] + s * 0.02, f[1] + s * 0.02],
                  fill=(140, 130, 120, 255))

    # flame at the fuse end (burning)
    def flame(x, y, scale):
        # outer flame (orange)
        d.polygon([(x, y - s * 0.11 * scale),
                   (x - s * 0.05 * scale, y - s * 0.02 * scale),
                   (x - s * 0.06 * scale, y),
                   (x - s * 0.02 * scale, y + s * 0.04 * scale),
                   (x, y + s * 0.10 * scale),
                   (x + s * 0.02 * scale, y + s * 0.04 * scale),
                   (x + s * 0.06 * scale, y),
                   (x + s * 0.05 * scale, y - s * 0.02 * scale)],
                  fill=(255, 110, 40, 255))
        # inner flame (yellow)
        d.polygon([(x, y - s * 0.08 * scale),
                   (x - s * 0.03 * scale, y),
                   (x, y + s * 0.08 * scale),
                   (x + s * 0.03 * scale, y)],
                  fill=(255, 220, 70, 255))
        # core (white-yellow)
        d.ellipse([x - s * 0.012 * scale, y - s * 0.04 * scale,
                   x + s * 0.012 * scale, y + s * 0.04 * scale],
                  fill=(255, 245, 140, 255))

    flame(fx2, fy2, 1.0)
    # small secondary flicker
    flame(fx2 - s * 0.04, fy2 - s * 0.03, 0.45)

    return img


def main():
    import os

    img = make_icon(512)
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (24, 24), (16, 16)]
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bomb.ico')
    img.save(out, format='ICO', sizes=sizes)
    print('ICO saved:', out)


if __name__ == '__main__':
    main()
