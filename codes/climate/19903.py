DEVICE_DATA = {
    "manufacturer": "Perfect Aire",
    "supported_models": [
        "RG10A(D2S)/BGEFU1",
    ],
    "commandsEncoding": "Generic",
    "minTemperature": {
        "cool": 60,
        "heat": 60,
        "auto": 60,
        "dry": 60,
    },
    "maxTemperature": {
        "cool": 86,
        "heat": 86,
        "auto": 86,
        "dry": 86,
    },
    "precision": 1,
    "operationModes": [
        "cool",
        "heat",
        "auto",
        "dry",
    ],
    "fanModes": {
        "auto",
        "low",
        "low_medium" "medium",
        "medium_high",
        "high",
    },
    "swingModes": {
        "on",
        "top",
        "upper",
        "middle",
        "lower",
        "bottom",
    },
    "toggles": {
        "turbo_mode",
        "self_cleaning",
    },
}


def command(hvac_mode, swing_mode, fan_mode, temp, turbo_mode=False, cleaning_enabled=False):
    # 1. Handle OFF Command (Short distinct packet: 4d,de,07)
    if hvac_mode == "off":
        offPkt = [0x4D, 0xDE, 0x07]
        return (
            "nec",
            "tp=528,t0=519,t1=1571,ph=4272,pl=4303,cm=3,a=2,pg=5096",
            [
                offPkt,
                offPkt,
            ],
        )

    # 2. Mode Constraints
    # Auto and Dry force Fan to Auto
    if hvac_mode in ["auto", "dry"]:
        fan_mode = "auto"

    # 3. Lookup Tables

    # Packet 1, Byte 4: "Coarse" Temp
    p1_temp_map = {
        60: 0x00,
        61: 0x00,
        62: 0x00,
        63: 0x00,
        64: 0x08,
        65: 0x08,
        66: 0x0C,
        67: 0x0C,
        68: 0x04,
        69: 0x04,
        70: 0x06,
        71: 0x06,
        72: 0x0E,
        73: 0x0A,
        74: 0x0A,
        75: 0x02,
        76: 0x02,
        77: 0x03,
        78: 0x03,
        79: 0x0B,
        80: 0x0B,
        81: 0x09,
        82: 0x09,
        83: 0x01,
        84: 0x05,
        85: 0x05,
        86: 0x0D,
    }

    # Packet 2, Byte 2: "Fine Tune" Temp Bit
    p2_fine_tune_map = {
        60: 0x00,
        61: 0x04,
        62: 0x00,
        63: 0x04,
        64: 0x00,
        65: 0x04,
        66: 0x00,
        67: 0x04,
        68: 0x00,
        69: 0x04,
        70: 0x00,
        71: 0x04,
        72: 0x00,
        73: 0x00,
        74: 0x04,
        75: 0x00,
        76: 0x04,
        77: 0x00,
        78: 0x04,
        79: 0x00,
        80: 0x04,
        81: 0x00,
        82: 0x00,
        83: 0x04,
        84: 0x00,
        85: 0x04,
        86: 0x00,
    }

    # Packet 2, Byte 5: BASE Checksum (for Cool Mode + Auto Fan)
    # This serves as our anchor. We add offsets to this value.
    p2_base_checksum = {
        60: 0x32,
        61: 0x36,
        62: 0x3C,
        63: 0x3A,
        64: 0x3C,
        65: 0x3A,
        66: 0x3C,
        67: 0x3A,
        68: 0x3C,
        69: 0x3A,
        70: 0x3C,
        71: 0x3A,
        72: 0x3C,
        73: 0x3C,
        74: 0x3A,
        75: 0x3C,
        76: 0x3A,
        77: 0x3C,
        78: 0x3A,
        79: 0x3C,
        80: 0x3A,
        81: 0x3C,
        82: 0x3C,
        83: 0x3A,
        84: 0x3C,
        85: 0x3A,
        86: 0x3C,
    }

    # Fan Configuration Map
    # Key: Fan Mode
    # Value: (Packet 1 Header Byte, Packet 2 Fan Byte, Packet 2 Checksum Offset)
    fan_config = {
        # Auto: P1=FD, P2=66, Offset=0
        "auto": (0xFD, 0x66, 0x00),
        # Low (20%): P1=FF, P2=28, Offset=+1B (0x1B)
        "low": (0xFF, 0x28, 0x1B),
        # Low-Mid (40%): P1=F9, P2=14, Offset=+43 (0x43)
        "low_medium": (0xF9, 0x14, 0x43),
        # Mid (60%): P1=FA, P2=3C, Offset=+0C (0x0C)
        "medium": (0xFA, 0x3C, 0x0C),
        # Mid-High (80%): P1=FC, P2=0A, Offset=+28 (0x28)
        "medium_high": (0xFC, 0x0A, 0x28),
        # High (100%): P1=FC, P2=26, Offset=+20 (0x20)
        "high": (0xFC, 0x26, 0x20),
    }

    # 4. Get Fan Parameters
    p1_fan_header, p2_fan_byte, p2_cs_offset = fan_config.get(fan_mode, (0xFD, 0x66, 0x00))

    # 5. Build PACKET 1 (Header)
    p1_b0 = 0x4D
    p1_b1 = 0xB2
    p1_b2 = p1_fan_header
    p1_b3 = (~p1_b2) & 0xFF  # Byte 3 is always inverse of Byte 2

    p1_b4 = p1_temp_map.get(int(temp), 0x00)

    # Apply Mode Offsets to P1 Byte 4
    if hvac_mode == "heat":
        p1_b4 = (p1_b4 + 0x30) & 0xFF
    elif hvac_mode == "auto":
        p1_b2 = 0xF8  # Auto mode changes the header entirely
        p1_b3 = 0x07
        p1_b4 = (p1_b4 + 0x10) & 0xFF
    elif hvac_mode == "dry":
        p1_b2 = 0xF8  # Dry mode changes the header entirely
        p1_b3 = 0x07
        p1_b4 = (p1_b4 + 0x20) & 0xFF

    p1_b5 = (~p1_b4) & 0xFF  # Checksum is inverse of Byte 4

    packet1 = [p1_b0, p1_b1, p1_b2, p1_b3, p1_b4, p1_b5]

    # 6. Build PACKET 2 (Payload)
    p2_b0 = 0xAB

    # Auto/Dry Force specific Fan Bytes in P2
    if hvac_mode in ["auto", "dry"]:
        p2_fan_byte = 0xA6
        p2_cs_offset += 0xA0  # Offset for Auto/Dry checksum

    p2_b1 = p2_fan_byte
    p2_b2 = p2_fine_tune_map.get(int(temp), 0x00)

    # Byte 3: Standard is 0x80, but <= 61F it becomes 0x88
    # This logic was confirmed in your Cool 60/61 vs 62+ logs
    if int(temp) <= 61:
        p2_b3 = 0x88
    else:
        p2_b3 = 0x80

    p2_b4 = 0x00

    # Checksum Calculation
    base_cs = p2_base_checksum.get(int(temp), 0x3C)
    p2_b5 = (base_cs + p2_cs_offset) & 0xFF

    packet2 = [p2_b0, p2_b1, p2_b2, p2_b3, p2_b4, p2_b5]

    # 7. Final Sequence
    # Remote sequence is P1, P1, P2
    return (
        "nec",
        "tp=528,t0=519,t1=1571,ph=4272,pl=4303,cm=3,a=2,pg=5096",
        [
            packet1,
            packet1,
            packet2,
        ],
    )
