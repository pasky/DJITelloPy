import time
import logging
from djitellopy import Tello, TelloException

# Constants
TELLO_IP = "192.168.6.38"
MOVE_SPEED = 10
VERTICAL_MOVEMENT = 20

def initialize_tello() -> Tello:
    """Initialize and configure the Tello drone."""
    tello = Tello(TELLO_IP)
    tello.connect()
    tello.enable_mission_pads()
    tello.set_mission_pad_detection_direction(2)
    tello.takeoff()
    return tello

def print_telemetry(tello: Tello, pad: int):
    """Print telemetry data for the Tello drone."""
    print(f"\nBattery: {tello.get_battery()}% Time: {tello.get_flight_time()} "
          f"TOFd: {tello.get_distance_tof()}cm Height: {tello.get_height()}cm "
          f"Temp: {tello.get_temperature()} Bar: {tello.get_barometer()}")
    print(f"Pitch: {tello.get_pitch()} Roll: {tello.get_roll()} Yaw: {tello.get_yaw()} "
          f"Speed: {tello.get_speed_x()}/{tello.get_speed_y()}/{tello.get_speed_z()} "
          f"Acc: {tello.get_acceleration_x()}/{tello.get_acceleration_y()}/{tello.get_acceleration_z()}")
    print(f"Mission pad: ID {pad} Distance "
          f"{tello.get_mission_pad_distance_x()}cm/{tello.get_mission_pad_distance_y()}cm/{tello.get_mission_pad_distance_z()}cm")

def main_loop(tello: Tello):
    """Execute the main mission pad detection and movement loop."""
    while (pad := tello.get_mission_pad_id()) != 1:
        print_telemetry(tello, pad)

        if pad == -1:
            tello.move_up(VERTICAL_MOVEMENT)
            time.sleep(0.5)
            tello.move_down(VERTICAL_MOVEMENT)
            time.sleep(0.5)
        elif tello.get_mission_pad_distance_x() > 20 or tello.get_mission_pad_distance_y() > 20:
            tello.go_xyz_speed_mid(0, 0, tello.get_height(), MOVE_SPEED, pad)
            time.sleep(0.5)
        else:
            break

def move_between_pads(tello: Tello, from_pad: int, x: int, y: int, to_pad: int):
    """Move the Tello drone towards a specific mission pad and align to the given x, y coordinates."""
    print_telemetry(tello, tello.get_mission_pad_id())

    def try_find_pad():
        n_tries = 0

        while (pad := tello.get_mission_pad_id()) == -1:
            if tello.get_height() <= 100:
                print(f"moving up {VERTICAL_MOVEMENT}")
                tello.move_up(VERTICAL_MOVEMENT)
                print_telemetry(tello, pad)
                continue

            if n_tries < 5:
                print(f"circling {n_tries}")
                n_tries += 1

                tello.move_forward(20)
                print_telemetry(tello, pad)
                if pad := tello.get_mission_pad_id() != -1:
                    break

                time.sleep(0.5)
                tello.rotate_clockwise(90)
                print_telemetry(tello, pad)
                continue

            else:
                raise TelloException("can't find pad")

        print(f"Found pad {pad}")
        return pad

    n_tries = 0
    while n_tries < 5:
        print(f"MOVE FROM: {from_pad} X: {x} Y: {y} TO: {to_pad} ({n_tries})")
        n_tries += 1

        try:
            if from_pad == -1:
                tello.go_xyz_speed_mid(x, y, tello.get_height(), MOVE_SPEED, to_pad)
            else:
                tello.go_xyz_speed_yaw_mid(x, y, tello.get_height(), MOVE_SPEED, 0, from_pad, to_pad)
        except TelloException as e:
            print(f"Pad {from_pad} not in sight ({e})")
            pad = try_find_pad()
            time.sleep(0.5)

            if pad == to_pad:
                center_on_pad(tello, pad)
                break

def center_on_pad(tello: Tello, pad: int):
    """Center the drone on a specific mission pad."""
    print(f"CENTER ON TARGET PAD {pad}")
    print_telemetry(tello, pad)
    tello.go_xyz_speed_mid(0, 0, tello.get_height(), MOVE_SPEED, pad)
    time.sleep(0.5)

def cleanup(tello: Tello):
    """Perform cleanup operations and land the drone."""
    tello.disable_mission_pads()
    tello.land()
    tello.end()

if __name__ == "__main__":
    Tello.LOGGER.setLevel(logging.INFO)
    tello = initialize_tello()
    try:
        # main_loop(tello)
        move_between_pads(tello, from_pad=-1, x=0, y=0, to_pad=9)  # align on starting position
        move_between_pads(tello, from_pad=9, x=50, y=0, to_pad=8)  # move towards pad 7
        center_on_pad(tello, 8)
    finally:
        cleanup(tello)
