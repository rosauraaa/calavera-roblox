"""Convierte la malla canonica de MediaPipe (OBJ) en un JSON listo para three.js.

El OBJ trae indices de vertice y de UV distintos (f v/vt). MediaPipe entrega 468
landmarks en el mismo orden que los vertices "v", asi que aqui se reordenan las UV
para que haya exactamente una UV por landmark.

Uso:
    python tools/build_mesh.py
Salida:
    assets/mesh/face_mesh.json  ->  {"uv": [u0, v0, u1, v1, ...], "index": [a, b, c, ...]}
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets", "mesh", "canonical_face_model.obj")
OUT = os.path.join(ROOT, "assets", "mesh", "face_mesh.json")


def load_obj(path):
    verts, uvs, faces = [], [], []
    for line in open(path, encoding="utf-8"):
        parts = line.split()
        if not parts:
            continue
        if parts[0] == "v":
            verts.append(tuple(map(float, parts[1:4])))
        elif parts[0] == "vt":
            uvs.append(tuple(map(float, parts[1:3])))
        elif parts[0] == "f":
            faces.append([tuple(int(i) - 1 for i in p.split("/")[:2]) for p in parts[1:]])
    return verts, uvs, faces


def per_vertex_uv(verts, uvs, faces):
    uv = [None] * len(verts)
    for face in faces:
        for vi, ti in face:
            if uv[vi] is not None and uv[vi] != uvs[ti]:
                raise ValueError(f"el vertice {vi} tiene dos UV distintas")
            uv[vi] = uvs[ti]
    missing = [i for i, u in enumerate(uv) if u is None]
    assert not missing, f"vertices sin UV: {missing}"
    return uv


def main():
    verts, uvs, faces = load_obj(SRC)
    uv = per_vertex_uv(verts, uvs, faces)
    data = {
        "uv": [round(c, 6) for u in uv for c in u],
        "index": [vi for face in faces for vi, _ in face],
    }
    assert len(verts) == 468 and len(data["index"]) % 3 == 0
    json.dump(data, open(OUT, "w"), separators=(",", ":"))
    print(f"OK {OUT}: {len(verts)} vertices, {len(faces)} triangulos")


if __name__ == "__main__":
    main()
