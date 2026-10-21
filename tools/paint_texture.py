"""Pinta la textura de la calavera directamente sobre la plantilla UV de la malla facial.

Cada adorno se coloca usando la posicion UV de landmarks reales de MediaPipe
(contorno de ojos, labios, nariz, frente, mejillas), asi que el dibujo cae justo
sobre la cara. Ojos y boca interior quedan transparentes (alpha = 0).

Uso:
    python tools/paint_texture.py
Salida (una textura por paleta, el gesto de cejas cambia entre ellas):
    assets/textures/calavera-clasica.png
    assets/textures/calavera-turquesa.png
    assets/textures/calavera-dorada.png
"""
import json
import math
import os

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MESH = os.path.join(ROOT, "assets", "mesh", "face_mesh.json")
OUT_DIR = os.path.join(ROOT, "assets", "textures")
SIZE = 1024
SS = 2  # supermuestreo para bordes suaves
S = SIZE * SS

# Landmarks de MediaPipe Face Mesh
LEFT_EYE = [263, 249, 390, 373, 374, 380, 381, 382, 362, 398, 384, 385, 386, 387, 388, 466]
RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
LEFT_BROW = [276, 283, 282, 295, 285, 300, 293, 334, 296, 336]
RIGHT_BROW = [46, 53, 52, 65, 55, 70, 63, 105, 66, 107]
LIPS_INNER = [78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308, 415, 310, 311, 312, 13, 82, 81, 80, 191]
FACE_OVAL = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377,
             152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]
FOREHEAD_TOP = [21, 54, 103, 67, 109, 10, 338, 297, 332, 284, 251]

PALETTES = {
    "clasica": dict(base="#fbf7ee", socket="#2b1640", p1="#ff8c00", p2="#ffc300",
                    a1="#e6007e", a2="#00a6a6", a3="#7b2cbf", ink="#1a1020"),
    "turquesa": dict(base="#eefcff", socket="#0b2e4a", p1="#00b4c5", p2="#8be9ff",
                     a1="#ff4fa3", a2="#7b2cbf", a3="#ffb000", ink="#081a2a"),
    "dorada": dict(base="#fff3d6", socket="#3a0a0a", p1="#ffb000", p2="#ffe066",
                   a1="#d00000", a2="#ff6d00", a3="#6a040f", ink="#240505"),
}

uv = json.load(open(MESH))["uv"]


def pt(i):
    """Landmark -> pixel en la imagen (v de OBJ va hacia arriba, la imagen hacia abajo)."""
    return (uv[2 * i] * S, (1 - uv[2 * i + 1]) * S)


def centroid(ids):
    ps = [pt(i) for i in ids]
    return (sum(p[0] for p in ps) / len(ps), sum(p[1] for p in ps) / len(ps))


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def scaled(ids, k, center=None):
    c = center or centroid(ids)
    return [(c[0] + (p[0] - c[0]) * k, c[1] + (p[1] - c[1]) * k) for p in map(pt, ids)]


def petal(d, c, ang, r0, length, width, fill, ink, lw):
    """Petalo (elipse rotada) que nace a distancia r0 del centro c."""
    cx = c[0] + math.cos(ang) * (r0 + length / 2)
    cy = c[1] + math.sin(ang) * (r0 + length / 2)
    pts = []
    for k in range(24):
        t = 2 * math.pi * k / 24
        x, y = math.cos(t) * length / 2, math.sin(t) * width / 2
        pts.append((cx + x * math.cos(ang) - y * math.sin(ang), cy + x * math.sin(ang) + y * math.cos(ang)))
    d.polygon(pts, fill=fill, outline=ink, width=lw)


def circle(d, c, r, fill=None, outline=None, width=1):
    d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=fill, outline=outline, width=width)


def cempasuchil(d, c, r, P, lw):
    """Flor de cempasuchil: tres coronas de petalos y centro."""
    for ring, (n, k, col) in enumerate(((18, 1.0, P["p1"]), (14, 0.72, P["p2"]), (10, 0.45, P["p1"]))):
        off = ring * 0.3
        for i in range(n):
            ang = 2 * math.pi * i / n + off
            petal(d, c, ang, r * 0.12, r * k * 0.85, r * k * 0.38, col, P["ink"], lw)
    circle(d, c, r * 0.18, fill=P["a3"], outline=P["ink"], width=lw)


def heart(d, c, w, fill, inverted=False):
    """Corazon; inverted=True apunta hacia arriba (nariz de calavera)."""
    s = -1 if inverted else 1
    r = w / 4
    circle(d, (c[0] - r, c[1] - s * r * 0.4), r, fill=fill)
    circle(d, (c[0] + r, c[1] - s * r * 0.4), r, fill=fill)
    d.polygon([(c[0] - 2 * r, c[1] - s * r * 0.2), (c[0] + 2 * r, c[1] - s * r * 0.2), (c[0], c[1] + s * w * 0.6)], fill=fill)


def paint(P):
    img = Image.new("RGBA", (S, S), P["base"])
    d = ImageDraw.Draw(img)
    eye_w = dist(pt(33), pt(133))
    lw = max(int(eye_w * 0.06), 2)

    # --- papel picado colgando del borde de la frente
    cols = [P["a1"], P["a2"], P["p1"], P["a3"]]
    top = [pt(i) for i in FOREHEAD_TOP]
    for k, (a, b) in enumerate(zip(top, top[1:])):
        h = eye_w * 0.9
        x0, x1 = a[0], b[0]
        y0 = max(a[1], b[1]) - eye_w * 0.05
        flag = [(x0, y0 - eye_w), (x1, y0 - eye_w), (x1, y0 + h)]
        n = 4  # borde inferior en zigzag
        for j in range(n, -1, -1):
            flag.append((x0 + (x1 - x0) * j / n, y0 + h - (eye_w * 0.18 if j % 2 else 0)))
        d.polygon(flag, fill=cols[k % 4])
        cx, cy = (x0 + x1) / 2, y0 + h * 0.45   # recortes del papel picado
        circle(d, (cx, cy), eye_w * 0.12, fill=P["base"])
        for dx in (-1, 1):
            d.polygon([(cx + dx * eye_w * 0.28, cy - eye_w * 0.12), (cx + dx * eye_w * 0.4, cy),
                       (cx + dx * eye_w * 0.28, cy + eye_w * 0.12), (cx + dx * eye_w * 0.16, cy)], fill=P["base"])
    d.line(top, fill=P["ink"], width=lw * 2)

    # --- flor grande en la frente y florecitas en las sienes
    fore = pt(151)
    cempasuchil(d, (fore[0], fore[1] - eye_w * 0.15), eye_w * 0.85, P, lw)
    for t in (71, 301):
        c = pt(t)
        for i in range(8):
            petal(d, c, 2 * math.pi * i / 8, eye_w * 0.05, eye_w * 0.3, eye_w * 0.16, P["a1"], P["ink"], lw)
        circle(d, c, eye_w * 0.08, fill=P["p2"], outline=P["ink"], width=lw)

    # --- cuencas de los ojos con corona de petalos
    for eye in (LEFT_EYE, RIGHT_EYE):
        c = centroid(eye)
        r = max(dist(c, pt(i)) for i in eye) * 1.35
        for i in range(16):
            col = P["p1"] if i % 2 else P["p2"]
            petal(d, c, 2 * math.pi * i / 16, r * 0.85, r * 0.62, r * 0.32, col, P["ink"], lw)
        circle(d, c, r, fill=P["socket"], outline=P["ink"], width=lw * 2)
        for i in range(16):  # puntitos en la orilla de la cuenca
            ang = 2 * math.pi * (i + 0.5) / 16
            circle(d, (c[0] + math.cos(ang) * r * 0.86, c[1] + math.sin(ang) * r * 0.86), r * 0.05, fill=P["a2"])

    # --- puntos decorativos sobre las cejas
    for brow in (LEFT_BROW, RIGHT_BROW):
        for k, i in enumerate(brow[:5]):
            p = pt(i)
            circle(d, (p[0], p[1] - eye_w * 0.28), eye_w * 0.07, fill=P["a2"] if k % 2 else P["a1"], outline=P["ink"], width=lw)

    # --- mejillas: espirales de circulos y corazones
    for cheek in (205, 425):
        c = pt(cheek)
        circle(d, c, eye_w * 0.42, outline=P["a2"], width=lw * 3)
        circle(d, c, eye_w * 0.26, outline=P["a1"], width=lw * 3)
        circle(d, c, eye_w * 0.1, fill=P["a3"])
        for i in range(10):
            ang = 2 * math.pi * i / 10
            circle(d, (c[0] + math.cos(ang) * eye_w * 0.56, c[1] + math.sin(ang) * eye_w * 0.56), eye_w * 0.045, fill=P["p1"])

    # --- nariz: corazon invertido
    nw = dist(pt(98), pt(327)) * 1.1
    heart(d, centroid([1, 2, 98, 327]), nw, P["ink"], inverted=True)

    # --- boca cosida (dientes de calavera)
    a, b = pt(61), pt(291)
    ext = 0.35
    l = (a[0] - (b[0] - a[0]) * ext, a[1] - (b[1] - a[1]) * ext)
    r = (b[0] + (b[0] - a[0]) * ext, b[1] + (b[1] - a[1]) * ext)
    mouth_h = dist(pt(0), pt(17))
    d.line([l, r], fill=P["ink"], width=lw * 2)
    n = 12
    for k in range(n + 1):
        x = l[0] + (r[0] - l[0]) * k / n
        y = l[1] + (r[1] - l[1]) * k / n
        hk = mouth_h * (0.75 - 0.35 * abs(k / n - 0.5) * 2)
        d.line([(x, y - hk / 2), (x, y + hk / 2)], fill=P["ink"], width=lw * 2)

    # --- barbilla: gotas y puntos
    ch = pt(199)
    for dx in (-1, 0, 1):
        heart(d, (ch[0] + dx * eye_w * 0.45, ch[1] + abs(dx) * eye_w * -0.05), eye_w * (0.32 if dx else 0.42), P["a1"] if dx else P["a3"])

    # --- festón de puntos por la mandibula (de oreja a oreja pasando por la barbilla)
    center = centroid(FACE_OVAL)
    jaw = FACE_OVAL[FACE_OVAL.index(454):FACE_OVAL.index(234) + 1]
    for k, i in enumerate(jaw):
        p = pt(i)
        q = (center[0] + (p[0] - center[0]) * 0.9, center[1] + (p[1] - center[1]) * 0.9)
        circle(d, q, eye_w * (0.11 if k % 2 else 0.07), fill=[P["a1"], P["p1"], P["a2"]][k % 3], outline=P["ink"], width=lw)

    # --- contorno de la cara (borde nitido)
    oval = [pt(i) for i in FACE_OVAL]
    d.line(oval + oval[:1], fill=P["ink"], width=lw * 3, joint="curve")

    # --- transparencias: ojos y boca interior
    alpha = Image.new("L", (S, S), 255)
    ad = ImageDraw.Draw(alpha)
    for eye in (LEFT_EYE, RIGHT_EYE):
        ad.polygon(scaled(eye, 1.12), fill=0)
    ad.polygon(scaled(LIPS_INNER, 1.0), fill=0)
    img.putalpha(alpha)

    return img.resize((SIZE, SIZE), Image.LANCZOS)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for name, P in PALETTES.items():
        path = os.path.join(OUT_DIR, f"calavera-{name}.png")
        paint(P).save(path, optimize=True)
        print("OK", path)


if __name__ == "__main__":
    main()
