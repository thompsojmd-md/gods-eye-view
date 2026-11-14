#!/usr/bin/env python3
"""Minimal SNTP server. Run as root/admin (UDP 123): sudo python3 ntp_server.py [port]"""
import socket, struct, sys, time

OFFSET = 0  # ponytail: seconds to add to system clock; NTP is UTC, Xbox applies its own timezone
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
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        # one-shot check: fake client request -> server reply must carry current time
        req = bytes([0x23]) + bytes(39) + ts(12345.5)
        r = reply(req, time.time())
        assert len(r) == 48 and r[0] & 7 == 4 and r[24:32] == ts(12345.5)
        assert abs(struct.unpack("!I", r[40:44])[0] - EPOCH - time.time()) < 2
        print("ok")
    else:
        main(int(sys.argv[1]) if len(sys.argv) > 1 else 123)
