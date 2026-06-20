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
    x, y, z, pos = None, None, None, None

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

        # POS 파싱 — 정규식으로 안정적으로 추출
        # 예: PARKING=OCCUPIED, POS=IN_POSITION(x=74.6,y=181.2,z=139.1)
        # 예: PARKING=OUT_OF_RANGE(x=74.6,y=181.2,z=139.1)
        if "PARKING=" in line or line.startswith("POS="):
            pos = line.strip()

            # x, y, z 정규식 파싱
            mx = re.search(r'x=([-\d.]+)', line)
            my = re.search(r'y=([-\d.]+)', line)
            mz = re.search(r'z=([-\d.]+)', line)
            mh = re.search(r'h=([-\d.]+)', line)

            if mx:
                try: x = float(mx.group(1))
                except: pass
            if my:
                try: y = float(my.group(1))
                except: pass
            if mz:
                try: z = float(mz.group(1))
                except: pass
            elif mh:
                try: z = float(mh.group(1))
                except: pass

    return r1, r2, r3, f1, f2, f3, x, y, z, pos


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


def format_row(ts, r1, r2, r3, f1, f2, f3, x, y, z, pos):
    if pos is None:
        pos_str = "대기 중..."
    elif "IN_POSITION" in pos:
        pos_str = f"✅ {pos}"
    elif "OUT_OF_RANGE" in pos:
        pos_str = f"⚠️  {pos}"
    elif "TOO_CLOSE" in pos:
        pos_str = f"🔴 {pos}"
    elif "EMPTY" in pos:
        pos_str = f"⬜ {pos}"
    elif "ERROR" in pos:
        pos_str = f"❗ {pos}"
    else:
        pos_str = pos

    def dist_str(r, f):
        if r is None:
            return "      -"
        if f is not None and f != r:
            return f"{r}→{f}"
        return f"{r:>7}"

    d1 = dist_str(r1, f1)
    d2 = dist_str(r2, f2)
    d3 = dist_str(r3, f3)

    x_s = fmt(x, 6, 1)
    y_s = fmt(y, 6, 1)
    z_s = fmt(z, 6, 1)

    return f"  {ts:<10} {d1:>9} {d2:>9} {d3:>9} {x_s} {y_s} {z_s}  {pos_str}"


def redraw(csv_path):
    os.system('cls')
    print("=" * 100)
    print(f"  주차 모니터링  |  시작: {start_time}  |  종료: Ctrl+C")
    print(f"  저장 경로: {csv_path}")
    print("  ※ 거리값: 원시→필터 (필터 미적용 시 원시값만 표시)")
    print("=" * 100)
    print(f"  {'시각':<10} {'R1(cm)':>9} {'R2(cm)':>9} {'R3(cm)':>9} {'x':>6} {'y':>6} {'z/h':>6}  판정")
    print("-" * 100)
    for row in display_buffer:
        print(row)
    print("-" * 100)
    print(f"  최근 {len(display_buffer)}개 표시 중 (전체 데이터는 CSV에 저장됨)")


# ───────────────────────────────────────────────
# 메인
# ───────────────────────────────────────────────
def main():
    csv_path = get_save_path()

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

    csv_file = open(csv_path, 'w', newline='', encoding='utf-8-sig')
    writer = csv.writer(csv_file)
    writer.writerow([
        'timestamp',
        'r1_raw', 'r2_raw', 'r3_raw',
        'r1_filtered', 'r2_filtered', 'r3_filtered',
        'x', 'y', 'z_or_h', 'pos'
    ])
    print(f"📄 CSV 저장 경로: {csv_path}")

    global start_time
    start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    redraw(csv_path)

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
                    # 이전 블록이 PARKING/POS 없이 끝난 경우 처리
                    if in_block and len(buffer) > 1:
                        ts = datetime.now().strftime('%H:%M:%S')
                        r1, r2, r3, f1, f2, f3, x, y, z, pos = parse_block(buffer)
                        row_str = format_row(ts, r1, r2, r3, f1, f2, f3, x, y, z, pos)
                        display_buffer.append(row_str)
                        if len(display_buffer) > DISPLAY_ROWS:
                            display_buffer.pop(0)
                        redraw(csv_path)
                        writer.writerow([
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            r1 if r1 is not None else '',
                            r2 if r2 is not None else '',
                            r3 if r3 is not None else '',
                            f1 if f1 is not None else '',
                            f2 if f2 is not None else '',
                            f3 if f3 is not None else '',
                            f"{x:.1f}" if x is not None else '',
                            f"{y:.1f}" if y is not None else '',
                            f"{z:.1f}" if z is not None else '',
                            pos if pos is not None else ''
                        ])
                        csv_file.flush()

                    in_block = True
                    buffer = [line]
                    continue

                if in_block:
                    buffer.append(line)

                    # PARKING= 줄이 오면 블록 완료
                    if "PARKING=" in line or line.startswith("POS="):
                        ts = datetime.now().strftime('%H:%M:%S')
                        r1, r2, r3, f1, f2, f3, x, y, z, pos = parse_block(buffer)

                        row_str = format_row(ts, r1, r2, r3, f1, f2, f3, x, y, z, pos)
                        display_buffer.append(row_str)
                        if len(display_buffer) > DISPLAY_ROWS:
                            display_buffer.pop(0)
                        redraw(csv_path)

                        writer.writerow([
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            r1 if r1 is not None else '',
                            r2 if r2 is not None else '',
                            r3 if r3 is not None else '',
                            f1 if f1 is not None else '',
                            f2 if f2 is not None else '',
                            f3 if f3 is not None else '',
                            f"{x:.1f}" if x is not None else '',
                            f"{y:.1f}" if y is not None else '',
                            f"{z:.1f}" if z is not None else '',
                            pos if pos is not None else ''
                        ])
                        csv_file.flush()
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
