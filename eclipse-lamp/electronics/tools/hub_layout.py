"""Geometry shared by the hub footprints and the hub PCB generator.

44 angular slots around the Ø36 hub: each colour channel owns 10 consecutive slots
(one sprig wire pair each) plus one empty 'gap' slot where its feed goes inward.
Angles in degrees, 0 = toward +Y screen-up (KiCad -y), clockwise.
"""
import math

N_SLOTS = 44
CHANNEL_ORDER = ("W1", "C1", "W2", "C2")     # around the hub
R_BOARD, R_HOLE = 18.0, 2.0
R_OUT, R_IN = 15.0, 11.3                     # sprig pad rings (A outer, K inner)
R_FEED_A, R_FEED_K, R_AUX = 7.6, 5.2, 6.4   # trunk-wire pad radii
NTC_R, NTC_ANG = 9.3, 45.0
# J1 (trunk harness, same pinout as core J2) pin -> (radius, angle)
J1_PIN_NET = {1: "C1_K", 2: "C1_A", 3: "W1_A", 4: "W1_K", 5: "NTC", 6: "GND",
              7: "W2_K", 8: "W2_A", 9: "C2_A", 10: "C2_K"}


def slot_angle(s):
    return 360.0 * s / N_SLOTS


def sprig_slot(channel, k):
    """Slot of the k-th (0..9) sprig in a channel's series chain."""
    n = CHANNEL_ORDER.index(channel)
    return 11 * n + 1 + k


def j1_pad_pos(pin):
    net = J1_PIN_NET[pin]
    if net == "NTC":
        return R_AUX, NTC_ANG - 6.0
    if net == "GND":
        return R_AUX, NTC_ANG + 6.0
    ch, end = net.split("_")
    n = CHANNEL_ORDER.index(ch)
    if end == "A":
        return R_FEED_A, slot_angle(11 * n)
    return R_FEED_K, slot_angle(11 * n + 10)


def polar(r, a, c=(0.0, 0.0)):
    t = math.radians(a)
    return c[0] + r * math.sin(t), c[1] - r * math.cos(t)
