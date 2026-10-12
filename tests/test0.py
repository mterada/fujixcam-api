# 
from fujixcam import CameraAPI
from fujixcam.camera_api import API_CODE, XSDK_FOCUS_AFS, XSDK_FOCUS_AFC

with CameraAPI() as cam:
    if not cam.connect().success:
        print( "failed to connect to camera." )
        exit()
    print( "camera connected." )

    print( "camera.get_focus_mode_options() ------------------------------" )
    print( f"Response: {cam.get_focus_mode_options()}" )
    print()

    print( "camera.set_focus_mode( XSDK_FOCUS_AFS ) ------------------------------" )
    print( f"Response: {cam.set_focus_mode( XSDK_FOCUS_AFS )}" )
    print()

    print( "camera.get_focus_mode() ------------------------------" )
    print( f"Response: {cam.get_focus_mode()}" )
    print()

    value = cam._get_prop(API_CODE.API_CODE_GetPreAFMode)
    print( f"PreAFMode: {value}" )
    if value is not None:
        mode = (value % 2)+1
        if cam._set_prop(API_CODE.API_CODE_SetPreAFMode, mode):
            print( f"PreAFMode set to: {mode}" )
    print()

    print( "camera.get_status() ------------------------------" )
    print( f"Response: {cam.get_status()}" )
    print()

    yn = input("return to exit...")

print( "test0 complete." )
print()
