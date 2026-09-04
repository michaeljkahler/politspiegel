#!/usr/bin/env python3
"""
Tonspur für die Reels, selbst erzeugt
=====================================
Ein ruhiges, synthetisches Stück: Flächenklang mit vier Akkorden, darüber ein
leises Zupfmuster, dazu ein weicher Impuls bei jedem Bildwechsel. Erzeugt aus
Sinus- und Dreieckschwingungen mit numpy, ohne fremde Aufnahmen. Damit gibt es
keine Lizenz, keine Namensnennung und keine Content-ID-Ansprüche, und das
Stück passt sich der Länge und den Schnittpunkten jedes Videos an.

Verwendung aus social.py:
    from ton import tonspur
    tonspur(dauern, pfad_wav)      # dauern: Sekunden je Bild, Reihenfolge wie im Video

Einzeln zum Anhören:
    python3 scripts/ton.py 3.5 4 4 4 3   # schreibt output/ton_probe.wav
"""
import math
import struct
import sys
import wave
from pathlib import Path

import numpy as np

RATE = 44100
BPM = 76
TAKT = 60.0 / BPM * 4          # Sekunden je 4/4-Takt

# D-Dur: D, A, Bm, G (Grundton in Hz, Dreiklang als Halbtonschritte)
AKKORDE = [
    (146.83, (0, 4, 7)),      # D
    (110.00, (0, 4, 7)),      # A
    (123.47, (0, 3, 7)),      # Bm
    (98.00, (0, 4, 7)),       # G
]


def ton(freq, dauer, form="sinus", rate=RATE):
    t = np.arange(int(dauer * rate)) / rate
    if form == "dreieck":
        return 2 * np.abs(2 * ((t * freq) % 1) - 1) - 1
    return np.sin(2 * np.pi * freq * t)


def huelle(n, an, ab, halten=1.0):
    """Lautstärkeverlauf: Einschwingen, Halten, Ausklingen (Anteile der Länge)."""
    e = np.ones(n) * halten
    a = int(n * an)
    b = int(n * ab)
    if a:
        e[:a] = np.linspace(0, halten, a)
    if b:
        e[-b:] = np.linspace(halten, 0, b)
    return e


def tiefpass(x, alpha=0.05):
    """Einfacher Tiefpass erster Ordnung, macht Dreieck und Sinus weicher."""
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc += alpha * (v - acc)
        y[i] = acc
    return y


def flaeche(gesamt):
    """Flächenklang: je Takt ein Akkord, drei leicht verstimmte Stimmen je Ton."""
    out = np.zeros(int(gesamt * RATE))
    t0 = 0.0
    k = 0
    while t0 < gesamt:
        grund, stufen = AKKORDE[k % len(AKKORDE)]
        n = int(min(TAKT * 2, gesamt - t0) * RATE)
        block = np.zeros(n)
        for st in stufen:
            f = grund * 2 ** (st / 12)
            for verstimmung in (-0.15, 0.0, 0.15):
                block += ton(f * 2 ** (verstimmung / 1200) * 2, n / RATE) * 0.5
                block += ton(f * 2 ** (verstimmung / 1200), n / RATE)
        block *= huelle(n, 0.25, 0.25, 1.0)
        i0 = int(t0 * RATE)
        out[i0:i0 + n] += block[:len(out) - i0]
        t0 += TAKT * 2
        k += 1
    return out / (np.max(np.abs(out)) + 1e-9)


def zupfen(gesamt):
    """Achtel-Arpeggio über den Akkordtönen, kurz angeschlagen, leise."""
    out = np.zeros(int(gesamt * RATE))
    achtel = TAKT / 8
    t0 = 0.0
    i = 0
    while t0 < gesamt:
        takt = int(t0 // (TAKT * 2))
        grund, stufen = AKKORDE[takt % len(AKKORDE)]
        muster = (0, 1, 2, 1, 0, 2, 1, 2)
        st = stufen[muster[i % 8]]
        f = grund * 4 * 2 ** (st / 12)
        n = int(achtel * 1.6 * RATE)
        note = ton(f, n / RATE, "dreieck") * huelle(n, 0.01, 0.85, 0.5)
        i0 = int(t0 * RATE)
        out[i0:i0 + n] += note[:len(out) - i0]
        t0 += achtel
        i += 1
    return out / (np.max(np.abs(out)) + 1e-9)


def impulse(dauern):
    """Weicher, tiefer Impuls an jedem Bildwechsel."""
    gesamt = sum(dauern)
    out = np.zeros(int(gesamt * RATE))
    t = 0.0
    for d in dauern[:-1]:
        t += d
        n = int(0.35 * RATE)
        f = np.linspace(180, 70, n)
        phase = np.cumsum(2 * np.pi * f / RATE)
        klick = np.sin(phase) * huelle(n, 0.005, 0.9, 1.0)
        i0 = int(t * RATE)
        out[i0:i0 + n] += klick[:len(out) - i0]
    return out


def tonspur(dauern, pfad, lautstaerke=0.6):
    gesamt = float(sum(dauern))
    mix = (tiefpass(flaeche(gesamt), 0.08) * 0.55
           + tiefpass(zupfen(gesamt), 0.25) * 0.22
           + impulse(dauern) * 0.5)
    n = len(mix)
    mix *= huelle(n, min(1.5 / gesamt, 0.3), min(2.5 / gesamt, 0.4), 1.0)   # Ein- und Ausblenden
    mix = mix / (np.max(np.abs(mix)) + 1e-9) * lautstaerke
    daten = (mix * 32767).astype(np.int16)
    stereo = np.column_stack([daten, daten]).ravel()
    with wave.open(str(pfad), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(stereo.tobytes())
    return pfad


if __name__ == "__main__":
    dauern = [float(x) for x in sys.argv[1:]] or [3.5, 4, 4, 4, 3]
    ziel = Path(__file__).resolve().parent.parent / "output" / "ton_probe.wav"
    ziel.parent.mkdir(exist_ok=True)
    tonspur(dauern, ziel)
    print(ziel, f"{sum(dauern):.1f} s")
