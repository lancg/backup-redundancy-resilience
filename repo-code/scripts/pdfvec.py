#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Minimal vector PDF writer: paths, rectangles, circles, text (base-14 fonts).

Text supports `_{...}` for subscripts and Greek letters via the Symbol font.
All coordinates are top-left; output flips them.
"""

import math
from PIL import ImageFont

# characters that live in the Symbol font (Greek letters and maths operators)
SYMBOL = {"≤": "\243", "≥": "\263", "×": "\264", "−": "-", "→": "\256",
          "∅": "\306", "±": "\261", "≈": "\273", "∞": "\245"}
GREEK = {"θ": "q", "ρ": "r", "λ": "l", "Θ": "Q", "Δ": "D", "π": "p",
         "ε": "e", "δ": "d", "κ": "k", "ω": "w", "Σ": "S", "μ": "m",
         "α": "a", "β": "b", "γ": "g", "σ": "s", "φ": "j", "τ": "t"}
NAMED = {"white": (1, 1, 1), "black": (0, 0, 0)}
_F = {}


def _pil(size, bold):
    key = (size, bold)
    if key not in _F:
        p = "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"
        _F[key] = ImageFont.truetype(p, max(1, int(round(size))))
    return _F[key]


def _esc(s):
    return s.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def _segments(s):
    out, i = [], 0
    while i < len(s):
        j = s.find("_{", i)
        if j < 0:
            out.append((s[i:], False))
            break
        if j > i:
            out.append((s[i:j], False))
        k = s.find("}", j)
        if k < 0:
            out.append((s[j:], False))
            break
        out.append((s[j + 2:k], True))
        i = k + 1
    return out


class PDF:
    def __init__(self, width, height):
        self.W, self.H = width, height
        self.ops = []

    # ------------------------------------------------------------- colours
    def _set(self, c, stroke=True):
        r, g, b = NAMED[c] if c in NAMED else (int(c[1:3], 16) / 255,
                                               int(c[3:5], 16) / 255,
                                               int(c[5:7], 16) / 255)
        self.ops.append("%.3f %.3f %.3f %s" % (r, g, b, "RG" if stroke else "rg"))

    # --------------------------------------------------------------- shapes
    def line(self, pts, color="#000000", width=1.0, dash=None):
        if len(pts) < 2:
            return
        self._set(color)
        self.ops.append("%.2f w" % width)
        self.ops.append("[%s] 0 d" % (dash or ""))
        self.ops.append("%.2f %.2f m" % (pts[0][0], self.H - pts[0][1]))
        for p in pts[1:]:
            self.ops.append("%.2f %.2f l" % (p[0], self.H - p[1]))
        self.ops.append("S")

    def rect(self, x0, y0, x1, y1, stroke=None, fill=None, width=0.7):
        if fill:
            self._set(fill, False)
            self.ops.append("%.2f %.2f %.2f %.2f re f" % (x0, self.H - y1, x1 - x0, y1 - y0))
        if stroke:
            self._set(stroke)
            self.ops.append("%.2f w" % width)
            self.ops.append("%.2f %.2f %.2f %.2f re S" % (x0, self.H - y1, x1 - x0, y1 - y0))

    def circle(self, cx, cy, r, fill="#000000"):
        k, y = 0.5523 * r, self.H - cy
        self._set(fill, False)
        self.ops.append("%.2f %.2f m" % (cx + r, y))
        self.ops.append("%.2f %.2f %.2f %.2f %.2f %.2f c" % (cx + r, y - k, cx + k, y - r, cx, y - r))
        self.ops.append("%.2f %.2f %.2f %.2f %.2f %.2f c" % (cx - k, y - r, cx - r, y - k, cx - r, y))
        self.ops.append("%.2f %.2f %.2f %.2f %.2f %.2f c" % (cx - r, y + k, cx - k, y + r, cx, y + r))
        self.ops.append("%.2f %.2f %.2f %.2f %.2f %.2f c" % (cx + k, y + r, cx + r, y + k, cx + r, y))
        self.ops.append("f")

    # ----------------------------------------------------------------- text
    def width(self, s, size, bold=False):
        w = 0.0
        f = _pil(size, bold)
        for ch in s:
            w += 0.58 * size if (ch in GREEK or ch in SYMBOL) else f.getlength(ch)
        return w

    def _show(self, x, y, s, size, color, bold):
        """Emit glyphs at PDF coordinates (y already flipped by caller)."""
        self._set(color, False)
        f = _pil(size, bold)
        for ch in s:
            if ch in GREEK or ch in SYMBOL:
                code = GREEK.get(ch) or SYMBOL[ch]
                self.ops.append("BT /F3 %.2f Tf %.3f %.3f Td (%s) Tj ET"
                                % (size, x, y, _esc(code)))
                x += 0.58 * size
            else:
                self.ops.append("BT /F%s %.2f Tf %.3f %.3f Td (%s) Tj ET"
                                % ("2" if bold else "1", size, x, y, _esc(ch)))
                x += f.getlength(ch)

    def text(self, x, y, s, size, color="#000000", bold=False, anchor="left"):
        total = 0.0
        for t, sub in _segments(s):
            total += self.width(t, size * 0.74 if sub else size, bold)
        if anchor == "center":
            x -= total / 2
        elif anchor == "right":
            x -= total
        for t, sub in _segments(s):
            sz = size * 0.74 if sub else size
            dy = 0.22 * size if sub else 0.0
            self._show(x, self.H - (y + dy), t, sz, color, bold)
            x += self.width(t, sz, bold)

    def text_vertical(self, x, y, s, size, color="#000000"):
        """Rotated 90 degrees counter-clockwise, centred on (x, y)."""
        w = self.width(s, size)
        self.ops.append("q")
        self.ops.append("0 1 -1 0 %.2f %.2f cm" % (x, self.H - y))
        self._show(-w / 2, -size * 0.35, s, size, color, False)
        self.ops.append("Q")

    # --------------------------------------------------------------- output
    def save(self, path):
        content = "\n".join(self.ops).encode("latin-1", "replace")
        objs = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            ("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %d %d] /Resources << /Font << "
             "/F1 5 0 R /F2 6 0 R /F3 7 0 R >> >> /Contents 4 0 R >>" % (self.W, self.H)).encode(),
            b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Symbol >>",
        ]
        out, offsets = bytearray(b"%PDF-1.4\n"), []
        for i, o in enumerate(objs, 1):
            offsets.append(len(out))
            out += ("%d 0 obj\n" % i).encode() + o + b"\nendobj\n"
        xref = len(out)
        out += ("xref\n0 %d\n" % (len(objs) + 1)).encode() + b"0000000000 65535 f \n"
        for off in offsets:
            out += ("%010d 00000 n \n" % off).encode()
        out += ("trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n"
                % (len(objs) + 1, xref)).encode()
        open(path, "wb").write(out)
