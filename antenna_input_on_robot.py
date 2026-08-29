"""Read the antennas as a physical input, running on the robot itself.

アンテナのモーターだけトルクを切り、手で動かした角度を読み続ける。頭と胴体は
トルクを保つため姿勢が崩れない。終了時にアンテナのトルクを必ず戻す。
"""

import argparse
import math
import time

from reachy_mini import ReachyMini


ANTENNA_MOTORS = ["left_antenna", "right_antenna"]


def bar(value_deg: float, span: float = 90.0, width: int = 21) -> str:
    """Render one antenna angle as a text gauge centred on zero."""
    half = width // 2
    clamped = max(-span, min(span, value_deg))
    offset = round(clamped / span * half)
    cells = ["-"] * width
    cells[half] = "|"
    cells[half + offset] = "#"
    return "".join(cells)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seconds",
        type=int,
        default=20,
        help="読み取りを続ける秒数",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.2,
        help="読み取り間隔（秒）",
    )
    parser.add_argument(
        "--keep-torque",
        action="store_true",
        help="アンテナのトルクを切らない（動かせないが、指令値との比較に使える）",
    )
    args = parser.parse_args()

    print("ローカルの Reachy Mini daemon に接続しています...", flush=True)
    with ReachyMini(
        connection_mode="localhost_only",
        media_backend="no_media",
    ) as mini:
        print("接続しました。", flush=True)
        mini.enable_motors()

        if not args.keep_torque:
            # アンテナだけトルクを切る。頭と胴体は保持されるので姿勢が崩れない。
            print(f"アンテナのトルクを切ります: {', '.join(ANTENNA_MOTORS)}", flush=True)
            mini.disable_motors(ids=ANTENNA_MOTORS)

        print(
            f"{args.seconds}秒間、アンテナの角度を読み続けます。"
            "指でアンテナを動かしてください。",
            flush=True,
        )
        print("  左アンテナ            右アンテナ", flush=True)

        readings: list[tuple[float, float]] = []
        started = time.monotonic()
        try:
            while time.monotonic() - started < args.seconds:
                left, right = mini.get_present_antenna_joint_positions()
                readings.append((left, right))
                left_deg = math.degrees(left)
                right_deg = math.degrees(right)
                print(
                    f"[{time.monotonic() - started:5.1f}s] "
                    f"{bar(left_deg)} {left_deg:+7.1f}°   "
                    f"{bar(right_deg)} {right_deg:+7.1f}°",
                    flush=True,
                )
                time.sleep(args.interval)
        finally:
            if not args.keep_torque:
                print("アンテナのトルクを戻します。", flush=True)
                mini.enable_motors(ids=ANTENNA_MOTORS)
                # トルク復帰後の現在値を目標にして、勝手に跳ねないようにする。
                left, right = mini.get_present_antenna_joint_positions()
                mini.goto_target(antennas=[left, right], duration=0.5)

        if readings:
            lefts = [math.degrees(v[0]) for v in readings]
            rights = [math.degrees(v[1]) for v in readings]
            print(
                f"\n左アンテナ: 最小 {min(lefts):+.1f}° / 最大 {max(lefts):+.1f}° / "
                f"可動幅 {max(lefts) - min(lefts):.1f}°",
                flush=True,
            )
            print(
                f"右アンテナ: 最小 {min(rights):+.1f}° / 最大 {max(rights):+.1f}° / "
                f"可動幅 {max(rights) - min(rights):.1f}°",
                flush=True,
            )
            print(f"サンプル数: {len(readings)}", flush=True)

    print("完了しました。", flush=True)


if __name__ == "__main__":
    main()
