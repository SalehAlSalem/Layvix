from PIL import Image, ImageDraw

def create_layvix_icon(size, state="active"):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    scale = size / 28.0
    
    bg_color = (10, 10, 10, 255) # #0A0A0A
    border_color = (26, 32, 48, 255) # #1A2030
    line_width = max(1, int(1.5 * scale))
    
    x0, y0 = 1 * scale, 1 * scale
    x1, y1 = 27 * scale, 27 * scale
    r = 6 * scale
    draw.rounded_rectangle([x0, y0, x1, y1], radius=r, fill=bg_color, outline=border_color, width=max(1, int(0.5 * scale)))
    
    if state == "active":
        wave_color = (0, 201, 143, 255)
    elif state == "error":
        wave_color = (231, 76, 60, 255)
    else:
        wave_color = (74, 74, 90, 255)

    points = [(7, 14), (12, 14), (14, 9), (16, 19), (18, 14), (21, 14)]
    scaled_points = [(p[0] * scale, p[1] * scale) for p in points]
    draw.line(scaled_points, fill=wave_color, width=line_width, joint="curve")
    
    if state in ["active", "error"]:
        cx, cy = 22 * scale, 6 * scale
        cr = 2.5 * scale
        draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=wave_color)
    
    return img

if __name__ == "__main__":
    import os
    os.makedirs("data", exist_ok=True)
    
    # Create 256x256 base for the main icon
    icon_256 = create_layvix_icon(256, "active")
    icon_256.save("data/icon.png")
    icon_256.save("data/icon.ico", format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
    
    # Create 64x64 for tray icons
    for st in ["active", "paused", "error"]:
        img = create_layvix_icon(64, st)
        img.save(f"data/tray_icon_64_{st}.png")
    
    print("Icons generated successfully in data/")
