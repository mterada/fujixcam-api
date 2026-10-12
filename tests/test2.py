# -----------------------------------------------------
# simple test code for camera.py
#
# Copyright 2026 Masahiro Terada (@mterada.com)
# This software is released under the MIT License.
# http://opensource.org/licenses/mit-license.php
# -----------------------------------------------------

import cv2, numpy as np
import time
from dataclasses import asdict

from fujixcam import Camera
from fujixcam import ResultStatus, ResultConfig, ResultImage, ResultFiles

CAPTURED_IMAGES_FOLDER = "tests/captured_images"

# ---------------------------------------------------------------------
# custom helper for testing camera functionality
# ---------------------------------------------------------------------
def test_custom_case(x: Camera):
    """カスタム設定とカスタムシナリオを実行"""
    config_m = x.setup( program_mode="M", aperture="F2.8", shutter_speed="1/60",
                        focus_mode="MF" )
    #config_a = x.setup( program_mode="A", aperture="F2.8" )
    #config_s = x.setup( program_mode="S", shutter_speed="1/60" )
    config_p = x.setup( program_mode="P", exposure_compensation="0.0EV", iso_sensitivity="ISO 400",
                        focus_mode="AF-S" )
    print_config(config_p)
    x.focus_on( 0, 0 )
    x.reconnect()

# -----------------------------------------------------------------
# Result情報の表示用関数
# -----------------------------------------------------------------
def print_status(res: ResultStatus):
    if res.success:
        print("Camera Status:\n",
            f"\tis_ready = {res.camera_status.is_ready}\n",
            f"\tbuffer_count = {res.camera_status.buffer_count}\n",
            f"\tconditions = {res.camera_status.conditions}\n")
    else:
        print("Failed to get camera status:", res.error_message)

def print_config(res: ResultConfig):
    if res.success:
        print("current settings:")
        if not res.settings is None:
            print("\tExposure Settings: ", res.settings["exposure"] or "N/A")
            print("\tFocus Settings: ", res.settings["focus"] or "N/A")
            print("\timage Settings: ", res.settings["image"] or "N/A")
#            print("liveview Settings: ", res.settings["liveview"] or "N/A")
        if not res.options is None:
            print("current options:")
            print("\tExposure Options: ", res.options["exposure"] or "N/A")
            print("\tFocus Options: ", res.options["focus"] or "N/A")
            print("\timage Options: ", res.options["image"] or "N/A")
#            print("liveview Options: ", res.options["liveview"] or "N/A")
    else:
        print("Failed to get camera config:", res.error_message)

def print_files(res: ResultFiles, windows=False):
    if res.success:
        print(f"{len(res.image_files)} image file(s) captured:")
        for i, f in enumerate(res.image_files):
            print(f"\t{i+1}: {f}")
    else:
        print("Failed to capture image:", res.error_message)

def show_image(res: ResultImage):
    if res.success and res.image_data:
        print(f"{len(res.image_data)} bytes of image data received, Return to close window.")
        img = cv2.imdecode( np.frombuffer(res.image_data, np.uint8), cv2.IMREAD_COLOR )
        if img is None:
            print("Failed to decode image data.")
            return
        cv2.imshow("Captured Image", img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        print("Failed to show image:", res.error_message)

# -----------------------------------------------------------------
# テスト用関数
# -----------------------------------------------------------------
def test_get_status(x: Camera):
    """カメラのステータスを取得して表示するテスト"""
    print("x.get_status()")
    print_status(x.get_status())

def test_get_config(x: Camera):
    """カメラの設定を取得して表示するテスト"""
    print("x.get_config()")
    print_config(x.get_config())

def test_reconnect(x: Camera):
    """カメラの再接続をテストする"""
    print("x.reconnect()")
    res = x.reconnect()
    if res:
        print("Camera reconnected successfully.")
    else:
        print("Failed to reconnect camera.")
    print_status(x.get_status())

def test_setup(x:Camera, exposure_modes=["P", "A", "S", "M"], focus_modes=["AF-S", "AF-C", "MF"]):
    """カメラのプログラムモード・フォーカスモード毎の設定とオプションを表示する"""
    #print("x.get_status() --------------------------------------------------")
    #print_status(x.get_status())

    res = x.setup()
    if len(exposure_modes) == 0 and len(focus_modes) == 0:
        print("x.setup() --------------------------------------------------")
        print_config(res)
        return 

    # backup current exposure and focus settings
    exposure_dict = asdict(res.settings["exposure"])
    focus_dict = asdict(res.settings["focus"])

    def print_only_exposure(res: ResultConfig):
#        res.settings["focus"] = None
#        res.settings["image"] = None
#        res.options["focus"] = None
#        res.options["image"] = None
#        print_config(res)
        print(res.settings["exposure"])
        print(res.options["exposure"])

    def print_only_focus(res: ResultConfig):
#        res.settings["exposure"] = None
#        res.settings["image"] = None
#        res.options["exposure"] = None
#        res.options["image"] = None
#        print_config(res) 
        print(res.settings["focus"])
        print(res.options["focus"])

    print( "\n[exposure]")
    if "P" in exposure_modes:
        print("x.setup( program_mode='P', exposure_compensation='+1.0EV') --------------------------------------------------")
        res = x.setup(program_mode="P", exposure_compensation="+1.0EV")
        print_only_exposure(res)

    if "A" in exposure_modes:
        print("x.setup( program_mode='A', aperture='F8.0') --------------------------------------------------")
        res = x.setup(program_mode="A", aperture="F8.0")
        print_only_exposure(res)

    if "S" in exposure_modes:
        print("x.setup( program_mode='S', shutter_speed='1/60') --------------------------------------------------")
        res = x.setup(program_mode="S", shutter_speed="1/60")
        print_only_exposure(res)

    if "M" in exposure_modes:
        print("x.setup( program_mode='M', shutter_speed='1/250', aperture='F5.6', iso_sensitivity='ISO 3200' ) ----") 
        res = x.setup(program_mode="M", shutter_speed="1/250", aperture="F5.6", iso_sensitivity="ISO 3200" )
        print_only_exposure(res)

    # restore initial settings
    print("Restoring initial exposure settings...")
    exposure_keys = ["program_mode", "shutter_speed", "aperture", "iso_sensitivity", "exposure_compensation"]
    previous_exposure = {k: exposure_dict[k] for k in exposure_keys}
    x.setup(**previous_exposure)

    print("\n[focus]")
    if "AF-C" in focus_modes:
        print("x.setup( focus_mode='AF-C', af_mode='WIDETRACKING') -------------------------------------------")
        res = x.setup(focus_mode="AF-C", af_mode="WIDETRACKING")
        print_only_focus(res)

    if "AF-S" in focus_modes:
        print("x.setup( focus_mode='AF-S', af_mode='SINGLE', af_area_size='Large') ---------------------------")
        res = x.setup(focus_mode="AF-S", af_mode="SINGLE", af_area_size="Large")
        print_only_focus(res)

    if "MF" in focus_modes:
        print("x.setup( focus_mode='MF', mf_distance='inf') --------------------------------------------------")
        res = x.setup(focus_mode="MF")
        res = x.setup(focus_mode="MF", mf_distance=res.options["focus"].mf_distance[0]) # INF
        print_only_focus(res)

    # restore initial focus settings
    print("Restoring initial focus settings...")
    focus_keys = ["focus_mode", "mf_distance", "af_mode", "af_area_size"]
    previous_focus = {k: focus_dict[k] for k in focus_keys}
    x.setup(**previous_focus)

def test_revert(x:Camera):
    """カメラの設定を元に戻すテスト """
    print("x.revert() -------------------------------------------")
    res = x.revert()
    if res.success:
        print_config(res)
        print("Camera settings reverted successfully.")
    else:
        print("Failed to revert camera settings : ", res.error_message)

def test_preview(x:Camera):
    """プレビュー撮影のテスト（繰り返し）"""
    print("x.preview() -------------------------------------------")
    while True:
        if input("Press Enter to preview an image...(q to quit)") == "q":
            break
        res = x.preview()
        show_image(res)

def test_capture_single(x:Camera):
    """単写撮影のテスト（繰り返し）"""
    print("x.capture() -------------------------------------------")
    while True:
        if input("Press Enter to capture an image...(q to quit)") == "q":
            break
        res = x.capture(folder=CAPTURED_IMAGES_FOLDER)
        print_files(res)

def test_capture_multiple(x:Camera):
    """連続撮影のテスト（繰り返し）"""
    while True:
        if input("Press Enter to capture multiple images...(q to quit)") == "q":
            break

        count = int( input("Enter count number (default 5) :") or "5" )
        print(f"x.capture(count={count}) -------------------------------------------")
        res = x.capture(folder=CAPTURED_IMAGES_FOLDER, count=count )
        print_files(res)

def test_bulb_capture(x:Camera):
    """バルブ撮影のテスト（繰り返し）"""
    while True:
        if input("Press Enter to start bulb capture...(q to quit)") == "q":
            break
        exposure_time = int(input("Enter bulb capture duration in seconds (default 5): ") or "5")
        print(f"x.bulb_capture(exposure_time={exposure_time}) -------------------------------------------")
        #res = x.bulb_capture(folder=CAPTURED_IMAGES_FOLDER, exposure_time=exposure_time, callback="default")
        res = x.bulb_capture(folder=CAPTURED_IMAGES_FOLDER, exposure_time=exposure_time )
        print_files(res)

def test_focus_position(x:Camera):
    """フォーカスを指定した位置に変更する（繰り返し）"""
    print("x.get_config().options['focus'] --------------------------------------------------")
    res = x.get_config()
    print(res.options["focus"])

    if (not res.options["focus"].af_point_h) or len(res.options["focus"].af_point_h)==0:
        print("No available focus points in this focus mode, change the focus mode and try again.")
        return

    while True:
        h = int(input(" h: ") or "0")
        v = int(input(" v: ") or "0")
        res = x.focus_on(h, v)
        if res.success:
            print(f"x.focus_on({h}, {v}) successful")
        else:
            print("Failed to focus : ", res.error_message )
        if input("Press Enter to continue (q to quit)") == "q":
            break
    x.focus_on(0, 0)  # Reset focus to center position

def test_monitor(x:Camera):
    pass
#    print("x.get_monitor_options() ")
#    res = x.get_monitor_options()
#    print(res.options["monitor"])
#
#    while True:
#        print("x.get_monitor_image()")
#        # input h, v, zoom
#        h = int(input("h: ") or "0")
#        v = int(input("v: ") or "0")
#        zoom = input("zoom: ") or "x1.0"
#        af = input("perform AF? (y/n): ") 
#        if not af in ["y", "n"]:
#            break
#        res = x.get_monitor_image(h, v, zoom, perform_af=(af=='y'))
#        # display image data of bytearray jpeg
#        if res.failed:
#            print("Failed to get monitor image : ", res.error_message )
#            continue
#        img = cv2.imdecode( np.frombuffer(res.image_data, np.uint8), cv2.IMREAD_COLOR )
#        cv2.imshow("Live View", img)
#        cv2.waitKey(1)
#    cv2.destroyAllWindows()

def test_liveview(x:Camera):
    """ライブビューのテスト（繰り返し）"""
    print("x.get_config().options['focus'] --------------------------------------------------")
    res = x.get_config()
    h_options = res.options["focus"].af_point_h
    v_options = res.options["focus"].af_point_v
    print("Available af_point h: ", h_options)
    print("Available af_point v: ", v_options)

    print("x.get_liveview_config() --------------------------------------------------")
    res = x.get_liveview_config()
    print(res.options["liveview"])

    def _liveview_session():
        size = input("size: ") or "L"
        zoom = input("zoom: ") or "x1.0"
        h_center, v_center = len(h_options)//2, len(v_options)//2  # default to center focus area
        h_index, v_index = h_center, v_center

        print("x.start_liveview() --------------------------------------------------")
        res = x.start_liveview(size=size, zoom=zoom)
        if res.failed:
            print("Failed to start live view : ", res.error_message )
            return

        print("While live view session, press 'q' to quit, 'h','j','k','l' to move focus area")
        af = False
        while True:
            res = x.get_liveview_image()
            if res.success and res.image_data:
                img = cv2.imdecode( np.frombuffer(res.image_data, np.uint8), cv2.IMREAD_COLOR )
                if img is None:
                    print("Failed to decode image data.")
                    continue
                cv2.imshow("Live View", img)
            else:
                print("Failed to get liveview image : ", res.error_message )
                return

            time.sleep(0.05)

            def set_focus_area(h_index, v_index, af):
                h, v = h_options[h_index], v_options[v_index]
                print(f"set af_point:({h},{v}), zoom:{zoom}")
                #if zoom != "x1.0":
                #    x.stop_liveview()
                res = x.focus_on(h, v, af_on=af)
                if not res.success:
                    print("Failed to move af_point.", res.error_message )
                #if zoom != "x1.0":
                #    x.start_liveview(size=size, zoom=zoom)

            key = cv2.waitKey(1)
            if key == ord('q'):
                break
            elif key == ord('h'):
                h_index = max(0, h_index - 1)
            elif key == ord('l'):
                h_index = min(len(h_options)-1, h_index + 1)
            elif key == ord('j'):
                v_index = max(0, v_index - 1) 
            elif key == ord('k'):
                v_index = min(len(v_options)-1, v_index + 1) 
            elif key == ord('m'):
                h_index, v_index = h_center, v_center
            elif key == ord('f'):
                af = True
            else:
                continue

            # move focus area based on key input
            set_focus_area(h_index, v_index, af)
            af = False
    
        cv2.destroyAllWindows()
        x.stop_liveview()
        print("x.stop_liveview() --------------------------------------------------")
        x.revert()
    
    while True:
        _liveview_session()
        if input("Press Enter to start new liveview session (or 'q' to quit): ").strip().lower() == 'q':
            break

def test_batch_cases(x:Camera):
    """テストケースをまとめて連続実行する（一部を除く）"""
    #print("Starting batch test cases...")
    # Here you would add the actual batch test logic
    batch_list = [
        test_get_status,
        test_get_config,
        test_reconnect,
        test_setup,
        test_revert,
        test_preview,
        test_capture_single,
        test_capture_multiple,
        test_bulb_capture,
        test_focus_position,
        test_liveview
    ]

    print(f"\nBatch Test Cases ({len(batch_list)}): The following test will be executed sequentially.")
    for i, test_case in enumerate(batch_list):
        print(f"[{i+1}] {test_case.__name__} : {test_case.__doc__}")

    diag = (input("Do you want to confirm befor the next case ? ([y]/n): ").strip().lower() != 'n')

    for i, test_case in enumerate(batch_list):
        print( "-"*60)
        print(f"[{i+1}] {test_case.__name__} : {test_case.__doc__}")
        if diag:
            todo = input("Press Enter to proceed (or 's' to skip, 'q' to quit)...").strip().lower()
            if todo == 's':
                print(f"Skipping {test_case.__name__}...")
                continue
            elif todo == 'q':
                print("Quitting batch test...")
                break
        test_case(x)
    print( "-"*60)
    print( "Batch test completed." )
#
# Main Menu to run the test cases
#
def test_camera():
    """Test the camera by running various test functions."""
    # define the list of test functions to run
    test_cases_menu = [
        test_custom_case,
        test_get_status,
        test_get_config,
        test_reconnect,
        test_setup,
        test_revert,
        test_preview,
        test_capture_single,
        test_capture_multiple,
        test_bulb_capture,
        test_focus_position,
        test_liveview,
        test_batch_cases,
    ]

    # create a Camera instance
    #cam = Camera( log_level="info" )
    cam = Camera()

    while True:
        # display the menu of test cases
        print(f"\nAvailable Test Cases ({len(test_cases_menu)}):")
        for i, test_case in enumerate(test_cases_menu):
            print(f"{i+1}. {test_case.__name__} : {test_case.__doc__}")

        choice = input("Enter the number of the test case to run (q to exit): ").strip().lower()
        if choice == 'q':
            cam.close()
            break
        elif choice == 'Q':
            cam.close(shutdown=True)
            break
        elif choice.isdigit():
            i = int(choice) - 1
            if 0 <=i < len(test_cases_menu):
                test_case = test_cases_menu[i]
                print(f"\n[{i+1}] {test_case.__name__} : {test_case.__doc__}")
                test_case(cam)
        else:
            print("Invalid number. Please try again.")

    print( "Exiting camera test menu.\n")
    return 0

# =================================
# Main entry point for the script
# =================================
if __name__ == "__main__":
    # テスト撮影の保存用フォルダが存在するか確認
    import os
    if not os.path.exists( CAPTURED_IMAGES_FOLDER ):
        print(f"テスト撮影の保存用フォルダが見つかりません {CAPTURED_IMAGES_FOLDER}")
        yn = input("続行しますか？ (y/[n]):").strip().lower() or "n"
        if yn != "y":
            exit(1)

    input("Press Enter to start the camera class tests...")
    print("Camera class tests started at ", time.strftime("%Y-%m-%d %H:%M:%S\n"))

    test_camera()

    print("Camera class tests finished at ", time.strftime("%Y-%m-%d %H:%M:%S"))
    input("Press Enter to exit...")
    exit(0)