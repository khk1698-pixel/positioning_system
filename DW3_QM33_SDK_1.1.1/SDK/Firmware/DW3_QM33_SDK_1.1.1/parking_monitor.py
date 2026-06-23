import serial
import serial.tools.list_ports
import re
import csv
import os
from datetime import datetime

# ───────────────────────────────────────────────
# CSV 저장 경로 설정
# ───────────────────────────────────────────────
def get_save_path():
    print("\n=== 주차 모니터링 시스템 ===")
    print("CSV 저장 경로를 입력하세요.")
    print("(예: C:\\Users\\user\\Desktop  또는 그냥 Enter 누르면 현재 폴더에 저장)")
    path = input("저장 경로: ").strip()
    if not path:
        path = os.getcwd()
    if not os.path.exists(path):
        print(f"경로가 존재하지 않습니다. 현재 폴더에 저장합니다: {os.getcwd()}")
        path = os.getcwd()
    filename = f"parking_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return os.path.join(path, filename)


# ───────────────────────────────────────────────
# Initiator 높이 설정 (앙각 보정용)
# ───────────────────────────────────────────────
def get_init_height():
    print("\nInitiator 설치 높이를 입력하세요 (앙각 보정에 사용됩니다).")
    print("(예: 45  → Initiator가 바닥에서 45cm 높이에 설치된 경우)")
    print("(Enter만 누르면 기본값 100cm 사용)")
    while True:
        val = input("높이 (cm): ").strip()
        if not val:
            print("기본값 100cm 사용합니다.")
            return 100.0
        try:
            h = float(val)
            if 0.0 <= h < 200.0:
                return h
            else:
                print("0 이상 200 미만의 값을 입력해주세요.")
        except ValueError:
            print("숫자를 입력해주세요.")


# ───────────────────────────────────────────────
# COM 포트 자동 감지
# ───────────────────────────────────────────────
def find_com_port():
    print("\nCOM 포트를 자동으로 탐색 중...")
    ports = list(serial.tools.list_ports.comports())

    if not ports:
        print("연결된 COM 포트가 없습니다. 보드를 연결해주세요.")
        return None

    keywords = ["JLink", "J-Link", "DWM", "nRF", "USB Serial", "Segger"]
    matched = []
    for p in ports:
        desc = (p.description or "") + (p.manufacturer or "")
        if any(kw.lower() in desc.lower() for kw in keywords):
            matched.append(p)

    if len(matched) == 1:
        print(f"보드 자동 감지됨: {matched[0].device} - {matched[0].description}")
        return matched[0].device

    print("\n연결된 COM 포트 목록:")
    all_ports = matched if matched else ports
    for i, p in enumerate(all_ports):
        print(f"  [{i+1}] {p.device} - {p.description}")

    while True:
        try:
            choice = int(input("사용할 포트 번호를 선택하세요: ")) - 1
            if 0 <= choice < len(all_ports):
                return all_ports[choice].device
            else:
                print("올바른 번호를 입력해주세요.")
        except ValueError:
            print("숫자를 입력해주세요.")


# ───────────────────────────────────────────────
# 데이터 파싱
# ───────────────────────────────────────────────
def parse_value(line, key):
    """line에서 key= 뒤의 정수값 파싱"""
    try:
        return int(line.split(f"{key}=")[1].split(",")[0].split("]")[0].strip())
    except:
        return None


def parse_block(block_lines):
    r1, r2, r3 = None, None, None
    f1, f2, f3 = None, None, None
    x, y, z_est, pos = None, None, None, None
    elev_dh = None          # ELEV_CORR: 앙각 보정 높이차
    r1h, r2h, r3h = None, None, None  # 보정된 수평거리

    for line in block_lines:
        # 거리값 파싱
        if "mac_address=0x0001" in line and "distance[cm]=" in line:
            r1 = parse_value(line, "distance[cm]")
            f1 = parse_value(line, "filtered[cm]")

        if "mac_address=0x0002" in line and "distance[cm]=" in line:
            r2 = parse_value(line, "distance[cm]")
            f2 = parse_value(line, "filtered[cm]")

        if "mac_address=0x0003" in line and "distance[cm]=" in line:
            r3 = parse_value(line, "distance[cm]")
            f3 = parse_value(line, "filtered[cm]")

        # ELEV_CORR 줄 파싱
        # 예: ELEV_CORR: init_h=45.0 dh=155.0 r1:180->97 r2:190->105 r3:200->120
        if line.startswith("ELEV_CORR:"):
            mdh = re.search(r'dh=([\d.]+)', line)
            mr1h = re.search(r'r1:[\d.]+\->([\d.]+)', line)
            mr2h = re.search(r'r2:[\d.]+\->([\d.]+)', line)
            mr3h = re.search(r'r3:[\d.]+\->([\d.]+)', line)
            if mdh:
                try: elev_dh = float(mdh.group(1))
                except: pass
            if mr1h:
                try: r1h = float(mr1h.group(1))
                except: pass
            if mr2h:
                try: r2h = float(mr2h.group(1))
                except: pass
            if mr3h:
                try: r3h = float(mr3h.group(1))
                except: pass

        # PARKING= 줄 파싱
        # 예: PARKING=OCCUPIED, POS=IN_POSITION(x=74.6,y=181.2,z_est=45.2)
        # 예: PARKING=OUT_OF_RANGE(x=74.6,y=181.2,z_est=45.2)
        if "PARKING=" in line or line.startswith("POS="):
            pos = line.strip()

            mx  = re.search(r'x=([-\d.]+)', line)
            my  = re.search(r'y=([-\d.]+)', line)
            mz  = re.search(r'z_est=([-\d.]+)', line)  # z_est 우선
            if not mz:
                mz = re.search(r'z=([-\d.]+)', line)   # 구버전 z 호환

            if mx:
                try: x = float(mx.group(1))
                except: pass
            if my:
                try: y = float(my.group(1))
                except: pass
            if mz:
                try: z_est = float(mz.group(1))
                except: pass

    return r1, r2, r3, f1, f2, f3, x, y, z_est, pos, elev_dh, r1h, r2h, r3h


# ───────────────────────────────────────────────
# 화면 출력
# ───────────────────────────────────────────────
DISPLAY_ROWS = 20
display_buffer = []
start_time = None


def fmt(val, width=7, decimal=None):
    if val is None:
        return " " * (width - 1) + "-"
    if decimal is not None:
        return f"{val:>{width}.{decimal}f}"
    return f"{val:>{width}}"


def format_row(ts, r1, r2, r3, f1, f2, f3, x, y, z_est, pos, elev_dh=None, r1h=None, r2h=None, r3h=None):
    if pos is None:
        pos_str = "대기 중..."
    elif "IN_POSITION" in pos:
        pos_str = f"✅ IN_POSITION"
    elif "OUT_OF_RANGE" in pos:
        pos_str = f"⚠️  OUT_OF_RANGE"
    elif "TOO_CLOSE" in pos:
        pos_str = f"🔴 TOO_CLOSE"
    elif "EMPTY" in pos:
        pos_str = f"⬜ EMPTY"
    elif "ERROR" in pos:
        pos_str = f"❗ ERROR"
    else:
        pos_str = pos

    def dist_str(r, f, rh=None):
        if r is None:
            return "        -"
        parts = f"{r}"
        if f is not None and f != r:
            parts += f"→{f}"
        if rh is not None:
            parts += f"[{int(rh)}]"   # 앙각 보정된 수평거리
        return parts

    d1 = dist_str(r1, f1, r1h)
    d2 = dist_str(r2, f2, r2h)
    d3 = dist_str(r3, f3, r3h)

    x_s    = fmt(x, 6, 1)
    y_s    = fmt(y, 6, 1)
    z_s    = fmt(z_est, 6, 1)
    dh_s   = fmt(elev_dh, 6, 1)

    return f"  {ts:<10} {d1:>12} {d2:>12} {d3:>12} {x_s} {y_s} {z_s} {dh_s}  {pos_str}"


def redraw(csv_path, init_height=None):
    os.system('cls')
    print("=" * 115)
    print(f"  주차 모니터링  |  시작: {start_time}  |  종료: Ctrl+C")
    print(f"  저장 경로: {csv_path}")
    h_str = f"{init_height:.1f}cm" if init_height is not None else "-"
    print(f"  Initiator 높이: {h_str}  |  ※ 거리값: 원시→필터[앙각보정] 순 표시")
    print("=" * 115)
    print(f"  {'시각':<10} {'R1(cm)':>12} {'R2(cm)':>12} {'R3(cm)':>12} {'x':>6} {'y':>6} {'z_est':>6} {'Δh':>6}  판정")
    print("-" * 115)
    for row in display_buffer:
        print(row)
    print("-" * 115)
    print(f"  최근 {len(display_buffer)}개 표시 중 (전체 데이터는 CSV에 저장됨)")


# ───────────────────────────────────────────────
# 메인
# ───────────────────────────────────────────────
def write_csv_row(writer, csv_file, r1, r2, r3, f1, f2, f3,
                  x, y, z_est, pos, elev_dh, r1h, r2h, r3h):
    writer.writerow([
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        r1   if r1   is not None else '',
        r2   if r2   is not None else '',
        r3   if r3   is not None else '',
        f1   if f1   is not None else '',
        f2   if f2   is not None else '',
        f3   if f3   is not None else '',
        f"{r1h:.0f}" if r1h is not None else '',
        f"{r2h:.0f}" if r2h is not None else '',
        f"{r3h:.0f}" if r3h is not None else '',
        f"{x:.1f}"    if x    is not None else '',
        f"{y:.1f}"    if y    is not None else '',
        f"{z_est:.1f}" if z_est is not None else '',
        f"{elev_dh:.1f}" if elev_dh is not None else '',
        pos  if pos  is not None else ''
    ])
    csv_file.flush()


def main():
    csv_path = get_save_path()
    init_height = get_init_height()

    com_port = find_com_port()
    if not com_port:
        input("보드를 연결 후 Enter를 눌러 다시 시도하세요.")
        com_port = find_com_port()
        if not com_port:
            print("포트를 찾을 수 없어 종료합니다.")
            return

    try:
        ser = serial.Serial(com_port, 115200, timeout=1)
        print(f"\n✅ 연결 성공: {com_port}")
    except Exception as e:
        print(f"연결 실패: {e}")
        return

    # SETHEIGHT 명령 전송
    cmd = f"SETHEIGHT {init_height:.1f}\r\n"
    ser.write(cmd.encode('utf-8'))
    print(f"📡 SETHEIGHT {init_height:.1f} 전송 완료")

    csv_file = open(csv_path, 'w', newline='', encoding='utf-8-sig')
    writer = csv.writer(csv_file)
    writer.writerow([
        'timestamp',
        'r1_raw', 'r2_raw', 'r3_raw',
        'r1_filtered', 'r2_filtered', 'r3_filtered',
        'r1_corrected', 'r2_corrected', 'r3_corrected',  # 앙각 보정된 수평거리
        'x', 'y', 'z_est',                               # z_est = 추정 높이
        'delta_h',                                        # 앙각 보정에 사용된 높이차
        'pos'
    ])
    print(f"📄 CSV 저장 경로: {csv_path}")

    global start_time
    start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    redraw(csv_path, init_height)

    buffer = []
    in_block = False

    try:
        while True:
            try:
                raw = ser.readline()
                if not raw:
                    continue
                line = raw.decode('utf-8', errors='ignore').strip()
                if not line:
                    continue

                # 블록 시작 감지
                if "SESSION_INFO_NTF:" in line:
                    # 이전 블록이 PARKING 줄 없이 끊긴 경우 처리
                    if in_block and len(buffer) > 1:
                        ts = datetime.now().strftime('%H:%M:%S')
                        r1, r2, r3, f1, f2, f3, x, y, z_est, pos, elev_dh, r1h, r2h, r3h = parse_block(buffer)
                        row_str = format_row(ts, r1, r2, r3, f1, f2, f3,
                                             x, y, z_est, pos, elev_dh, r1h, r2h, r3h)
                        display_buffer.append(row_str)
                        if len(display_buffer) > DISPLAY_ROWS:
                            display_buffer.pop(0)
                        redraw(csv_path, init_height)
                        write_csv_row(writer, csv_file, r1, r2, r3, f1, f2, f3,
                                      x, y, z_est, pos, elev_dh, r1h, r2h, r3h)

                    in_block = True
                    buffer = [line]
                    continue

                if in_block:
                    buffer.append(line)

                    # PARKING= 줄이 오면 블록 완료
                    if "PARKING=" in line or line.startswith("POS="):
                        ts = datetime.now().strftime('%H:%M:%S')
                        r1, r2, r3, f1, f2, f3, x, y, z_est, pos, elev_dh, r1h, r2h, r3h = parse_block(buffer)

                        row_str = format_row(ts, r1, r2, r3, f1, f2, f3,
                                             x, y, z_est, pos, elev_dh, r1h, r2h, r3h)
                        display_buffer.append(row_str)
                        if len(display_buffer) > DISPLAY_ROWS:
                            display_buffer.pop(0)
                        redraw(csv_path, init_height)
                        write_csv_row(writer, csv_file, r1, r2, r3, f1, f2, f3,
                                      x, y, z_est, pos, elev_dh, r1h, r2h, r3h)
                        buffer = []
                        in_block = False

            except UnicodeDecodeError:
                continue

    except KeyboardInterrupt:
        print("\n\n종료합니다.")
        print(f"📄 CSV 저장 완료: {csv_path}")
    finally:
        ser.close()
        csv_file.close()


if __name__ == "__main__":
    main()
