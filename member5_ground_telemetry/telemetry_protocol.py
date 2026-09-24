"""
Member 5: Space Telemetry Protocol & CCSDS Packet Encoder
Implements CCSDS-compliant packet structure, CRC-32 integrity, and ground downlink serialization.
"""

import time
import struct
import zlib
import json
from typing import Dict, Optional, Tuple

from config.settings import (
    TELEMETRY_PACKET_APID,
    STATION_ID,
    MISSION_NAME,
    GROUND_STATION_ID,
    SIMULATED_UPLINK_DELAY_SEC,
)
from config.schemas import (
    CCSDSPacketHeader,
    GroundTelemetryPacket,
    MultimodalFusionContext,
    TelemetryAlert,
    PsychologicalIntervention,
)


class CCSDSPacketEncoder:
    """
    Encodes astronaut health telemetry into standardized CCSDS Space Packet format.
    """

    def __init__(self, apid: int = TELEMETRY_PACKET_APID):
        self.apid = apid
        self.packet_counter = 0

    def create_ccsds_header(self, payload_length_bytes: int) -> CCSDSPacketHeader:
        self.packet_counter = (self.packet_counter + 1) % 16384
        return CCSDSPacketHeader(
            version_number=0,
            packet_type=0,  # Telemetry
            secondary_header_flag=1,
            application_process_id=self.apid,
            sequence_flags=3,  # Unsegmented standalone packet
            packet_sequence_count=self.packet_counter,
            packet_data_length=payload_length_bytes + 6 - 1,
        )

    def pack_binary_frame(
        self,
        awbi: float,
        stress: float,
        fatigue: float,
        cog_load: float,
        perclos: float,
        pitch: float,
        vocal_strain: float,
        severity_code: int,
    ) -> bytes:
        """
        Packs fixed-width space telemetry binary frame:
        - 4-byte float: awbi
        - 4-byte float: stress
        - 4-byte float: fatigue
        - 4-byte float: cog_load
        - 4-byte float: perclos
        - 4-byte float: pitch
        - 4-byte float: vocal_strain
        - 1-byte uint8: severity_code (0=GREEN, 1=YELLOW, 2=ORANGE, 3=RED)
        """
        return struct.pack(
            "!fffffffB",
            float(awbi),
            float(stress),
            float(fatigue),
            float(cog_load),
            float(perclos),
            float(pitch),
            float(vocal_strain),
            int(severity_code),
        )


class TelemetryProtocol:
    """
    Manages end-to-end packet creation, CRC-32 verification, and ground transmission.
    """

    SEVERITY_MAP = {"GREEN": 0, "YELLOW": 1, "ORANGE": 2, "RED": 3}

    def __init__(self):
        self.encoder = CCSDSPacketEncoder()
        self.total_packets_transmitted = 0

    def generate_packet(
        self,
        fusion_context: MultimodalFusionContext,
        alert: TelemetryAlert,
        intervention: Optional[PsychologicalIntervention] = None,
    ) -> GroundTelemetryPacket:
        """
        Generate complete CCSDS telemetry packet with CRC-32 checksum and Hex frame.
        """
        self.total_packets_transmitted += 1
        now = time.time()
        packet_id = f"TLM-{int(now * 1000)}-{self.total_packets_transmitted:06d}"
        
        severity_code = self.SEVERITY_MAP.get(alert.severity, 0)
        binary_payload = self.encoder.pack_binary_frame(
            awbi=fusion_context.awbi_score,
            stress=fusion_context.stress_index,
            fatigue=fusion_context.fatigue_index,
            cog_load=fusion_context.cognitive_load_index,
            perclos=fusion_context.visual_state.fatigue_metrics.perclos,
            pitch=fusion_context.audio_state.acoustic_features.f0_pitch_hz,
            vocal_strain=fusion_context.audio_state.vocal_strain_score,
            severity_code=severity_code,
        )
        
        # Calculate CRC-32 checksum
        crc_val = zlib.crc32(binary_payload)
        crc_hex = f"0x{crc_val & 0xFFFFFFFF:08X}"
        hex_payload = binary_payload.hex().upper()
        
        header = self.encoder.create_ccsds_header(len(binary_payload))
        
        packet = GroundTelemetryPacket(
            packet_id=packet_id,
            timestamp=now,
            station_id=STATION_ID,
            mission_id=MISSION_NAME,
            astronaut_id=fusion_context.astronaut_id,
            ccsds_header=header,
            awbi_score=fusion_context.awbi_score,
            stress_index=fusion_context.stress_index,
            fatigue_index=fusion_context.fatigue_index,
            cognitive_load=fusion_context.cognitive_load_index,
            visual_emotion=fusion_context.visual_state.primary_emotion,
            audio_emotion=fusion_context.audio_state.audio_emotion,
            perclos_val=fusion_context.visual_state.fatigue_metrics.perclos,
            pitch_mean_hz=fusion_context.audio_state.acoustic_features.f0_pitch_hz,
            vocal_strain_score=fusion_context.audio_state.vocal_strain_score,
            current_alert=alert,
            active_intervention=intervention,
            crc32_checksum=crc_hex,
            hex_payload=hex_payload,
            is_downlink_acknowledged=True,
        )
        
        return packet

    def verify_packet_integrity(self, hex_payload: str, expected_crc: str) -> bool:
        """
        Verify CRC-32 checksum integrity of transmitted telemetry frame.
        """
        try:
            data = bytes.fromhex(hex_payload)
            calc_crc = f"0x{zlib.crc32(data) & 0xFFFFFFFF:08X}"
            return calc_crc.upper() == expected_crc.upper()
        except Exception:
            return False
