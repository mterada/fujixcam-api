# -----------------------------------------------------
# test/sample code for camera_api.py CameraAPI class
#
# Copyright 2026 Masahiro Terada (@mterada.com)
# This software is released under the MIT License.
# http://opensource.org/licenses/mit-license.php
# -----------------------------------------------------
import time
import cv2, numpy as np

from fujixcam import CameraAPI
from fujixcam.camera_api_dictionary import *

CAPTURED_IMAGES_FOLDER = "tests/captured_images"    

# ---------------------------------------------------------------------
# custom helper for testing camera functionality
# ---------------------------------------------------------------------
def test_custom_case(cam:CameraAPI):
    """カスタム設定とカスタムシナリオを実行"""
    default_settings(cam)
    show_exposure_settings(cam)

#   応用テスト ライブビュー表示しながら、フォーカス変更、AF実行、撮影保存を行う
#    test_liveview_and_capture(cam)
    pass

# ---------------------------------------------------------------------
# basic test for camera status
# ---------------------------------------------------------------------
def test_get_status(cam:CameraAPI):
    """カメラの接続を確認し内部状態を取得するテスト"""
    if not cam.is_connected():
        print( "Camera is not connected. Please connect to the camera first." )
        return

    res = cam.get_status()
    if not res.success:
        print( f"Failed to get camera status. '{res.error_message}'" )
        return
    # res.data contains the detailed camera status information
    print( f"Camera Status: is_connected" )
    if res.data is not None:
        for item in res.data.items():
            print( f"   {item[0]}   : {item[1]}" )

# ---------------------------------------------------------------------
# test reconnection loop
# ---------------------------------------------------------------------
def test_reconnection(cam:CameraAPI):
    """カメラの接続・切断の反復を確認するテスト"""
    print( "Camera reconnection loop test. Connect and disconnect the camera repeatedly to check for stability." )
    while True:
        if input("Press Enter to check the camera status...[q to quit] ").strip().lower() == 'q':
            break   
        print( f"- Camera is connected: {cam.is_connected()}" )
        print( f"- Camera status: {cam.get_status()}" )
        input("Press Enter to disconnect the camera...")
        print( f"Camera disconnected. response = {cam.disconnect()}" )
        input("Press Enter to check the camera status...")
        print( f"- Camera is connected: {cam.is_connected()}" )
        print( f"- Camera status: {cam.get_status()}" )
        input("Press Enter to reconnect the camera...")
        print( f"Camera reconnected. response = {cam.connect(index=0)}" )

# ---------------------------------------------------------------------
# basic test for exposure settings
# (program mode, aperture value, shutter speed, exposure conpensation, ISO sensitivity)
# ---------------------------------------------------------------------
def test_program_mode(cam:CameraAPI):
    """プログラムモードの選択肢と設定を確認するテスト"""
    res = cam.get_program_mode_options()
    if not res.success:
        print( f"Failed to get_program_mode_options. '{res.error_message}'" )
        return
    print( f"Program Mode Options : {res.options}\n => {[ program_mode_value_to_string(s) for s in res.options]}" )
    program_mode_options = res.options

    res = cam.get_program_mode()
    if not res.success:
        print( f'Failed to get program mode. "{res.error_message}"' )
        return
    print( f'Current Mode = {res.value} : "{program_mode_value_to_string(res.value)}"' )
    initial_value = res.value

    for mode in program_mode_options:
        res1 = cam.set_program_mode(mode)
        res2 = cam.get_program_mode()
        if not res1.success or not res2.success or res2.value != mode:
            print( f'Failed to set/get program mode to {mode} ({program_mode_value_to_string(mode)}). "{res1.error_message or res2.error_message}"' )
        else:
            print( f'Set/Get Program Mode to {mode} : "{program_mode_value_to_string(mode)}" => OK ' )
    # restore original mode
    print( f"Restoring original program mode: {program_mode_value_to_string(initial_value)}\n" )
    cam.set_program_mode(initial_value)
    return True

def test_aperture_setting(cam: CameraAPI):
    """プログラムモードAで絞り値の設定と取得を確認するテスト"""
    # A or M 以外のモードでは絞り値の設定ができないので、先にプログラムモードをAにしておく
    old_settings = _setup_exposure( cam, program_mode = "A" )

    res = cam.get_aperture_value_options()
    if not res.success:
        print( f"Failed to get aperture value options. '{res.error_message}'" )
        _restore_exposure( cam, old_settings )
        return
    print( f"Aperture Value Options : {res.options}\n => {[ aperture_value_to_string(s) for s in res.options]}" )
    aperture_value_options = res.options

    res = cam.get_aperture_value()
    if not res.success:
        print( f'Failed to get aperture value. "{res.error_message}"' )
        return
    print( f'Current Aperture Value = {res.value} : "{aperture_value_to_string(res.value)}"' )
    initial_value = res.value

    for aperture_value in aperture_value_options:
        res1 = cam.set_aperture_value(aperture_value)
        res2 = cam.get_aperture_value()
        if not res1.success or not res2.success or res2.value != aperture_value:
            print( f'Failed to set/get aperture value to {aperture_value} ({aperture_value_to_string(aperture_value)}). "{res1.error_message or res2.error_message}"' )
        else:
            print( f'Set/Get Aperture Value to {aperture_value} : "{aperture_value_to_string(aperture_value)}" => OK ' )    

    # restore original aperture value
    print( f"Restoring original aperture value: {aperture_value_to_string(initial_value)}\n" )
    cam.set_aperture_value(initial_value)

    _restore_exposure( cam, old_settings )

def test_shutter_speed_setting(cam: CameraAPI):
    """プログラムモードSでシャッタースピードの設定と取得を確認するテスト"""
    # S or M 以外のモードではシャッタースピードの設定ができないので、先にプログラムモードをSにしておく
    old_settings = _setup_exposure( cam, program_mode = "S" )

    res = cam.get_shutter_speed_options()
    if not res.success:
        print( f"Failed to get shutter speed options. '{res.error_message}'" )
        _restore_exposure( cam, old_settings )
        return
    print( f"Shutter Speed Options : {res.options}\n => {[ shutter_speed_value_to_string(s) for s in res.options]}" )
    shutter_speed_options = res.options

    res = cam.get_shutter_speed()
    if not res.success:
        print( f'Failed to get shutter speed. "{res.error_message}"' )
        return
    print( f'Current Shutter Speed = {res.value} : "{shutter_speed_value_to_string(res.value)}"' )
    initial_value = res.value

    for shutter_speed in shutter_speed_options:
        res1 = cam.set_shutter_speed(shutter_speed)
        res2 = cam.get_shutter_speed()
        if not res1.success or not res2.success or res2.value != shutter_speed:
            print( f'Failed to set/get shutter speed to {shutter_speed} ({shutter_speed_value_to_string(shutter_speed)}). "{res1.error_message or res2.error_message}"' )
        else:
            print( f'Set/Get Shutter Speed to {shutter_speed} : "{shutter_speed_value_to_string(shutter_speed)}" => OK ' )
    # restore original shutter speed
    print( f"Restoring original shutter speed: {shutter_speed_value_to_string(initial_value)}\n" )
    cam.set_shutter_speed(initial_value)

    _restore_exposure( cam, old_settings )

def test_exposure_compensation_setting(cam: CameraAPI):
    """プログラムモードPで露出補正の設定と取得を確認するテスト"""
    # P or S or A 以外のモードでは露出補正の設定ができないので、先にプログラムモードをPにしておく
    old_settings = _setup_exposure( cam, program_mode = "P" )

    res = cam.get_exposure_compensation_options()
    if not res.success:
        print( f"Failed to get exposure compensation options. '{res.error_message}'" )
        _restore_exposure( cam, old_settings )
        return
    print( f"Exposure Compensation Options : {res.options}\n => {[ exposure_compensation_value_to_string(s) for s in res.options]}" )
    exposure_compensation_options = res.options

    res = cam.get_exposure_compensation()
    if not res.success:
        print( f'Failed to get exposure compensation. "{res.error_message}"' )
        return
    print( f'Current Exposure Compensation = {res.value} : "{exposure_compensation_value_to_string(res.value)}"' )
    initial_value = res.value

    for ev in exposure_compensation_options:
        res1 = cam.set_exposure_compensation(ev)
        res2 = cam.get_exposure_compensation()
        if not res1.success or not res2.success or res2.value != ev:
            print( f'Failed to set/get exposure compensation to {ev} ({exposure_compensation_value_to_string(ev)}). "{res1.error_message or res2.error_message}"' )
        else:
            print( f'Set/Get Exposure Compensation to {ev} : "{exposure_compensation_value_to_string(ev)}" => OK ' )
    # restore original exposure compensation
    print( f"Restoring original exposure compensation: {exposure_compensation_value_to_string(initial_value)}\n" )
    cam.set_exposure_compensation(initial_value)

    _restore_exposure( cam, old_settings )

def test_iso_sensitivity_setting(cam: CameraAPI):
    """プログラムモードMでISO感度の設定と取得を確認するテスト"""
    # ISO感度の設定はプログラムモードで共通なので、プログラムモードMを使用する
    old_settings = _setup_exposure( cam, program_mode = "M" )

    res = cam.get_iso_sensitivity_options()
    if not res.success:
        print( f"Failed to get ISO sensitivity options. '{res.error_message}'" )
        _restore_exposure( cam, old_settings )
        return
    print( f"ISO Sensitivity Options : {res.options}\n => {[ iso_sensitivity_value_to_string(s) for s in res.options]}" )
    iso_sensitivity_options = res.options

    res = cam.get_iso_sensitivity()
    if not res.success:
        print( f'Failed to get ISO sensitivity. "{res.error_message}"' )
        return
    print( f'Current ISO Sensitivity = {res.value} : "{iso_sensitivity_value_to_string(res.value)}"' )
    initial_value = res.value

    for iso in iso_sensitivity_options:
        res1 = cam.set_iso_sensitivity(iso)
        res2 = cam.get_iso_sensitivity()
        if not res1.success or not res2.success or res2.value != iso:
            print( f'Failed to set/get ISO sensitivity to {iso} ({iso_sensitivity_value_to_string(iso)}). "{res1.error_message or res2.error_message}"' )
        else:
            print( f'Set/Get ISO Sensitivity to {iso} : "{iso_sensitivity_value_to_string(iso)}" => OK ' )
    # restore original ISO sensitivity
    print( f"Restoring original ISO sensitivity: {iso_sensitivity_value_to_string(initial_value)}\n" )
    cam.set_iso_sensitivity(initial_value)

    _restore_exposure( cam, old_settings )

def show_exposure_settings(cam: CameraAPI):
    """露出設定に関するパラメータの選択肢と現在値をすべて表示する"""
    res = cam.get_program_mode_options()
    if res.success:
        print( f"Program Mode Options : {res.options}\n => {[ program_mode_value_to_string(s) for s in res.options]}" )
    res = cam.get_program_mode()
    if res.success:
        print( f'Current Program Mode = {res.value} : "{program_mode_value_to_string(res.value)}"' )
    
    res = cam.get_exposure_compensation_options()
    if res.success:
        print( f"Exposure Compensation Options : {res.options}\n => {[ exposure_compensation_value_to_string(s) for s in res.options]}" )
    res = cam.get_exposure_compensation()
    if res.success:
        print( f'Current Exposure Compensation = {res.value} : "{exposure_compensation_value_to_string(res.value)}"' )
    
    res = cam.get_shutter_speed_options()
    if res.success:
        print( f"Shutter Speed Options : {res.options}\n => {[ shutter_speed_value_to_string(s) for s in res.options]}" )
    res = cam.get_shutter_speed()
    if res.success:
        print( f'Current Shutter Speed = {res.value} : "{shutter_speed_value_to_string(res.value)}"' )
    
    res = cam.get_aperture_value_options()
    if res.success:
        print( f"Aperture Value Options : {res.options}\n => {[ aperture_value_to_string(s) for s in res.options]}" )
    res = cam.get_aperture_value()
    if res.success:
        print( f'Current Aperture Value = {res.value} : "{aperture_value_to_string(res.value)}"' )
    
    res = cam.get_iso_sensitivity_options()
    if res.success:
        print( f"ISO Sensitivity Options : {res.options}\n => {[ iso_sensitivity_value_to_string(s) for s in res.options]}" )
    res = cam.get_iso_sensitivity()
    if res.success:
        print( f'Current ISO Sensitivity = {res.value} : "{iso_sensitivity_value_to_string(res.value)}"' )

# Helper function to update multiple camera settings at once,
#   parameters can be None to skip, or string values from dictionary
def _setup_exposure(cam, exposure_compensation=None, shutter_speed=None, aperture_value=None, iso_sensitivity=None, program_mode=None):
    old_settings = {}
    if program_mode is not None:
        old_settings["program_mode"] = cam.get_program_mode().value
        res = cam.set_program_mode( string_to_program_mode_value(program_mode) )
        if res.success:
            print( f"Set Program Mode to '{program_mode}'" )
        else:
            print( res.error_message )

    if exposure_compensation is not None:
        old_settings["exposure_compensation"] = cam.get_exposure_compensation().value
        res = cam.set_exposure_compensation( string_to_exposure_compensation_value(exposure_compensation) )
        if res.success:
            print( f"Set Exposure Compensation to '{exposure_compensation}'" )
        else:
            print( res.error_message )

    if shutter_speed is not None:
        old_settings["shutter_speed"] = cam.get_shutter_speed().value
        res = cam.set_shutter_speed( string_to_shutter_speed_value(shutter_speed) )
        if res.success:
            print( f"Set Shutter Speed to '{shutter_speed}'" ) 
        else:
            print( res.error_message )

    if aperture_value is not None:
        old_settings["aperture_value"] = cam.get_aperture_value().value
        res = cam.set_aperture_value( string_to_aperture_value(aperture_value) )
        if res.success:
            print( f"Set Aperture Value to '{aperture_value}'" )
        else:
            print( res.error_message )

    if iso_sensitivity is not None:
        old_settings["iso_sensitivity"] = cam.get_iso_sensitivity().value
        res = cam.set_iso_sensitivity( string_to_iso_sensitivity_value(iso_sensitivity) )
        if res.success:
            print( f"Set ISO Sensitivity to '{iso_sensitivity}'" )
        else:
            print( res.error_message )

    return old_settings

def _restore_exposure(cam, old_settings):
    # restore camera settings from old_settings in reverse order of setup_exposure
    if "iso_sensitivity" in old_settings:
        cam.set_iso_sensitivity( old_settings["iso_sensitivity"] )
    if "aperture_value" in old_settings:
        cam.set_aperture_value( old_settings["aperture_value"] )
    if "shutter_speed" in old_settings:
        cam.set_shutter_speed( old_settings["shutter_speed"] )
    if "exposure_compensation" in old_settings:
        cam.set_exposure_compensation( old_settings["exposure_compensation"] )
    if "program_mode" in old_settings:
        print( f"Restoring Program Mode:'{program_mode_value_to_string(old_settings['program_mode'])}'" )
        cam.set_program_mode( old_settings["program_mode"] )

# ---------------------------------------------------------------------
# Shooting status query and control 
# (get_status, af_lock, ae_lock, awb_lock, reset_status)
# ---------------------------------------------------------------------
def test_release_status(cam:CameraAPI):
    """カメラの撮影状態を取得するテスト"""
    # AE lock は自動露出, AF lock は自動フォーカス　であること
    old_settings = _setup_exposure( cam, program_mode = "P", exposure_compensation="0.0EV", iso_sensitivity="ISO 400" )
    #old_focusing = setup_focus(cam, focus_mode="AF-S", focus_pos="CENTER", focus_distance="INF")

    print( f"Camera Status: {cam.get_status().data}" )

    input( "Press Enter to continue... AF Lock test" )
    print( f"- AF Lock: {cam.af_lock()}" )
    print( f"-> Camera Status: {cam.get_status().data}" )
    
    input( "Press Enter to continue... AE Lock test" )
    print( f"- AE Lock: {cam.ae_lock()}" )
    print( f"-> Camera Status: {cam.get_status().data}" )

    input( "Press Enter to continue... AWB Lock test" )
    print( f"- AWB Lock: {cam.awb_lock()}" )
    print( f"-> Camera Status: {cam.get_status().data}" )

    input( "Press Enter to continue... reset status" )
    print( f"- Reset Status: {cam.reset_status()}" )
    print( f"-> Camera Status: {cam.get_status().data}" )

    _restore_exposure( cam, old_settings )

def test_lenszoom_capability(cam:CameraAPI):
    """カメラのレンズズーム能力を取得するテスト"""
    print( f"Lens name: {cam._lens_name}")
    res = cam.get_lens_zoom_capability()
    if not res.success:
        print( f"Failed to get lens zoom capability. '{res.error_message}'" )
        return
    print( f"Zoom capablity: {res.data["ability"]}" )
    zoom_dict = dict(zip( res.data["options"], [ str(i/100)+"mm" for i in res.data["actual_length"] ] ))
    print( f"Zoom positions: {zoom_dict}" )
    res = cam.get_lens_zoom()
    if not res.success:
        print( f"Failed to get current zoom position. '{res.error_message}'" )
        return
    print( f"current focal length: {zoom_dict[res.value]}" )

# ---------------------------------------------------------------------
# basic test for image capture
# (full image capture, preview image capture, bulb capture, burst capture)
# ---------------------------------------------------------------------
def test_capture_image(cam:CameraAPI):
    """各プログラムモードで1枚ずつテスト撮影する"""
    folder = CAPTURED_IMAGES_FOLDER

    print( "Exposure Settings : P, 0.0EV, ISO 1600" )
    old_settings = _setup_exposure( cam, program_mode = "P", exposure_compensation="0.0EV", iso_sensitivity="ISO 1600" )
    res = cam.capture_image( folder=folder )
    print( f"Captured Image: {res.data}" if res.success else f"Failed to capture image. '{res.error_message}'" )
    _restore_exposure( cam, old_settings )

    print( "Exposure Settings : M, 15s, F11, ISO 100" )
    old_settings = _setup_exposure( cam, program_mode = "M", shutter_speed="15s", aperture_value="F11", iso_sensitivity="ISO 100" )
    res = cam.capture_image( folder=folder, long_exposure=True )
    print( f"Captured Image: {res.data}" if res.success else f"Failed to capture image. '{res.error_message}'" )
    _restore_exposure( cam, old_settings )
    
    print( "Exposure Settings : S, 1/1000, ISO 6400" )
    old_settings = _setup_exposure( cam, program_mode = "S", shutter_speed="1/1000", iso_sensitivity="ISO 6400" )
    res = cam.capture_image( folder=folder )
    print( f"Captured Image: {res.data}" if res.success else f"Failed to capture image. '{res.error_message}'" )
    _restore_exposure( cam, old_settings )

    print( "Exposure Settings : A, F5.6, ISO 3200" )
    old_settings = _setup_exposure( cam, program_mode = "A", aperture_value="F5.6", iso_sensitivity="ISO 3200" )
    res = cam.capture_image( folder=folder )
    print( f"Captured Image: {res.data}" if res.success else f"Failed to capture image. '{res.error_message}'" )
    _restore_exposure( cam, old_settings )

def test_preview_image(cam:CameraAPI):
    """シャッタースピード1/8000秒の設定でプレビュー画像を取得するテスト"""
    old_settings = _setup_exposure( cam, program_mode = "M",
                            shutter_speed = "1/8000",   # highspeed capture test
                            aperture_value = "F4.0",
                            iso_sensitivity = "ISO 12800" )
    if cam.get_shutter_speed().value != string_to_shutter_speed_value("1/8000"):
        print( "Failed to set shutter speed to 1/8000 sec. Check if the camera is set to electronic shutter mode." )
        _restore_exposure( cam, old_settings )
        return

    if _show_image_buffer(cam, "Preview Image", cam.capture_preview()):
        input( f"press ENTER to close image window." ) 
        cv2.destroyAllWindows()

    # reset to program mode
    _restore_exposure( cam, old_settings )

def test_aflock_and_preview(cam:CameraAPI):
    """FocusモードとAF動作を組み合わせた撮影テスト"""
    # focus mode options
    old_settings = _setup_exposure( cam, program_mode = "P", iso_sensitivity="ISO 800" ) 
    old_focus = _setup_focus( cam, focus_mode="AF-S", focus_pos=(0,0) )

    print( "[1] Focus Mode AF-S -> Instant AF & AF Lock -> capture_preview" )   
    _setup_focus( cam, focus_mode="AF-S", focus_pos=(0,0) )
    if cam.perform_af().success:
        print( "-> Instant AF successful." )
        if cam.af_lock().success:
            print( "-> AF Lock successful." )
            if _show_image_buffer(cam, "AF-S AF&Lock", cam.capture_preview() ):
                print( "-> Preview Image captured and display windows." )
            cam.af_lock(False)
        else:
            print( "-> AF Lock failed." )

    print( "[2] Focus Mode MF -> Instant AF -> capture_preview" )   
    _setup_focus( cam, focus_mode="MF", focus_pos=(0,0) )
    if cam.perform_af().success:
        print( "-> Instant AF successful." )
        if _show_image_buffer(cam, "MF Instant AF", cam.capture_preview() ):
            print( "-> Preview Image captured and display windows." )
    else:
        print( "-> Instant AF failed." )

    print( "[3] Focus Mode AF-C -> Continuous AF (3 sec.) -> capture_preview" )
    _setup_focus( cam, focus_mode="AF-C", focus_pos=(0,0) )
    if cam.perform_af(True).success:  # start
        print( "-> Continuous AF Started..." )
        time.sleep(3)
        if _show_image_buffer(cam, "Continuous AF", cam.capture_preview() ):
            print( "-> Preview Image captured and display windows." )
        # cam.perform_af(False)  # continuous AF will stop automatically by shooting
        print( "-> Continuous AF Stopped automatically." )
    else:
        print( "-> Continuous AF failed to start." )
    
    print( "[4] Focus Mode AF-C -> Continuous AF (3 sec.) -> AF Lock -> capture_preview" )
    if cam.perform_af(True).success:  # start
        print( "Continuous AF Started..." )
        time.sleep(3)
        if cam.af_lock():
            print( "-> AF Lock successful." )
            if _show_image_buffer(cam, "Continuous AF&Lock", cam.capture_preview() ):
                print( "-> Preview Image captured and display windows." )
            cam.af_lock(False)
        else:
            print( " -> AF Lock failed." )
            cam.perform_af(False)  # stop
    else:
        print( "Continuous AF failed to start." )

    _restore_focus( cam, old_focus )    
    _restore_exposure( cam, old_settings )

    input( "Press ENTER to close image windows..." )
    cv2.destroyAllWindows()

def _show_image_buffer(cam, title, res) -> bool:
    if not res.success:
        print(f"Failed to get {title} image, {res.error_message}" )
        return False
    res_buf = res.data["buffer"]
    if res_buf is None:
        print(f"{title} image buffer empty.")
        return False
    img = cv2.imdecode( np.frombuffer(res_buf, np.uint8), cv2.IMREAD_COLOR )
    if img is None:
        print(f"{title} image decoding failed.")
        return False
    cv2.imshow(title, img)
    cv2.waitKey(1)
    return True

def test_bulb_capture(cam:CameraAPI):
    """BULBモードでの長時間撮影が可能であることのテスト"""
    sec = 10     # capture time in seconds
    folder = CAPTURED_IMAGES_FOLDER
    old_settings = _setup_exposure( cam, program_mode = "M", shutter_speed="BULB", aperture_value="F13", iso_sensitivity="ISO 80" )
    old_focus    = _setup_focus( cam, focus_mode="MF", focus_distance="INF" )
#    old_focus    = _setup_focus( cam, focus_mode="AF-S", focus_afmode="ZONE" )

    res = cam.bulb_on()
    if not res.success:
        print( f"Failed to start bulb capture. '{res.error_message}'" )
    else: 
        print(f"Bulb capture started for {sec} seconds. Press Ctrl+C to abort.")
        for i in range(sec):
            print( ".", end="", flush=True )
            time.sleep(1)  # bulb撮影中
        print("[stop]")
        res = cam.bulb_off( folder=folder )
        #res = cam.bulb_off( abort=True )  # これもOK
        if not res.success:
            print( f"Failed to stop bulb capture. '{res.error_message}'" )
        else:
            print( f"Bulb capture completed : {res.data}" )

    _restore_focus( cam, old_focus )
    _restore_exposure( cam, old_settings )

def test_burst_capture(cam:CameraAPI):
    """連写撮影が可能であることのテスト"""
    old_settings = _setup_exposure( cam, program_mode = "S", shutter_speed="1/8000", iso_sensitivity="ISO 12800" )

    burst_count = 5
    folder = CAPTURED_IMAGES_FOLDER
    print(f"Capturing {burst_count} successive images ...")
    res = cam.capture_multi_images( count=burst_count, folder=folder )
    if not res.success:
        print( f"Failed to capture multi images. '{res.error_message}'" )
    else:
        images = res.data[ "objects" ]
        print(f"Captured {len(images)} images:")
        for i, imagefile in enumerate(images):
            print(f"image[{i}] = {imagefile}")  # RAW+JPEG, RAWのみ, JPEGのみ　撮影設定によってリストが変わることを確認する
    # reset to program mode
    _restore_exposure( cam, old_settings )

def test_auto_bracketing(cam:CameraAPI):
    """オートブラケット撮影を模擬するテスト"""
    old_settings = _setup_exposure( cam, program_mode = "P", exposure_compensation="0.0EV", iso_sensitivity="ISO 800" )
    ev_options = ["-2.0EV", "-1.0EV", "0.0EV", "+1.0EV", "+2.0EV"]

    folder = CAPTURED_IMAGES_FOLDER
    for ev_value in ev_options:
        print(f"Setting Exposure Compensation to {ev_value} and capturing image...")
        res = cam.set_exposure_compensation( string_to_exposure_compensation_value(ev_value) )
        if not res.success:
            print(f"Failed to set exposure compensation to {ev_value}. '{res.error_message}'")
            continue
        res = cam.capture_image( folder=folder )
        if not res.success:
            print(f"Failed to capture image at {ev_value}. '{res.error_message}'")
            continue
        print("Captured Image:", res.data)

    # reset to program mode
    _restore_exposure( cam, old_settings )

# ---------------------------------------------------------------------
# basic test for liveview image
# (start/stop, livevew modes, liveview image capture)
# ---------------------------------------------------------------------

def test_liveview(cam:CameraAPI):
    """ライブビューの開始と停止、ライブビュー画像の取得と表示のテスト"""
    old_settings = _setup_exposure( cam, program_mode = "P", exposure_compensation="0.0EV", iso_sensitivity="ISO 1600" )

    res1 = cam.get_liveview_quality_options()
    res2 = cam.get_liveview_size_options()
    if not res1.success or not res2.success:
        print( f"Failed to get liveview mode options. '{res1.error_message or res2.error_message}'" )
        _restore_exposure( cam, old_settings )
        return

    quality_options = res1.options
    size_options = res2.options
    print( f"LiveView quality: {quality_options} => {[liveview_quality_value_to_string(i) for i in quality_options]}" )
    print( f"LiveView size: {size_options} => {[liveview_size_value_to_string(i) for i in size_options]}" )

    for size in size_options:
        label = liveview_size_value_to_string(size)
        print( f"Testing LiveView Size {label} (50 frames)" )
        cam.set_liveview_size(size)
        cam.start_liveview()
        for i in range(50):
            if not _show_image_buffer(cam, f"LiveView Size {label}", cam.get_liveview_image()):
                break
        cam.stop_liveview()
    cam.set_liveview_size(size_options[0])

    input( "press ENTER to close image windows..." )
    cv2.destroyAllWindows()
    
    res = cam.get_finder_crop_options()
    if not res.success:
        print( f"Failed to get finder crop options. '{res.error_message}'" )
        return
    zoom_options = res.options
    print( f"Finder Crop Options: {zoom_options} => {[finder_crop_value_to_string(z) for z in zoom_options]}" )

    for zoom in zoom_options:
        label = finder_crop_value_to_string(zoom)
        print( f"Testing LiveView Zoom {label} (50 frames)" )
        cam.set_finder_crop( zoom )
        cam.start_liveview()
        for i in range(50):
            if not _show_image_buffer(cam, f"LiveView zoom {label}", cam.get_liveview_image()):
                break
        cam.stop_liveview()
    cam.set_finder_crop( zoom_options[0] )
    _restore_exposure( cam, old_settings )

    input( "press ENTER to close image windows..." )
    cv2.destroyAllWindows()
 
# ---------------------------------------------------------------------
# basic test for focus settings and focus control
# (focus settings, autofocus, manual focus)
# ---------------------------------------------------------------------
def test_focus_mode(cam:CameraAPI):
    """フォーカスモードの選択肢と設定を確認するテスト """
    res = cam.get_focus_mode_options()
    if not res.success:
        print( f"Failed to get focus mode options. '{res.error_message}'" )
        return 
    print( f"Focus Mode Options : {res.options} => {[ focus_mode_value_to_string(s) for s in res.options]}" )
    focus_mode_options = res.options

    res = cam.get_focus_mode()
    if not res.success:
        print( f'Failed to get focus mode. "{res.error_message}"' )
        return
    initial_value = res.value
    print( f'Current Focus Mode = {initial_value} : "{focus_mode_value_to_string(initial_value)}"' )

    for mode in focus_mode_options:
        res1 = cam.set_focus_mode(mode)
        res2 = cam.get_focus_mode()
        if not res1.success or not res2.success or res2.value != mode:
            print( f'Failed to set/get focus mode to {mode} ({focus_mode_value_to_string(mode)}). "{res1.error_message or res2.error_message}"' )
        else:
            print( f'Set/Get Focus Mode to {mode} : "{focus_mode_value_to_string(mode)}" => OK ' )

    # restore original mode
    print( f"Restoring original focus mode: {focus_mode_value_to_string(initial_value)}\n" )
    cam.set_focus_mode(initial_value)

def test_focus_adjust(cam:CameraAPI):
    """マニュアルフォーカス時のフォーカス位置の調整が可能であることのテスト"""
    initial_mode = cam.get_focus_mode().value

    cam.set_focus_mode( string_to_focus_mode_value("MF") )
    res = cam.get_focus_distance_range()
    if not res.success:
        print( f"Failed to get focus distance range. '{res.error_message}'" )
        return
    print( f"Focus Distance Range: {res.data}" )
    inf = res.data["inf"]
    mod = res.data["mod"]
    dof = res.data["dof"]
    if inf == 0 or mod == 0 or dof == 0:
        print( "Focus distance range is not available. Please check the camera connection and settings." )
        return

    res = cam.get_focus_distance()
    if not res.success:
        print( f'Failed to get focus distance. "{res.error_message}"' )
        return
    print( f'Current Focus distance = {res.value}')
    initial_value = res.value

    for distance in range(inf, mod, dof):
        res1 = cam.set_focus_distance(distance)
        res2 = cam.get_focus_distance()
        if not res1.success or not res2.success or res2.value != distance:
            print( f'Failed to set/get focus distance to {distance}. "{res1.error_message or res2.error_message}"' )
        else:
            print( f'Set/Get Focus distance to {distance} => OK ' )

    # restore original focus adjust
    print( f"Restoring original focus adjust: {initial_value}\n" )
    cam.set_focus_distance(initial_value)
    cam.set_focus_mode(initial_mode)

def test_autofocus(cam:CameraAPI):
    """AF設定条件を変えてもAFが実行できることのテスト"""
    old_settings = _setup_exposure( cam, program_mode = "P", exposure_compensation="0.0EV", iso_sensitivity="ISO AUTO (1)" )

    print( "Testing Autofocus in MANUAL foucs mode...")
    old_focus = _setup_focus( cam, focus_mode="MF", focus_pos=(0,0), focus_distance="INF" ) 
    while input("<Enter> to AF, 'q' to quit: ")!="q":
        print( f"perform_af Result: {cam.perform_af()} ")
    _restore_focus( cam, old_focus )
    
    print( "Testing Autofocus in AF-S mode...")
    old_focus = _setup_focus( cam, focus_mode="AF-S", focus_pos=(0,0) )
    while input("<Enter> to AF, 'q' to quit: ")!="q":
        print( f"perform_af Result: {cam.perform_af()} ")

    print( "Testing Autofocus in AF-C mode...")
    _setup_focus( cam, focus_mode="AF-C", focus_pos=(0,0) )
    sw = False
    while input("<Enter> to AF toggle, 'q' to quit: ")!="q":
        sw = not sw
        print( f"perform_af Result: {cam.perform_af(sw)} ")
    if sw:
        cam.perform_af( False )  # stop AF-C

    _restore_focus( cam, old_focus )
    _restore_exposure( cam, old_settings )

def test_focus_area(cam:CameraAPI):
    """フォーカスする画面内の位置とサイズを変更するテスト（かつ代表点でAFを実行）"""
    # (サイズを大きくすると上下左右の移動範囲が狭くなるため、エラーになる組み合わせがある)
    #old_focus = _setup_focus( cam, focus_mode="AF-S", focus_pos=(0,0) )
    old_focus = _setup_focus( cam, focus_mode="AF-S", focus_pos=(0,0), focus_afmode="SINGLE" )

    res = cam.get_focus_area_options( cap_inspection=True )  # cap_inspection=False で機種依存の制限を無視して既定のフォーカスエリアを取得する
    if not res.success:
        print( f"Failed to get focus area options. '{res.error_message}'" )
        return
    area_h_options = res.data["h"]
    area_v_options = res.data["v"]
    area_size_options = res.data["size"]
    area_points = res.data["points"]
    print( f"Focus Area Points: {area_points}" )
    print( f"Focus Area Options h: {area_h_options}, v: {area_v_options}, size: {area_size_options}" )
    if len(area_h_options) <= 1 and len(area_v_options) <= 1:
        print( "Focus area has no options in this focus mode. Skipping detailed tests." )
        return

    for size in area_size_options:
        print( f"Testing Focus Area Size: {size} ({focus_size_value_to_string(size)})" )
        for v in area_v_options:
            print( f"Testing Focus Area Position v:{v}, h:", end="", flush=True )
            for h in area_h_options:
                print( f"{h} ", end="", flush=True )
                res = cam.set_focus_area( h, v, size )
                if res.success:
                    res = cam.get_focus_area()
                    if res.success and res.data["h"] == h and res.data["v"] == v and res.data["size"] == size:
                        #print( f"Set Focus Area to h={h}, v={v}, size={size} successfully." )
                        continue
                print( f"err! ", end="", flush=True )
                if h == area_h_options[0]:
                    print( f"'{res.error_message}' -> skip" )
                    break
            print()
    
    print( f"Testing Focus Area Edge Cases AF(9 points check)" )
    # 9 points check
    v_half = area_v_options[-1]//2
    h_half = area_h_options[-1]//2
    for v in [-v_half, 0, v_half]:
        for h in [-h_half, 0, h_half]:
            res = cam.set_focus_area( h, v )
            if not res.success:
                print( f"Failed to set focus area to ({h},{v}). '{res.error_message}'" )
                continue
            res = cam.perform_af()
            print( f"Autofucus at ({h},{v}) : {'OK.' if res.success else 'Missed.'}" )

    # restore previous focus settings
    _restore_focus( cam, old_focus )

# HELPER Functions:
#  focus setup and restore
def _setup_focus(cam, focus_mode=None, focus_pos=None, focus_size=None, focus_distance=None, focus_afmode=None):
    old_settings = {}
    if focus_mode is not None:
        old_settings["focus_mode"] = cam.get_focus_mode().value
        res = cam.set_focus_mode( string_to_focus_mode_value(focus_mode) )
        if res.success:
            print( f"Set Focus Mode to '{focus_mode}'" )
        else:
            print( f"Failed to set Focus Mode to '{focus_mode}' {res.error_message}" )

    if focus_afmode is not None:
        old_settings["focus_afmode"] = cam.get_focus_afmode().value
        res = cam.set_focus_afmode( string_to_focus_afmode_value(focus_afmode) )
        if res.success:
            print( f"Set Focus AF Mode to '{focus_afmode}'" )
        else:
            print( f"Failed to set Focus AF Mode to '{focus_afmode}' {res.error_message}" )

    if focus_pos is not None:
        data = cam.get_focus_area().data
        old_settings["focus_pos"] = (data["h"], data["v"]) if "h" in data and "v" in data else None
        h, v = focus_pos
        res = cam.set_focus_area( h, v  )
        if res.success:
            print( f"Set Focus Area pos to '{focus_pos}'" )
        else:
            print( f"Failed to set Focus Area pos to '{focus_pos}' {res.error_message}" )
    
    if focus_size is not None:
        data = cam.get_focus_area().data
        old_settings["focus_size"] = data["size"] if "size" in data else None
        res = cam.set_focus_area( size=focus_size )
        if res.success:
            print( f"Set Focus Area size to '{focus_size}'" )
        else:
            print( f"Failed to set Focus Area size to '{focus_size}' {res.error_message}" )

    if focus_distance is not None:
        if focus_distance == "INF":
            res = cam.get_focus_distance_range()
            print( "Focus distance set to INF", res )
            if res.success:
                focus_distance = res.data["inf"]
            else:
                print( f"Failed to get focus distance range. '{res.error_message}'" )
                return old_settings
        old_settings["focus_distance"] = cam.get_focus_distance().value
        res = cam.set_focus_distance( focus_distance )
        if res.success and cam.get_focus_distance().value == focus_distance:
            print( f"Set Focus Distance to '{focus_distance}'" )
        else:
            print( f"Failed to set Focus Distance to '{focus_distance}' {res.error_message}" )

    return old_settings

def _restore_focus(cam, old_settings):
    # restore camera settings from old_settings in reverse order of setup_focus
    if "focus_distance" in old_settings and old_settings["focus_distance"] is not None:
        cam.set_focus_distance( old_settings["focus_distance"] )
    if "focus_size" in old_settings and old_settings["focus_size"] is not None:
        cam.set_focus_area( size=old_settings["focus_size"] )
    if "focus_pos" in old_settings and old_settings["focus_pos"] is not None:
        h, v  = old_settings["focus_pos"]
        cam.set_focus_area( h, v )
    if "focus_afmode" in old_settings and old_settings["focus_afmode"] is not None:
        cam.set_focus_afmode( old_settings["focus_afmode"] )
    if "focus_mode" in old_settings:
        print( f"Restoring focus mode: {focus_mode_value_to_string(old_settings['focus_mode'])}" )
        cam.set_focus_mode( old_settings["focus_mode"] )

def test_shoot_from_camera(cam:CameraAPI):
    """カメラ本体からの撮影操作で、PC側に画像が転送されることを確認するテスト"""
    res = cam.shoot_from_camera()
    if not res.success:
        print( f"Failed to set to camera priority mode. '{res.error_message}'" )
        return
    print( "Please operate the camera to capture an image. The captured image will be transferred to the PC." )
    print( "(The test will timeout after 10 seconds if no more image is captured.)" )
    seq_number = 0
    while True:
        res = cam.acquire_images( folder=CAPTURED_IMAGES_FOLDER, max_wait_seconds=10 )
        if not res.success:
            print( f"Failed to acquire images from camera. '{res.error_message}'" )
            return
        else:
            images = res.data[ "objects" ]
            print(f"Acquired {len(images)} images from camera:")
            for imagefile in images:
                print(f"image[{seq_number}] = {imagefile}")
                seq_number += 1
        yn = input( "Press Enter to continue acquiring images, or 'q' to quit: " )
        if yn.lower() == 'q':
            break
    cam.shoot_from_camera(False)  # reset to PC priority mode
    cam.reset_status()  # reset camera status to normal
    print( "No more images acquired from camera. Test completed." )

# ---------------------------------------------------------------------
# combined test for liveview and image capture
# ---------------------------------------------------------------------
def test_liveview_and_capture(cam:CameraAPI):
    """ライブビュー表示しながら、撮影条件を変更し、フォーカスを変更し、撮影保存を行う"""

    AUTO_PAUSE_LIVEVIEW = True   # True: ライブビュー表示中は撮影条件の変更を反映させない (エラー回避)。False: ライブビュー表示中も撮影条件の変更を反映させる (エラーになる機種がある)

    # exposure settings and options
    program_mode_options = cam.get_program_mode_options().options
    program_mode_P = string_to_program_mode_value("P")
    program_mode_M = string_to_program_mode_value("M")
    print( f"Program Mode Options : {program_mode_options}\n => {[ program_mode_value_to_string(s) for s in program_mode_options]}" )
    if program_mode_P not in program_mode_options or program_mode_M not in program_mode_options:
        print(  "This test requires program mode to be 'P' or 'M'. Swtich the camera settings and recconnect to continue." )
        return
    program_mode_index = program_mode_options.index( cam.get_program_mode().value )

    cam.set_program_mode( program_mode_M )
    shutter_speed_options = cam.get_shutter_speed_options().options
    aperture_value_options = cam.get_aperture_value_options().options
    ev_options = cam.get_exposure_compensation_options().options
    iso_options = cam.get_iso_sensitivity_options().options
    print( f"Shutter Speed Options : {shutter_speed_options}\n => {[ shutter_speed_value_to_string(s) for s in shutter_speed_options]}" )
    print( f"Aperture Value Options : {aperture_value_options}\n => {[ aperture_value_to_string(s) for s in aperture_value_options]}" )
    print( f"Exposure Compensation Options : {ev_options}\n => {[ exposure_compensation_value_to_string(s) for s in ev_options]}" )
    print( f"ISO Sensitivity Options : {iso_options}\n => {[ iso_sensitivity_value_to_string(s) for s in iso_options]}" )

    ss_index = shutter_speed_options.index( cam.get_shutter_speed().value )
    av_index = aperture_value_options.index( cam.get_aperture_value().value )
    ev_index = ev_options.index( cam.get_exposure_compensation().value )
    iso_index = iso_options.index( cam.get_iso_sensitivity().value )
    cam.set_program_mode( program_mode_options[program_mode_index] )

    def turn_program_mode():
        nonlocal program_mode_index
        program_mode_index = (program_mode_index+1) % len(program_mode_options)
        cam.set_program_mode( program_mode_options[program_mode_index] )

    def shutter_speed_up():
        nonlocal ss_index
        index = min( ss_index+1, len(shutter_speed_options)-1 )
        if cam.set_shutter_speed( shutter_speed_options[index] ).success:
            ss_index = index

    def shutter_speed_down():
        nonlocal ss_index
        index = max( ss_index-1, 0 )
        if cam.set_shutter_speed( shutter_speed_options[index] ).success:
            ss_index = index

    def aperture_up():
        nonlocal av_index
        index = min( av_index+1, len(aperture_value_options)-1 )
        if cam.set_aperture_value( aperture_value_options[index] ).success:
            av_index = index

    def aperture_down():
        nonlocal av_index
        index = max( av_index-1, 0 )
        if cam.set_aperture_value( aperture_value_options[index] ).success:
            av_index = index

    def ev_up():
        nonlocal ev_index
        index = min( ev_index+1, len(ev_options)-1 )
        if cam.set_exposure_compensation( ev_options[index] ).success:
            ev_index = index

    def ev_down():
        nonlocal ev_index
        index = max( ev_index-1, 0 )
        if cam.set_exposure_compensation( ev_options[index] ).success:
            ev_index = index

    def iso_up():
        nonlocal iso_index
        index = min( iso_index+1, len(iso_options)-1 )
        if cam.set_iso_sensitivity( iso_options[index] ).success:
            iso_index = index
    
    def iso_down():
        nonlocal iso_index
        index = max( iso_index-1, 0 )
        if cam.set_iso_sensitivity( iso_options[index] ).success:
            iso_index = index

    # af and capture functions
    def capture_image():
        res = cam.capture_image( folder="tests/captured_images", long_exposure=True )
        if res.success:
            print("Captured Image:", res.data)
        else:
            print( f"Failed to capture image. '{res.error_message}'" )
    
    def perform_af():
        res = cam.perform_af()
        if res.success:
            print("Autofocus successful.")
        else:
            print( f"Failed to perform autofocus. '{res.error_message}'" )
    
    # focus area settings and options
    focus_area_options = cam.get_focus_area_options().data
    focus_area = cam.get_focus_area().data
    h_options = focus_area_options["h"]
    h_index = h_options.index( focus_area["h"])
    v_options = focus_area_options["v"]
    v_index = v_options.index( focus_area["v"])
    focus_area_size_options = focus_area_options["size"]
    focus_area_size = focus_area["size"]
    focus_area_size_index = focus_area_size_options.index(focus_area_size)
    print( f"Focus Area Options h:{h_options}, v:{v_options}, size:{focus_area_size_options}" )

    # シングルポイントAFかつPreAFなしのときのみ画像ズームして移動が出来る。それ以外は x1 のみになる。Liveview中は変更できない。
    zoom_options = cam.get_finder_crop_options().options
    zoom_index = zoom_options.index( cam.get_finder_crop().value )
    print( f"Focus zoom Options:{zoom_options} = {[finder_crop_value_to_string(z) for z in zoom_options]}" )

    liveview_size_options = cam.get_liveview_size_options().options
    liveview_size_index = liveview_size_options.index( cam.get_liveview_size().value )
    cam.set_liveview_size( liveview_size_options[-1] )
    print( f"Liveview Size Options: {liveview_size_options}" )

    def focus_area_up():
        nonlocal v_index
        index = min( v_index+1, len(v_options)-1 )
        if cam.set_focus_area( v=v_options[index] ).success:
            v_index = index
    
    def focus_area_down():
        nonlocal v_index
        index = max( v_index-1, 0 )
        if cam.set_focus_area( v=v_options[index] ).success:
            v_index = index
    
    def focus_area_left():
        nonlocal h_index
        index = max( h_index-1, 0 )
        if cam.set_focus_area( h=h_options[index] ).success:
            h_index = index
    
    def focus_area_right():
        nonlocal h_index
        index = min( h_index+1, len(h_options)-1 )
        if cam.set_focus_area( h=h_options[index] ).success:
            h_index = index
    
    def focus_area_size_up():
        nonlocal focus_area_size_index
        index = min( focus_area_size_index+1, len(focus_area_size_options)-1 )
        if cam.set_focus_area( size=focus_area_size_options[index] ).success:
            focus_area_size_index = index
    
    def focus_area_size_down():
        nonlocal focus_area_size_index
        index = max( focus_area_size_index-1, 0 )
        if cam.set_focus_area( size=focus_area_size_options[index] ).success:
            focus_area_size_index = index

    def zoom_in():
        nonlocal zoom_index
        index = min( zoom_index+1, len(zoom_options)-1 )
        if cam.set_finder_crop( zoom_options[index] ).success:
            zoom_index = index
        
    def zoom_out():
        nonlocal zoom_index
        index = max( zoom_index-1, 0 )
        if cam.set_finder_crop( zoom_options[index] ).success:
            zoom_index = index
    
    def window_size_down():
        nonlocal liveview_size_index
        index = min( liveview_size_index+1, len(liveview_size_options)-1 )
        if cam.set_liveview_size( liveview_size_options[index] ).success:
            liveview_size_index = index

    def window_size_up():
        nonlocal liveview_size_index
        index = max( liveview_size_index-1, 0 )
        if cam.set_liveview_size( liveview_size_options[index] ).success:
            liveview_size_index = index

    is_liveview_on = False

    def toggle_liveview():
        nonlocal is_liveview_on
        if is_liveview_on:
            cam.stop_liveview()
            is_liveview_on = False
        else:
            cam.start_liveview()
            is_liveview_on = True

    def reset_settings():
        nonlocal program_mode_index, ss_index, av_index, ev_index, iso_index, h_index, v_index, focus_area_size_index, zoom_index

        current_program_mode = program_mode_value_to_string(program_mode_options[program_mode_index])
        if current_program_mode in ["S", "M"]:
            ss_value = string_to_shutter_speed_value("1/60")
            ss_index = shutter_speed_options.index( ss_value )
            cam.set_shutter_speed( ss_value )
        
        if current_program_mode in ["A", "M"]:
            av_value = string_to_aperture_value("F4.0")
            av_index = aperture_value_options.index( av_value )
            cam.set_aperture_value( av_value )

        if current_program_mode in ["P", "A", "S"]:
            ev_value = string_to_exposure_compensation_value("0.0EV")
            ev_index = ev_options.index( ev_value )
            cam.set_exposure_compensation( ev_value )

        iso_value = string_to_iso_sensitivity_value("ISO 800")
        iso_index = iso_options.index( iso_value )
        cam.set_iso_sensitivity( iso_value )

        h_index = h_options.index( 0 )
        v_index = v_options.index( 0 )
        cam.set_focus_area( h=0, v=0 )

        zoom_value = string_to_finder_crop_value("x1.0")
        zoom_index = zoom_options.index( zoom_value )
        cam.set_finder_crop( zoom_value )

    def print_current_settings():
        # print current settings in a single line, overwriting previous line
        program_mode_str = program_mode_value_to_string(program_mode_options[program_mode_index])
        shutter_speed_str = shutter_speed_value_to_string(shutter_speed_options[ss_index]) if program_mode_str in ["S", "M"] else "auto"
        aperture_value_str = aperture_value_to_string(aperture_value_options[av_index]) if program_mode_str in ["A", "M"] else "auto"
        exposure_compensation_str = exposure_compensation_value_to_string(ev_options[ev_index]) if program_mode_str != "M" else "N/A"
        print("\r"
            f"CAMERA MODE:{program_mode_str} / S:{shutter_speed_str} / F:{aperture_value_str} / EV:{exposure_compensation_str} / "
            f"ISO:{iso_sensitivity_value_to_string(iso_options[iso_index])} / "
            f"Focus({h_options[h_index]}, {v_options[v_index]})/{focus_size_value_to_string(focus_area_size_options[focus_area_size_index])} / "
            f"Zoom:{finder_crop_value_to_string(zoom_options[zoom_index])} --- "
            f"[{'LIVE' if is_liveview_on else 'OFF'}] ", end="", flush=True )

    def print_key_map():
        print("\nKey Map: (Effective only when 'Live View' window is active)")
        print("  W/w: Window size Up/Down" )
        print("  p: Change Program Mode")
        print("  S/s: Shutter Speed Up/Down")
        print("  A/a: Aperture Up/Down")
        print("  E/e: Exposure Compensation Up/Down")
        print("  I/i: ISO Sensitivity Up/Down")
        print("  k/j/h/l: Focus Area Up/Down/Left/Right")
        print("  O/o: Focus Area Size Up/Down")
        print("  Z/z: Zoom In/Out")
        print("  f: Perform Autofocus")
        print("  c: Capture Image")
        print("  <space>: Toggle Live View On/Off")
        print("  0: Reset to standard settings")
        print("  ?: Print this key map")
        print("  q: Quit Test\n")

    key_map = {
        "W": window_size_up,
        "w": window_size_down,
        'p': turn_program_mode,
        'S': shutter_speed_up,
        's': shutter_speed_down,
        'A': aperture_up,
        'a': aperture_down,
        'E': ev_up,
        'e': ev_down,
        'I': iso_up,
        'i': iso_down,
        'k': focus_area_up,
        'j': focus_area_down,
        'h': focus_area_left,
        'l': focus_area_right,
        'O': focus_area_size_up,
        'o': focus_area_size_down,
        'Z': zoom_in,
        'z': zoom_out,
        'f': perform_af,
        'c': capture_image,
        ' ': toggle_liveview,
        '0': reset_settings,
        '?': print_key_map,
#        'q': lambda: print("\nExiting test...")
    }
    ABLE_WITH_LIVEVIEW = "kjhlOo ?"  # These keys can be used without pausing liveview
    AUTO_PAUSE_LIVEVIEW = True   # True: ライブビュー表示中は撮影条件の変更を反映させない (エラー回避)。False: ライブビュー表示中も撮影条件の変更を反映させる (エラーになる機種がある)

    print_key_map()

    toggle_liveview()  # start liveview by default
    while True:
        print_current_settings()

        key = chr(cv2.waitKey(1) & 0xFF)
        if key in key_map:
            if is_liveview_on and AUTO_PAUSE_LIVEVIEW and key not in ABLE_WITH_LIVEVIEW:
                # print( "\nstop/start liveview to apply setting changes...")
                cam.stop_liveview()
                key_map[key]()
                cam.start_liveview()
            else:
                key_map[key]()
        elif key == 'q':
            break
        elif is_liveview_on:
            _show_image_buffer(cam, "Live View", cam.get_liveview_image())
            time.sleep(0.05)  # Add a small delay to avoid high CPU usage
    
    if is_liveview_on:
        print( "\nStop liveview." )
        cam.stop_liveview()
    
    print( "Camera status:",cam.get_status().data)
    print( "Liveview and operations completed." )

    cv2.destroyAllWindows()
    # Liveviewモード中の制限
    #   以下の設定は変更できない。（一旦liveviewをOFFにして変更しONに戻す必要がある）
    #   exposure settings, crop, perform AF, capture_*, bulb*
    #   フォーカスエリアの位置とサイズは変更はできる
    # preAF ONで接続するとcrop設定コマンドはCOMBINATIONエラーになる

#  multiple test cases
def test_batch_cases(cam):
    """テストケースをまとめて連続実行する（一部を除く）"""
    batch_list = [
        test_get_status,
        test_program_mode,
        test_shutter_speed_setting,
        test_exposure_compensation_setting,
        test_iso_sensitivity_setting,
        test_lenszoom_capability,
        test_capture_image,
        test_preview_image,
        test_bulb_capture,
        test_burst_capture,
        test_auto_bracketing,
        test_focus_mode,
        test_focus_adjust,
        test_focus_area,
        test_autofocus,
        test_aflock_and_preview,
        test_liveview,
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
#        print( f"Running {test_case.__name__}...")
        test_case(cam)
    print( "-"*60)
    print( "Batch test completed." )

def default_settings(cam:CameraAPI):
    """カメラの設定を標準設定に戻す"""
    print( "Resetting camera release status and image buffer")
    cam.reset_status()
    print( "Resetting camera exposure settings to standard values")
    _setup_exposure( cam, program_mode = "M", shutter_speed="1/125", aperture_value="F5.6", iso_sensitivity="ISO 800" )
    _setup_exposure( cam, program_mode = "A", exposure_compensation="0.0EV", aperture_value="F5.6", iso_sensitivity="ISO 800" )
    _setup_exposure( cam, program_mode = "S", exposure_compensation="0.0EV", shutter_speed="1/125", iso_sensitivity="ISO 800" )
    _setup_exposure( cam, program_mode = "P", exposure_compensation="0.0EV", iso_sensitivity="ISO 800" )
    print( "Resetting camera focus settings to standard values")
    _setup_focus( cam, focus_mode="MF", focus_pos=(0,0), focus_size=3, focus_distance=500 )  # focus_size, focus_distance 
    _setup_focus( cam, focus_mode="AF-S", focus_afmode="SINGLE" )


# ---------------------------------------------------------------------
# connect to camera and return CameraAPI instance
# ---------------------------------------------------------------------
def test_camera_connect() -> CameraAPI:
    #input("Press Enter to connect to camera...")
    cam = CameraAPI()
    cam._DEBUG_ = 0   # type: ignore

    while True:
        print("Waiting for camera[0] response...")
        # connect to camera with default settings via USB
        res = cam.connect( index=0 ) 
        # connect to camera via local network (IP address)
        # res = cam.connect( ip_address="192.168.1.20" )
        if res.success:
            break
        time.sleep(1)
    print( f"Connected to {res.data['camera_name']}/{res.data['lens_name']}" )

    res = cam.get_program_mode_options()
    if not res.success or len(res.options) != 4:
        print( "Program Mode Options are not available. Please check the camera connection and settings." )
    return cam
#
# Main Menu to run the test cases
#
def test_cameraAPIs():
    """カメラAPIのテストメニューを表示して、各テストケースを選択して実行する"""
    # define the list of test cases to run
    test_cases_menu = [
        test_custom_case,
        test_get_status,
        test_reconnection,
        test_program_mode,
        test_shutter_speed_setting,
        test_exposure_compensation_setting,
        test_iso_sensitivity_setting,
        show_exposure_settings,
        test_lenszoom_capability,
        test_release_status,
        test_capture_image,
        test_preview_image,
        test_bulb_capture,
        test_burst_capture,
        test_auto_bracketing,
        test_focus_mode,
        test_focus_adjust,
        test_focus_area,
        test_autofocus,
        test_aflock_and_preview,
        test_liveview,
        test_liveview_and_capture,
        test_shoot_from_camera,
        test_batch_cases,
    ]

    # connect to the camera before displaying the test menu
    cam = test_camera_connect()

    while True:
        # display the menu of test cases
        print(f"\nAvailable Test Cases ({len(test_cases_menu)}):")
        for i, test_case in enumerate(test_cases_menu):
            print(f"[{i+1}] {test_case.__name__} : {test_case.__doc__}")

        choice = input("Select case number (q:quit) = ").strip().lower()
        if choice == 'q':
            break
        elif choice.isdigit():
            i = int(choice) - 1
            if 0 <= i < len(test_cases_menu):
                test_case = test_cases_menu[i]
                print(f"\n[{i+1}] {test_case.__name__} : {test_case.__doc__}")
                test_case(cam)
        else:
            print("Invalid input. Please enter a case number or 'q' to quit.")

    cam.disconnect()
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

    input("Press Enter to start the Camera API tests...")
    print("Camera API Test Started at ", time.strftime("%Y-%m-%d %H:%M:%S\n"))

    test_cameraAPIs()

    print("\nCamera API Tests Finished at ", time.strftime("%Y-%m-%d %H:%M:%S"))
    input("Press Enter to exit.")
    exit(0)
