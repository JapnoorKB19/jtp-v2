import struct
import hashlib

# Protocol Constants
FLAG_DATA = 0x00
FLAG_ACK  = 0x01
FLAG_SYN  = 0x02
FLAG_FIN  = 0x04

class JTPHeader:
    HEADER_FORMAT = '!BBIIH10s'
    HEADER_SIZE = 22

    def __init__(self, flags=FLAG_DATA, window_size=64, seq_num=0, ack_num=0, payload_len=0, payload=b''):
        self.flags = flags
        self.window_size = window_size
        self.seq_num = seq_num
        self.ack_num = ack_num
        self.payload_length = payload_len
        self.payload = payload  # <--- FIX: Actually save the payload!
        self.integrity_hash = self._generate_hash(payload) if payload else b'\x00' * 10

    def _generate_hash(self, data):
        """Generates the 10-byte truncated SHA-256 hash."""
        return hashlib.sha256(data).digest()[:10]

    def pack(self):
        """Packs the header fields into a 22-byte raw binary string."""
        return struct.pack(
            self.HEADER_FORMAT,
            self.flags,
            self.window_size,
            self.seq_num,
            self.ack_num,
            self.payload_length,
            self.integrity_hash
        )

    @classmethod
    def unpack(cls, packet):
        """Unpacks a raw binary string back into a JTPHeader object."""
        if len(packet) < cls.HEADER_SIZE:
            raise ValueError(f"Expected at least {cls.HEADER_SIZE} bytes, got {len(packet)}")

        header_bytes = packet[:cls.HEADER_SIZE]
        unpacked = struct.unpack(cls.HEADER_FORMAT, header_bytes)

        # Reconstruct the header object
        obj = cls(
            flags=unpacked[0],
            window_size=unpacked[1],
            seq_num=unpacked[2],
            ack_num=unpacked[3]
        )
        obj.payload_length = unpacked[4]
        obj.integrity_hash = unpacked[5]
        
        # <--- FIX: Extract the payload from the rest of the packet!
        obj.payload = packet[cls.HEADER_SIZE:] 
        
        return obj

    def verify_payload(self, payload_data):
        """Checks if the received payload matches the integrity hash."""
        expected_hash = self._generate_hash(payload_data)
        return self.integrity_hash == expected_hash
