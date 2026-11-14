use smart_servo_core::{Result, SmartServoError};

pub const REQ_HEADER: [u8; 2] = [0x12, 0x4c];
pub const RESP_HEADER: [u8; 2] = [0x05, 0x1c];

pub const CODE_PING: u8 = 1;
pub const CODE_QUERY_SERVO_MONITOR: u8 = 22;
pub const CODE_SET_SERVO_ANGLE: u8 = 8;
pub const CODE_SET_DAMPING: u8 = 9;
pub const CODE_QUERY_SERVO_ANGLE: u8 = 10;
pub const CODE_SET_SERVO_ANGLE_BY_INTERVAL: u8 = 11;
pub const CODE_SET_SERVO_ANGLE_MTURN: u8 = 13;
pub const CODE_SET_SERVO_ANGLE_MTURN_BY_INTERVAL: u8 = 14;
pub const CODE_QUERY_SERVO_ANGLE_MTURN: u8 = 16;
pub const CODE_RESET_MTURN: u8 = 17;
pub const CODE_SET_ORIGIN: u8 = 23;
pub const CODE_SET_STOP_MODE: u8 = 24;
pub const CODE_SYNC_COMMAND: u8 = 25;

#[derive(Debug, Clone)]
pub struct Packet {
    pub code: u8,
    pub params: Vec<u8>,
}

#[derive(Debug, Clone, Copy)]
pub struct ServoMonitor {
    pub id: u8,
    pub voltage_mv: u16,
    pub current_ma: u16,
    pub power_mw: u16,
    pub temp_raw: u16,
    pub status: u8,
    pub angle_deg: f32,
    pub turn: i16,
    /// `true` = fresh reading from servo; `false` = held from last known value.
    pub reliable: bool,
}

pub fn checksum(header: [u8; 2], code: u8, params: &[u8]) -> u8 {
    let mut sum = header[0] as u16 + header[1] as u16 + code as u16 + params.len() as u16;
    for byte in params {
        sum += *byte as u16;
    }
    (sum & 0xff) as u8
}

pub fn pack_request(code: u8, params: &[u8]) -> Result<Vec<u8>> {
    if params.len() > u8::MAX as usize {
        return Err(SmartServoError::Protocol(
            "packet params too large".to_string(),
        ));
    }

    let mut out = Vec::with_capacity(5 + params.len());
    out.extend_from_slice(&REQ_HEADER);
    out.push(code);
    out.push(params.len() as u8);
    out.extend_from_slice(params);
    out.push(checksum(REQ_HEADER, code, params));
    Ok(out)
}

#[derive(Debug, Default)]
pub struct ParseReport {
    pub packets: Vec<Packet>,
    pub errors: Vec<SmartServoError>,
}

pub fn parse_response_stream(data: &[u8]) -> ParseReport {
    let mut report = ParseReport::default();
    let mut i = 0;

    while i + 5 <= data.len() {
        if data[i..].starts_with(&RESP_HEADER) {
            let code = data[i + 2];
            let size = data[i + 3] as usize;
            let end = i + 2 + 1 + 1 + size + 1;
            if end > data.len() {
                break;
            }
            let params = &data[i + 4..i + 4 + size];
            let got = data[end - 1];
            let expected = checksum(RESP_HEADER, code, params);
            if got == expected {
                report.packets.push(Packet {
                    code,
                    params: params.to_vec(),
                });
            } else {
                report.errors.push(SmartServoError::ChecksumMismatch {
                    code,
                    expected,
                    got,
                });
            }
            i = end;
        } else {
            i += 1;
        }
    }

    report
}

pub fn encode_ping(id: u8) -> Result<Vec<u8>> {
    pack_request(CODE_PING, &[id])
}

pub fn encode_query_angle(id: u8, multi_turn: bool) -> Result<Vec<u8>> {
    let code = if multi_turn {
        CODE_QUERY_SERVO_ANGLE_MTURN
    } else {
        CODE_QUERY_SERVO_ANGLE
    };
    pack_request(code, &[id])
}

pub fn encode_query_monitor(id: u8) -> Result<Vec<u8>> {
    pack_request(CODE_QUERY_SERVO_MONITOR, &[id])
}

pub fn encode_set_angle(
    id: u8,
    angle_deg: f32,
    multi_turn: bool,
    interval_ms: Option<u32>,
) -> Result<Vec<u8>> {
    if !angle_deg.is_finite() {
        return Err(SmartServoError::Protocol(
            "angle_deg must be finite".to_string(),
        ));
    }
    let angle_raw = (angle_deg * 10.0).round() as i32;
    let interval_ms = interval_ms.filter(|v| *v != 0);
    match (multi_turn, interval_ms) {
        (true, Some(interval)) => {
            if interval > 4_096_000 {
                return Err(SmartServoError::Protocol(
                    "multi-turn interval_ms must be <= 4096000".to_string(),
                ));
            }
            let mut p = Vec::with_capacity(13);
            p.push(id);
            p.extend_from_slice(&angle_raw.to_le_bytes());
            p.extend_from_slice(&interval.to_le_bytes());
            p.extend_from_slice(&20_u16.to_le_bytes());
            p.extend_from_slice(&20_u16.to_le_bytes());
            p.extend_from_slice(&0_u16.to_le_bytes());
            pack_request(CODE_SET_SERVO_ANGLE_MTURN_BY_INTERVAL, &p)
        }
        (false, Some(interval)) => {
            if interval > u16::MAX as u32 {
                return Err(SmartServoError::Protocol(
                    "single-turn interval_ms must be <= 65535".to_string(),
                ));
            }
            let clamped = angle_raw.clamp(-1800, 1800) as i16;
            let mut p = Vec::with_capacity(11);
            p.push(id);
            p.extend_from_slice(&clamped.to_le_bytes());
            p.extend_from_slice(&(interval as u16).to_le_bytes());
            p.extend_from_slice(&20_u16.to_le_bytes());
            p.extend_from_slice(&20_u16.to_le_bytes());
            p.extend_from_slice(&0_u16.to_le_bytes());
            pack_request(CODE_SET_SERVO_ANGLE_BY_INTERVAL, &p)
        }
        (false, None) => {
            let clamped = angle_raw.clamp(-1800, 1800) as i16;
            // Match vendor SDK: CODE_SET_SERVO_ANGLE uses angle + interval + power.
            let mut p = Vec::with_capacity(7);
            p.push(id);
            p.extend_from_slice(&clamped.to_le_bytes());
            p.extend_from_slice(&0_u16.to_le_bytes());
            p.extend_from_slice(&0_u16.to_le_bytes());
            pack_request(CODE_SET_SERVO_ANGLE, &p)
        }
        (true, None) => {
            // Match vendor SDK CODE_SET_SERVO_ANGLE_MTURN: id + angle(i32) + interval(u32) + power(u16).
            let mut p = Vec::with_capacity(11);
            p.push(id);
            p.extend_from_slice(&angle_raw.to_le_bytes());
            p.extend_from_slice(&0_u32.to_le_bytes());
            p.extend_from_slice(&0_u16.to_le_bytes());
            pack_request(CODE_SET_SERVO_ANGLE_MTURN, &p)
        }
    }
}

pub fn decode_ping(packet: &Packet) -> Option<u8> {
    (packet.code == CODE_PING && packet.params.len() == 1).then_some(packet.params[0])
}

pub fn decode_angle(packet: &Packet, multi_turn: bool) -> Result<(u8, f32)> {
    if multi_turn {
        if packet.code != CODE_QUERY_SERVO_ANGLE_MTURN || packet.params.len() < 7 {
            return Err(SmartServoError::Protocol(
                "unexpected multi-turn angle response".to_string(),
            ));
        }
        let id = packet.params[0];
        let raw = i32::from_le_bytes(packet.params[1..5].try_into().unwrap());
        Ok((id, raw as f32 / 10.0))
    } else {
        if packet.code != CODE_QUERY_SERVO_ANGLE || packet.params.len() < 3 {
            return Err(SmartServoError::Protocol(
                "unexpected angle response".to_string(),
            ));
        }
        let id = packet.params[0];
        let raw = i16::from_le_bytes(packet.params[1..3].try_into().unwrap());
        Ok((id, raw as f32 / 10.0))
    }
}

pub fn decode_monitor(packet: &Packet) -> Result<ServoMonitor> {
    if packet.code != CODE_QUERY_SERVO_MONITOR || packet.params.len() < 14 {
        return Err(SmartServoError::Protocol(
            "unexpected monitor response".to_string(),
        ));
    }
    let p = &packet.params;
    let id = p[0];
    let voltage_mv = u16::from_le_bytes([p[1], p[2]]);
    let current_ma = u16::from_le_bytes([p[3], p[4]]);
    let power_mw = u16::from_le_bytes([p[5], p[6]]);
    let temp_raw = u16::from_le_bytes([p[7], p[8]]);
    let status = p[9];
    let angle_raw = i32::from_le_bytes([p[10], p[11], p[12], p[13]]);
    let turn = if p.len() >= 16 {
        i16::from_le_bytes([p[14], p[15]])
    } else {
        0
    };
    Ok(ServoMonitor {
        id,
        voltage_mv,
        current_ma,
        power_mw,
        temp_raw,
        status,
        angle_deg: angle_raw as f32 / 10.0,
        turn,
        reliable: true,
    })
}

/// Encode a sync-monitor request (code 25 + sub-command 22).
/// One packet queries all `ids` simultaneously; each online servo replies
/// with its own standard monitor response packet (code 22).
pub fn encode_sync_monitor(ids: &[u8]) -> Result<Vec<u8>> {
    if ids.is_empty() {
        return Err(SmartServoError::Protocol(
            "sync_monitor: ids list must not be empty".to_string(),
        ));
    }
    // Outer params: [sub_cmd=22, sub_length=1, count, id0, id1, ...]
    let mut params = Vec::with_capacity(3 + ids.len());
    params.push(CODE_QUERY_SERVO_MONITOR); // 22
    params.push(1u8); // per-servo payload length in sub-cmd
    params.push(ids.len() as u8); // servo count
    params.extend_from_slice(ids);
    pack_request(CODE_SYNC_COMMAND, &params)
}

pub fn encode_reset_multi_turn(id: u8) -> Result<Vec<u8>> {
    pack_request(CODE_RESET_MTURN, &[id])
}

pub fn encode_set_origin_point(id: u8) -> Result<Vec<u8>> {
    // FashionStar protocol requires two bytes: [servo_id, 0].
    // The original Python SDK uses struct.pack('<BB', servo_id, 0).
    // Sending only [id] causes the firmware to reject the packet silently.
    pack_request(CODE_SET_ORIGIN, &[id, 0])
}

pub fn encode_set_damping(id: u8, power: u16) -> Result<Vec<u8>> {
    let [low, high] = power.to_le_bytes();
    pack_request(CODE_SET_DAMPING, &[id, low, high])
}

pub fn encode_set_stop_mode(id: u8, mode: u8, power: u16) -> Result<Vec<u8>> {
    let mut p = Vec::with_capacity(4);
    p.push(id);
    p.push(mode);
    p.extend_from_slice(&power.to_le_bytes());
    pack_request(CODE_SET_STOP_MODE, &p)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn damping_packets_match_unloaded_damping_script() {
        assert_eq!(encode_set_damping(0, 100).unwrap(), [0x12, 0x4c, 0x09, 0x03, 0x00, 0x64, 0x00, 0xce]);
        assert_eq!(encode_set_damping(2, 100).unwrap(), [0x12, 0x4c, 0x09, 0x03, 0x02, 0x64, 0x00, 0xd0]);
        assert_eq!(encode_set_damping(6, 100).unwrap(), [0x12, 0x4c, 0x09, 0x03, 0x06, 0x64, 0x00, 0xd4]);
        assert_eq!(encode_set_damping(0, 1200).unwrap(), [0x12, 0x4c, 0x09, 0x03, 0x00, 0xb0, 0x04, 0x1e]);
        assert_eq!(encode_set_damping(253, u16::MAX).unwrap(), [0x12, 0x4c, 0x09, 0x03, 0xfd, 0xff, 0xff, 0x65]);
        assert_eq!(encode_set_damping(0, 0).unwrap(), [0x12, 0x4c, 0x09, 0x03, 0x00, 0x00, 0x00, 0x6a]);
    }

    #[test]
    fn request_checksum_matches_python_sdk_shape() {
        let pkt = encode_ping(1).unwrap();
        assert_eq!(&pkt[..4], &[0x12, 0x4c, CODE_PING, 1]);
        assert_eq!(pkt[4], 1);
        assert_eq!(pkt[5], checksum(REQ_HEADER, CODE_PING, &[1]));
    }

    #[test]
    fn rejects_non_finite_angle() {
        assert!(encode_set_angle(0, f32::NAN, false, None).is_err());
        assert!(encode_set_angle(0, f32::INFINITY, true, Some(100)).is_err());
    }

    #[test]
    fn rejects_single_turn_interval_truncation() {
        assert!(encode_set_angle(0, 10.0, false, Some(100_000)).is_err());
    }

    #[test]
    fn reports_checksum_mismatch() {
        let mut bad = vec![0x05, 0x1c, CODE_PING, 1, 1, 0];
        bad[5] = 0xaa;
        let report = parse_response_stream(&bad);
        assert!(report.packets.is_empty());
        assert_eq!(report.errors.len(), 1);
    }
}
