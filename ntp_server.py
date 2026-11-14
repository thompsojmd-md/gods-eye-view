#!/usr/bin/env python3
"""Minimal SNTP server. Run as root/admin (UDP 123):
  sudo python3 ntp_server.py [port] [--at "2030-01-01 12:00:00"]   (--at is UTC; clock keeps ticking from there)
  --offset SECONDS shifts the real clock instead."""
import argparse, calendar, socket, struct, time

OFFSET = 0  # seconds added to the system clock; NTP is UTC, Xbox applies its own timezone
EPOCH = 2208988800  # 1900 -> 1970

def ts(t):
    return struct.pack("!II", int(t) + EPOCH, int((t % 1) * 2**32))

def reply(req, now):
    vn = (req[0] >> 3) & 7 or 4
    # LI=0, VN, mode=4 | stratum 1 | poll | precision | root delay/disp | refid
    hdr = struct.pack("!BBbb II 4s", (vn << 3) | 4, 1, req[2], -20, 0, 0, b"LOCL")
    return hdr + ts(now) + req[40:48] + ts(now) + ts(time.time() + OFFSET)

def main(port=123):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("0.0.0.0", port))
    print(f"NTP listening on UDP {port}")
    while True:
        req, addr = s.recvfrom(512)
        if len(req) >= 48:
            s.sendto(reply(req, time.time() + OFFSET), addr)
            print("served", addr[0])

if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("port", nargs="?", type=int, default=123)
    a.add_argument("--at", help='fake UTC time "YYYY-MM-DD HH:MM:SS"')
    a.add_argument("--offset", type=float, help="seconds to add to real time")
    a.add_argument("--selftest", action="store_true")
    a = a.parse_args()
    if a.at:
        OFFSET = calendar.timegm(time.strptime(a.at, "%Y-%m-%d %H:%M:%S")) - time.time()
    elif a.offset:
        OFFSET = a.offset
    if a.selftest:
        # fake client request -> reply must echo originate ts and carry current time
        req = bytes([0x23]) + bytes(39) + ts(12345.5)
        r = reply(req, time.time())
        assert len(r) == 48 and r[0] & 7 == 4 and r[24:32] == ts(12345.5)
        assert abs(struct.unpack("!I", r[40:44])[0] - EPOCH - time.time() - OFFSET) < 2
        print("ok")
    else:
        main(a.port)
