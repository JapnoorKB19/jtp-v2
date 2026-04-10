import struct
import hashlib

class JTPHeader:
    # Structure format: 
    # !   : Network byte order (Big-Endian)
    # B   : 1 byte unsigned char (Flags)
    # B   : 1 byte unsigned char (Window Size)
    # I   : 4 byte unsigned int (Seq Number)
    # I   : 4 byte unsigned int (Ack Number)
    # H   : 2 byte unsigned short (Payload Length)
    # 10s : 10 byte string/bytes (Integrity Hash)
    # Total = 1 + 1 + 4 + 4 + 2 + 10 = 22 bytes
    HEADER_FORMAT = '!BBIIH10s'
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    # Flag Bitmasks for easy reference
    FLAG_DATA = 0x00
    FLAG_SYN  = 0x01
    FLAG_ACK  = 0x02
    FLAG_FIN  = 0x04

    def __init__(self, flags, window_size, seq_num, ack_num, payload_data=b''):
        self.flags = flags
        self.window_size = window_size
        self.seq_num = seq_num
        self.ack_num = ack_num
        self.payload_length = len(payload_data)
        self.integrity_hash = self._generate_hash(payload_data)

    def _generate_hash(self, data):
        """Generates a truncated SHA-256 hash of the payload for integrity."""
        if not data:
            return b'\x00' * 10
        full_hash = hashlib.sha256(data).digest()
        return full_hash[:10]  # Take first 10 bytes to keep header compact

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
    def unpack(cls, header_bytes):
        """Unpacks a 22-byte raw binary string back into a JTPHeader object."""
        if len(header_bytes) != cls.HEADER_SIZE:
            raise ValueError(f"Expected {cls.HEADER_SIZE} bytes, got {len(header_bytes)}")
        
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
        return obj

    def verify_payload(self, payload_data):
        """Checks if the received payload matches the integrity hash."""
        expected_hash = self._generate_hash(payload_data)
        return self.integrity_hash == expected_hash
