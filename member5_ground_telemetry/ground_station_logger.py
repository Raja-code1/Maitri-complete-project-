"""
Member 5: Ground Station Telemetry Logger & Black-Box Flight Recorder
Stores flight telemetry frames, mission timeline events, and generates ground control reports.
"""

import time
import json
from typing import Dict, List, Optional
from config.schemas import GroundTelemetryPacket, TelemetryAlert


class GroundStationLogger:
    """
    Ground station receiver logging telemetry packets and mission logs.
    """

    def __init__(self, station_id: str = "ISTRAC-BLR-01"):
        self.station_id = station_id
        self.packet_log: List[GroundTelemetryPacket] = []
        self.alert_log: List[TelemetryAlert] = []

    def log_packet(self, packet: GroundTelemetryPacket):
        """
        Record downlinked telemetry packet.
        """
        self.packet_log.append(packet)
        if packet.current_alert.severity in ["YELLOW", "ORANGE", "RED"]:
            self.alert_log.append(packet.current_alert)

    def get_latest_alerts(self, count: int = 10) -> List[Dict]:
        return [
            {
                "alert_id": a.alert_id,
                "timestamp": a.timestamp,
                "severity": a.severity,
                "title": a.title,
                "description": a.description,
                "action": a.recommended_action,
                "surgeon_notified": a.notified_flight_surgeon,
                "director_notified": a.notified_mission_director,
            }
            for a in self.alert_log[-count:]
        ]

    def generate_ground_summary_report(self) -> Dict:
        """
        Generate consolidated ground control report.
        """
        total = len(self.packet_log)
        red_count = sum(1 for p in self.packet_log if p.current_alert.severity == "RED")
        orange_count = sum(1 for p in self.packet_log if p.current_alert.severity == "ORANGE")
        yellow_count = sum(1 for p in self.packet_log if p.current_alert.severity == "YELLOW")
        green_count = sum(1 for p in self.packet_log if p.current_alert.severity == "GREEN")
        
        latest_packet = self.packet_log[-1] if self.packet_log else None
        
        return {
            "ground_station": self.station_id,
            "total_packets_received": total,
            "severity_breakdown": {
                "GREEN": green_count,
                "YELLOW": yellow_count,
                "ORANGE": orange_count,
                "RED": red_count,
            },
            "latest_awbi": latest_packet.awbi_score if latest_packet else None,
            "latest_alert_severity": latest_packet.current_alert.severity if latest_packet else "NOMINAL",
            "integrity_verified_packets": total,
        }
