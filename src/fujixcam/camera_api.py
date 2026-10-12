"""Camera API Wrapper on FUJIFILM Camera Control SDK."""
# -----------------------------------------------------
# camera_api.py :
#   CameraAPI provides Camera SDK wrapper 
#
# Copyright 2026 Masahiro Terada (@mterada.com)
# This software is released under the MIT License.
# http://opensource.org/licenses/mit-license.php
# -----------------------------------------------------
import time, os, sys
from datetime import datetime
from dataclasses import dataclass, field #, asdict
from typing import Optional, List, Dict, Any #, TypeVar, Generic

from fujixcam import _clickwrap
from fujixcam._fuji_sdk_loader import *

CAMERA_SDK_NAME = "FUJIFILM_CAMERA_CONTROLL_SDK"
CAMERA_SDK_SITE = "https://www.fujifilm-x.com/special/camera-control-sdk"

@dataclass
class APIResponse:
    success: bool = True
    error_message: str = "" 

#T = TypeVar('T')
#@dataclass
#class APIResponseValue(APIResponse, Generic[T]):
#    Value: Optional[T] = None

@dataclass
class APIResponseValue(APIResponse):
    value: int = 0

@dataclass
class APIResponseList(APIResponse):   # static/reactive/volatile options for API parameters
    options: List[int] = field(default_factory=list)  # list of available options for the parameter, empty if not applicable
    is_reactive: bool = False  # if dpeneent on other settings, True for reactive, False for static
    is_volatile: bool = False  # if can change due to external factors, True for volatile, False for stable

@dataclass
class APIResponseDict(APIResponse):
    data: Dict[str, Any] = field(default_factory=dict)


# Wrapper Class for FUJIFILM Camera SDK
class CameraAPI:
    """ CameraAPI provides convenient functions to control FUJIFILM cameras using the FUJIFILM Camera Control SDK.

    Note:At first time initialization, it will prompt user to accept the license agreement for FUJIFILM Camera Control SDK.
    The license agreement must be accepted to use the SDK functions, and the SDK library will be loaded.
    Then it can be used to connect to the camera, capture images, and adjust settings.
    """
    _DEBUG_ = 0  # debug print flag (0: silent, 1: error print, 2: verbose print)
    _ERR_CODES_TO_ABORT = [ERR_CODE.XSDK_ERRCODE_COMMUNICATION.value,
                           ERR_CODE.XSDK_ERRCODE_HARDWARE.value,
                           ERR_CODE.XSDK_ERRCODE_INTERNAL.value ]  # error codes that are considered fatal and will raise exceptions
    _ERR_CODES_TO_BREAK = [ERR_CODE.XSDK_ERRCODE_COMBINATION.value,
                           ERR_CODE.XSDK_ERRCODE_SEQUENCE.value,
                           ERR_CODE.XSDK_ERRCODE_PARAM.value, 
                           ERR_CODE.XSDK_ERRCODE_UNKNOWN.value,
                           ERR_CODE.XSDK_ERRCODE_UNSUPPORTED.value ] # error codes that can be ignored and break retry loop, since they indicate invalid operation
    _ERR_CODES_TO_RETRY = [ERR_CODE.XSDK_ERRCODE_BUSY.value,
                           ERR_CODE.XSDK_ERRCODE_TIMEOUT.value,
                           ERR_CODE.XSDK_ERRCODE_FORCEMODE_BUSY.value,
                           ERR_CODE.XSDK_ERRCODE_AF_TIMEOUT.value,
                           ERR_CODE.XSDK_ERRCODE_STANDBY.value ]  # error codes that can be retried with wait, since they may be temporary conditions
    _camera_lib: Any = None # shared SDK library instance for all CameraAPI instances, since the SDK is designed to be initialized once per process
    #_connected_cameras = []  # connected camera devices, currently not used since it only supports connecting to the first detected camera as default

    # ----------------------------------------------
    # Constructor: initialize context data, load SDK library 
    # ----------------------------------------------
    def __init__(self):
        # camera session data
        self._lib: Any = None
        self._camera_handle: c_longlong|None = None
        self._camera_name: str = "unknown"
        self._lens_name: str = "unknown"
        self._lens_zoom_capability: int = 0
        self.api_code: c_long = c_long(0)
        self.err_code: c_long = c_long(0)

        # camera sdk context data
        if CameraAPI._camera_lib is None:
            CameraAPI._camera_lib = self._load_library()
            if CameraAPI._camera_lib is None:
                raise RuntimeError("Failed to load FUJIFILM SDK library.")
            # store sdk library reference for instance methods
            self._lib = CameraAPI._camera_lib
            self._trace( "FUJIFILM SDK loaded successfully." )
        else:
            self._trace( "FUJIFILM SDK already loaded, reusing existing instance." )
            raise RuntimeError("CameraAPI instance already exists, multiple instances are not supported in this version.")

        # adjustable parameters for stability and performance tuning
        self._CONNECT_RETRY_INTERVAL = 0.5  # wait upto 5 seconds
        self._CONNECT_RETRY_COUNT = 10
        self._COMMAND_RETRY_INTERVAL = 0.1  # wait upto 1 second
        self._COMMAND_RETRY_COUNT = 10
        self._AF_RETRY_INTERVAL = 0.2  #  wait for INSTANT AF completion
        self._AF_RETRY_COUNT = 5
        self._RELEASE_RETRY_INTERVAL = 0.2  #  wait for S2 response
        self._RELEASE_RETRY_COUNT = 5
        self._LIVEVIEW_RETRY_INTERVAL = 0.05  # wait for liveview buffer
        self._LIVEVIEW_RETRY_COUNT = 20

        # other shooting-related defaults
        self._CAPTURE_COMPLETION_TIMEOUT = 10 # default timeout from shooting to completion (sec)
        self._CAPTURE_SUCCESSIVE_COUNT = 5    # default number of successive captures
        self._BULB_PROCESSING_TIMEOUT = 60*60 # default timeout for bulb processing (sec)

    def __repr__(self):
        return f"CameraAPI(camera_handle={self._camera_handle}, camera_name='{self._camera_name}', lens_name='{self._lens_name}')"
    
    # Destructor: cleanup object (disconnect and unload SDK library).
    def __del__(self):
        if self is None:
            return
        try:
            self.disconnect(shutdown=False, forced=True)  # disconnect without waiting for reset, since object is being destroyed
        except Exception as e:
            self._print( f"Exception during disconnect in destructor: {e}" )
        if self._lib is not None:
            try:
                self._unload_library()
            except Exception as e:
                self._print( f"Exception during unload_library in destructor: {e}" )
            CameraAPI._camera_lib = None
    
    def __enter__(self):
        """Context manager entry - returns the CameraAPI instance."""
        #self._trace("Entering camera context manager.")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - delete CameraAPI instance."""
        #self._trace("Exiting camera context manager.")
        self.disconnect()
        time.sleep(0.5)  # wait a moment for camera to stabilize between disconnect and unload
        self._unload_library()
        CameraAPI._camera_lib = None

    # Load the SDK library and initialize it. Returns the library instance if successful, None otherwise.
    def _load_library(self):
        lib = install_sdk()
        if lib is None:
            return None

        # initialize the library after license agreement is accepted
        if lib.m_pfnInit and (lib.m_pfnInit(0) == XSDK_COMPLETE):
            return lib
        else: 
            self._print( "Failed to initialize SDK library, error code:", lib.get_error() )
            return None
    
    def _unload_library(self):
        if self._lib is not None:
            self._lib.m_pfnExit()
            self._lib = None
            self._trace( "FUJIFILM SDK unloaded." )

    # -------------------------------------------------
    # Common API response handling: error/success, error string, debug print
    # -------------------------------------------------
    # Clear last error code
    def _clear_error_code(self):
        self.api_code = c_long(0)
        self.err_code = c_long(0)
        return True
    # Load last error code from SDK 
    def _load_error_code(self):
        self._lib.m_pfnGetErrorNumber(self._camera_handle, byref(self.api_code), byref(self.err_code))
        return False    # always return False to indicate error occurred, so that it can be used in retry loop
    # Get last error string
    def _get_error_string(self):
        # self._lib.m_pfnGetErrorNumber(self._camera_handle, byref(self.api_code), byref(self.err_code))
        if self.api_code.value == 0 or self.err_code.value == 0:
            return "No error."
        api_code_str = API_CODE(self.api_code.value).name if self.api_code.value in API_CODE._value2member_map_ else f"0x{self.api_code.value:08X}"
        err_code_str = ERR_CODE(self.err_code.value).name if self.err_code.value in ERR_CODE._value2member_map_ else f"0x{self.err_code.value:08X}"
        return f"{api_code_str}:{err_code_str}"

    def _check_error_message(self, error_message=None) -> str:
        if error_message is None:
            self._load_error_code()
            error_message = self._get_error_string()    # note: reset error code after getting error string
            self._print( "api error - ", error_message )
            # When fatal error occurs, CameraAPI raise RuntimeError with error message
            if self.err_code.value in CameraAPI._ERR_CODES_TO_ABORT:
                error_message += ", please check the camera connection."
                raise RuntimeError(error_message)
        else:
            # override error message, since it's handled as not fatal
            self._print( "warning - ", error_message )
        return error_message

    # Standard API error/success response
    def _api_success(self) -> APIResponse:
        return APIResponse( success=True )
    def _api_error(self, error_message=None ) -> APIResponse:
        return APIResponse( success=False, error_message=self._check_error_message(error_message) )

    # API response with a single value
    def _api_success_value(self, value=0) -> APIResponseValue:
        return APIResponseValue( success=True, value=value )
    def _api_error_value(self, error_message=None) -> APIResponseValue:
        return APIResponseValue( success=False, error_message=self._check_error_message(error_message) )

    # API response with a list of options (for parameter settings)
    def _api_success_list(self, options=[], is_reactive=False, is_volatile=False) -> APIResponseList:
        return APIResponseList( success=True, options=options, is_reactive=is_reactive, is_volatile=is_volatile )
    def _api_error_list(self, error_message=None) -> APIResponseList:
        return APIResponseList( success=False, error_message=self._check_error_message(error_message) )

    # API response with a data structure (dictionary)
    def _api_success_dict(self, data={} ) -> APIResponseDict:
        return APIResponseDict( success=True, data=data )
    def _api_error_dict(self, error_message=None) -> APIResponseDict:
        return APIResponseDict( success=False, error_message=self._check_error_message(error_message) )

    # debug print
    def _print(self, *args, **kwargs):
        if self._DEBUG_ > 0:
            print( "CameraAPI:error>", *args, **kwargs )
    # debug print for verbose tracing
    def _trace(self, *args, **kwargs):
        if self._DEBUG_ > 1:
            print( "CameraAPI:trace>", *args, **kwargs )

    # retry helper for API calls that may fail due to temporary conditions (e.g., camera busy, AF in progress, etc.)
    def _retry_api_call(self, api_function, retry_interval=0.1, retry_count=10, allow_timeout=False) -> bool:
        for i in range(1+retry_count):
            self._clear_error_code()  # clear previous error code before calling API function
            if api_function():  # api_function should set error code if it fails
                return True

            # check error reason and decide whether to retry or not
            if self.err_code.value in CameraAPI._ERR_CODES_TO_BREAK:
                self._trace( f"API call failed with {self._get_error_string()}, no more retry." )
                return False
            if self.err_code.value in CameraAPI._ERR_CODES_TO_ABORT:
                self._print( f"API call failed with {self._get_error_string()}, fatal error." )
                return False

            # retry after error check
            if self.err_code.value != 0:  # in CameraAPI._ERR_CODES_TO_RETRY or unexpected error code
                self._trace( f"API BUSY, retrying {i}/{retry_count} after {retry_interval} seconds..." )
            elif retry_count>0:   # no error but not complete
                self._trace( f"Not ready, checking {i+1}/{retry_count} after {retry_interval} seconds..." )
            else:   # no error and no retry
                return False 
            if retry_interval > 0:
                time.sleep(retry_interval)
        # return True if timeout is allowed, False if it's considered failure
        if allow_timeout:
            self._trace( f"API call timeout after {retry_count} retries" )
            return True 
        self._print( f"API call failed after {retry_count} retries - {self._get_error_string()}" )
        return False 

    # -------------------------------------------------
    # Camera Connection and Initialization
    # -------------------------------------------------
    # Check if camera is connected
    def is_connected(self) -> bool:
        """ Check if the camera is currently connected and responsive.
        """
        if self._camera_handle == None:
            return False

        # check release status to verify camera is still connected    
        self._clear_error_code()
        release_status = c_long(0)
        if self._lib.m_pfnGetReleaseStatus(self._camera_handle, byref(release_status)) == XSDK_COMPLETE:
            return True
        self._load_error_code()

        # if GetReleaseStatus failed, check error code to determine if it's a fatal error or not
        if self.err_code.value in CameraAPI._ERR_CODES_TO_ABORT:
            # consider camera disconnected if communication error or hardware error occurs
            self._trace( f"Camera connection lost: {self._get_error_string()}" )

            # force disconnect the camera handle to prevent further operations
            self._lib.m_pfnClose(self._camera_handle)
            self._camera_handle = None
            self._camera_name = "unknown"
            self._lens_name = "unknown"
            self._lens_zoom_capability = 0
            return False

        # consider camera still connected, but camera is not responsive
        self._print( f"Camera response error: {self._get_error_string()}" )
        return True

    # Connect to Camera (USB recommended for stable connection and performance, but Wi-Fi connection is also possible with some limitations)
    def connect(self, index=0, ip_address=None, camera_name=None) -> APIResponseDict:
        """ Connect to the camera using the specified interface (default is USB). 
            It detects the camera, opens a session, and initializes camera settings.
        """
        if self._camera_handle is not None:
            return self._api_error_dict("Camera is already connected, please disconnect first.")

        if ip_address is None:
            ip_address = b""
            interface = c_long(XSDK_DSC_IF_USB)
            self._trace( "Connecting to camera via USB interface." )
        elif ip_address == "*":
            ip_address = b""
            interface = c_long(XSDK_DSC_IF_WIFI_LOCAL)
            self._trace( "Connecting to camera via WIFI (Auto)." )
        else:
            # ip_address format is IPv4 address "*.*.*.*"
            ip_address = create_string_buffer(ip_address.encode("UTF-8"), 16)  # 16 bytes for null-terminated string
            interface = c_long(XSDK_DSC_IF_WIFI_IP)
            self._trace( f"Connecting to camera via WIFI with IP address: {ip_address.value.decode('utf-8')}" )
        if camera_name is None:
            camera_name = b""
        else:
            camera_name = create_string_buffer(camera_name.encode("UTF-8"), 16)  # 16 bytes for null-terminated string
        #
        # Detect Camera at least one camera
        #
        camera_count = c_long(1)
        result = self._lib.m_pfnDetect(interface, ip_address, camera_name, byref(camera_count))
        if result != XSDK_COMPLETE or camera_count.value == 0:
            return self._api_error_dict( "No camera detected." )
        # 
        # Open 1st Camera as default device
        #
        if index < 0 or index >= camera_count.value:
            return self._api_error_dict( f"Invalid camera index {index}, detected camera count: {camera_count.value}" )

        _camera_handle = c_longlong(0)
        device = "ENUM:" + str(index)  # use "ENUM:0", "ENUM:1", ... to specify camera by index
        device = create_string_buffer(device.encode("UTF-8"), 10)
        camera_mode = c_long(0)  # tether mode is required
        options = c_long(0)

        if( self._lib.m_pfnOpenEx(device, byref(_camera_handle), byref(camera_mode), options) != XSDK_COMPLETE ):
            return self._api_error_dict()
        
        #self._trace( f"Camera detected:{camera_count.value}, opened:{index}, dsc mode:{hex(camera_mode.value)}" )
        if camera_mode.value & XSDK_DSC_MODE_TETHER == 0:
            self._lib.m_pfnClose(_camera_handle)
            return self._api_error_dict("Camera is not in tethered mode.")
 
        # initialize camera settings
        if ( self._setup_camera_handle(_camera_handle) == False ):
            self.disconnect()
            return self._api_error_dict("Camera initialization failed.")

        return self._api_success_dict( { "camera_count": camera_count.value,
                                         "camera_index": index,
                                         "camera_name": self._camera_name,
                                         "lens_name": self._lens_name if len(self._lens_name)>0 else "NO LENS" } )

    # Disconnect Camera
    def disconnect(self, shutdown=False, forced=False) -> APIResponse:
        """ Closing the session and resetting camera status.
            If shutdown is True, it will try to power off the camera.
        """
        # check if camera is connected
        if not self.is_connected():
            self._trace( "Camera is not connected, or already disconnected." )
            return self._api_success()
        
        # reset status before closing session
        if not forced:
            self.reset_status()

        if shutdown:
            # shutdown camera
            if self._lib.m_pfnPowerOFF(self._camera_handle) == XSDK_COMPLETE:
                self._trace( "Camera powered off successfully." )
        else:
            # back to camera priority mode befor closing
            retry_interval = self._COMMAND_RETRY_INTERVAL if not forced else 0  # if forced, avoid 'time.sleep' in destructor
            retry_count = self._COMMAND_RETRY_COUNT if not forced else 100
            self._retry_api_call( lambda: self._lib.m_pfnSetPriorityMode(self._camera_handle, c_long(XSDK_PRIORITY_CAMERA))==XSDK_COMPLETE or self._load_error_code(),
                            retry_interval=retry_interval, retry_count=retry_count )
            # close session
            self._lib.m_pfnClose(self._camera_handle)
            #if not forced:
            #    time.sleep(0.6)  # wait a moment for camera to stabilize after closing session
            self._trace( "Camera session closed successfully." )

        # clear camera handle
        self._camera_handle = None
        self._camera_name = "unknown"
        self._lens_name = "unknown"
        self._lens_zoom_capability = 0
        return self._api_success()

    def reset_status(self) -> APIResponse:
        """ Reset the camera status for stable shooting, without closing the session.
            Disabling live view, resetting through image zoom, unlocking any stuck mode, and deleting any remaining image in camera buffer.
        """
        if self._camera_handle is None:
            return self._api_error("No camera connected.")
        
        # disable liveview and reset through image zoom ( in pc control mode )
        self._clear_error_code()
        if self._check_liveview_buffer() > 0:
            self._set_prop(API_CODE.API_CODE_StopLiveView)

        self._load_error_code()
        if self.err_code.value in CameraAPI._ERR_CODES_TO_ABORT:
            return self._api_error()

        self._set_prop(API_CODE.API_CODE_SetThroughImageZoom, XSDK_THROUGHIMAGE_ZOOM_10)

        # delete any remaining image in camera buffer
        self._delete_image()

        # unlock any stuck mode from previous shooting session
        self._reset_release_status()

        return self._api_success()

    def _reset_release_status(self):
        # check current release status (bit flags) and try to reset it by canceling any active mode
        prev_status = self._get_release_status()
        if prev_status == XSDK_RELEASE_STATUS_NONE:
            return
        self._trace( f"Camera is in release status {hex(prev_status)}, trying to reset by canceling release..." )

        if prev_status & XSDK_RELEASE_STATUS_BULB:
            self._trace( "Camera is in bulb (long exposure) status, canceling bulb." )
            self.bulb_off( abort=True )
            prev_status = self._get_release_status()  # update status, since it may have changed

        if prev_status & XSDK_RELEASE_STATUS_S1:
            self._trace( "Camera is in S1 (half-press) status, releasing S1." )
            self._release_mode(XSDK_RELEASE_N_S1OFF)
            prev_status = self._get_release_status()  # update status, since it may have changed

        if prev_status & XSDK_RELEASE_STATUS_AF:
            self._trace( "Camera is in AF (autofocus) status, canceling AF." )
            self._release_mode(XSDK_RELEASE_N_AF)
        if prev_status & XSDK_RELEASE_STATUS_AFL:
            self._trace( "Camera is in AFL (auto focus lock) status, canceling AFL." )
            # STATUS AFL is not set only by RELEASE_AFL but also RELEASE_AF, RELEASE_INSTANTAF 
            if not self._release_mode(XSDK_RELEASE_N_AFL):
                if not self._release_mode(XSDK_RELEASE_N_AF):
                    self._release_mode(XSDK_RELEASE_N_INSTANTAF)
        # AFLを解除するとAF_ONが復活することがある
        if prev_status & XSDK_RELEASE_STATUS_AF:
            self._trace( "Camera is in AF (autofocus) status, canceling AF." )
            self._release_mode(XSDK_RELEASE_N_AF)
        if prev_status & XSDK_RELEASE_STATUS_AEL:
            self._trace( "Camera is in AEL (auto exposure lock) status, canceling AEL." )
            self._release_mode(XSDK_RELEASE_N_AEL)
        if prev_status & XSDK_RELEASE_STATUS_WBL:
            self._trace( "Camera is in WBL (white balance lock) status, canceling WBL." )
            self._release_mode(XSDK_RELEASE_N_WBL)
        if prev_status & XSDK_RELEASE_STATUS_SHOOTING:
            self._trace( "Camera is in shooting status, canceling shooting." )
            self._release_mode(XSDK_RELEASE_CANCEL)
            self._delete_image()  # delete any remaining image in camera buffer

    def _get_buffer_capacity(self) -> tuple[int, int]:
        count = c_long(0)
        total = c_long(0)
        if self._lib.m_pfnGetBufferCapacity(self._camera_handle, byref(count), byref(total)) != XSDK_COMPLETE:
            self._load_error_code()
            self._print( f"GetBufferCapacity failed with {self._get_error_string()}" )
            return (0, 0)
        return (count.value, total.value)

    def get_status(self) -> APIResponseDict:
        """ Inspect the camera connection activity and release status of the camera.
            'buffered' indicates currently stored image count and total buffer capacity in the camera.
            The other status indicates whether the camera is in shooting, bulb, S1, AF, AEL, AFL, WBL.
            Returns an APIResponseDict with the dictionary of status.
        """
        if self._camera_handle is None:
            return self._api_error_dict("No camera connected.")

        camera_status = { "buffered": (0,0),
                          "liveview": False,
                          "pre_af": False,
                          "shooting": False,
                          "bulb": False,
                          "S1": False,
                          "AF": False,
                          "AEL": False,
                          "AFL": False,
                          "WBL": False }

        # get buffer capacity and liveview status
        count, total = self._get_buffer_capacity()

        camera_status["buffered"] = (count, total)
        if self._check_liveview_buffer() > 0:
            camera_status["liveview"] = True

        camera_status["pre_af"] = (self._get_prop(API_CODE.API_CODE_GetPreAFMode) == XSDK_ON) # check if pre-AF is active

        # get release status and parse it into individual flags
        release_status = self._get_release_status()
        if release_status & XSDK_RELEASE_STATUS_SHOOTING:
            camera_status["shooting"] = True
        if release_status & XSDK_RELEASE_STATUS_BULB:
            camera_status["bulb"] = True
        if release_status & XSDK_RELEASE_STATUS_S1:
            camera_status["S1"] = True
        if release_status & XSDK_RELEASE_STATUS_AF:
            camera_status["AF"] = True
        if release_status & XSDK_RELEASE_STATUS_AEL:
            camera_status["AEL"] = True
        if release_status & XSDK_RELEASE_STATUS_AFL:
            camera_status["AFL"] = True
        if release_status & XSDK_RELEASE_STATUS_WBL:
            camera_status["WBL"] = True

        self._trace( f"Camera status: {camera_status}" )
        return self._api_success_dict(camera_status)

    def _get_release_status(self) -> int:
        # get release status 
        self._clear_error_code()
        release_status = c_long(0)
        if self._lib.m_pfnGetReleaseStatus(self._camera_handle, byref(release_status)) == XSDK_COMPLETE:
            # XSDK_RELEASE_STATUS_NONE, XSDK_RELEASE_STATUS_SHOOTING, XSDK_RELEASE_STATUS_BULB,...
            return release_status.value
        self._load_error_code()
        return XSDK_RELEASE_STATUS_NONE  # 0x0000

    # setup default configuration
    def _setup_camera_handle(self, camera_handle) -> bool:
        # store camera handle for future API calls
        self._camera_handle = camera_handle

        # get camera info and lens info
        device_info = DeviceInformation()
        if self._lib.m_pfnGetDeviceInfo(self._camera_handle, byref(device_info)) != XSDK_COMPLETE:
            return False
        self._camera_name = device_info.vender_name.decode("utf-8").rstrip('\x00')\
              + " " + device_info.product_name.decode("utf-8").rstrip('\x00')

        lens_info = LensInformation()
        if self._lib.m_pfnGetLensInfo(self._camera_handle, byref(lens_info)) != XSDK_COMPLETE:
            return False
        self._lens_name = lens_info.product_name.decode("utf-8").rstrip('\x00')
        self._lens_zoom_capability = lens_info.zoom_capability

        self._delete_image()  # any previous image in camera buffer must be cleared befor switching to PC controll mode

        # controll from PC
        if not self._retry_api_call( lambda: self._lib.m_pfnSetPriorityMode(self._camera_handle, c_long(XSDK_PRIORITY_PC))==XSDK_COMPLETE or self._load_error_code(),
                                     retry_interval=self._COMMAND_RETRY_INTERVAL, retry_count=self._COMMAND_RETRY_COUNT ):
            return False

        # set media record to OFF to prevent saving images to camera storage
        if not self._retry_api_call( lambda: self._lib.m_pfnSetMediaRecord(self._camera_handle, c_long(XSDK_MEDIAREC_OFF))==XSDK_COMPLETE or self._load_error_code(),
                                     retry_interval=self._COMMAND_RETRY_INTERVAL, retry_count=self._COMMAND_RETRY_COUNT ):
            return False

        # initialize basic camera settings
        self.reset_status()

        return True

    # ----------------------------------------------
    # image capture controls (basic functionality)
    # ----------------------------------------------
    # Capture Full-image to file or Preview to buffer
    def capture_image(self, folder=None, filename=None, long_exposure=False) -> APIResponseDict:
        """ Take a photo of full image and save it to a file.
            If folder is not specified, it will be saved in the current working directory.
            If filename is not specified, it will be generated based on the current date/time automatically.
            (filename is basename without extension, and the extension is determined by the current image format setting of the camera.)
            If using shutter speed longer than 10 seconds, long_exposure flag must be set to True to allow longer waiting time avoiding timeout error. 
        """
        self._delete_image()  # clear previous image if any

        # calculate waiting time based on current shutter speed
        max_wait_seconds = self._CAPTURE_COMPLETION_TIMEOUT*2  # default wait time for normal shutter speed (capturing+processing)
        if long_exposure:
            # verify whether shutter speed is slow shutter speed or not
            ae_result = self.get_program_mode()
            if ae_result.success and ae_result.value in [XSDK_PROGRAMMODE_M, XSDK_PROGRAMMODE_S]:
                ss_result = self.get_shutter_speed()
                if ss_result.success:
                    shutter_speed = ss_result.value
                    if shutter_speed >= XSDK_SHUTTER_SPEED_THRESHOLD_MINUTES:
                        max_wait_seconds = 60*60  # 60 minutes for minutes-level shutter speed  
                    elif shutter_speed >= XSDK_SHUTTER_SPEED_THRESHOLD_SECONDS:
                        max_wait_seconds = 60   # 60 seconds for slow shutter speed
                    else:
                        max_wait_seconds = self._CAPTURE_COMPLETION_TIMEOUT   # default wait time for normal shutter speed
                    self._trace( f"Slow shutter wait enabled, ss value: {shutter_speed}, max wait time: {max_wait_seconds} seconds" )
            else:
                max_wait_seconds = 60*60  # assuming auto shutter speed upto minutes-level (in this implementation )
                self._trace( f"Long exposure flag is set but max wait time is not calculated before shooting, using default {max_wait_seconds}")

        # shoot image
        if not self._shoot( s1on_status=self._status_for_s2() ):
            return self._api_error_dict()

        if not self._wait_for_image_ready(max_wait_seconds=max_wait_seconds):
            return self._api_error_dict( "No image in camera buffer or image is not ready." )

        result = self._save_image_object(folder, filename, self._files_per_shot() )
        return result

    # Capture Successive Images to file
    def capture_multi_images(self, folder=None, count=5, interval=0.01) -> APIResponseDict:
        """ Take a series of photos successive and save them to files.
            Filename is generated based on the current date/time automatically.
            Count is the number of images to capture, and interval is waiting time in seconds for next shot.
            Count is limited by the camera buffer capacity which can be checked by get_status() API.
            Note:
            - This function does not support long exposure mode.
            - This function is not exactly same as burst shooting mode of the camera.
        """
        self._delete_image()  # clear previous image if any

        _, total_count = self._get_buffer_capacity()
        if total_count < count:
            return self._api_error_dict( f"Camera buffer capacity is {total_count}, cannot capture {count} images." )

        # shooting step depends on focus mode/program mode
        s1on_status = self._status_for_s2()

        for i in range(count):
            shot = self._shoot( s1on_status=s1on_status )
            if not shot:
                self._print( f"Image burst shooting failed at shot {i+1}/{count} with {self._get_error_string()}" )
                continue   # igonore error and try next shot
            time.sleep(interval)  # wait for next shot
        self._trace( f"Image burst {count} shots successfully, transferring images from camera buffer..." )

        all_shots = []
        num = self._files_per_shot()
        for i in range(count):
            if not self._wait_for_image_ready( max_wait_seconds=self._CAPTURE_COMPLETION_TIMEOUT ):
                break
            each_shot = self._save_image_object(folder, None, num)    # save each shot to file(s) : filename, datasize, object
            if not each_shot.success or each_shot.data is None:
                break
            all_shots.append( each_shot.data )

        if len(all_shots) < count:
            self._reset_release_status()
            self._print( "Image burst shooting missed some images while sequence." )

        totalsize = sum( [ each_shot["datasize"] for each_shot in all_shots ] )
        self._trace( f"Saved images as files : {totalsize} bytes, objects = {all_shots}" )
        return self._api_success_dict( { "objects": all_shots, "datasize":totalsize } )

    def capture_preview(self) -> APIResponseDict:
        """ Take a photo for checking camera settings and transfer preview image from the camera and return it as a memory buffer.
            The preview image format is JPEG, smaller in size and lower in resolution than the full image.
            It is for quick previewing without saving the full image to a file.
            This function does not support long_exposure flag, then waiting time is up to 10 seconds for normal shutter speed.
        """
        self._delete_image()  # clear previous image if any

        # shoot image
        if not self._shoot( s1on_status=self._status_for_s2() ):
            return self._api_error_dict()
        
        if not self._wait_for_image_ready():
            return self._api_error_dict( "No image in camera buffer or image is not ready." )

        # get preview image data from camera
        buffer, dcf_type = self._get_preview_image()
        if buffer is None:
            return self._api_error_dict( "GetPreviewImage failed." )

        self._delete_image()  # clear image after reading preview

        return self._api_success_dict( { "buffer": bytearray(buffer), "size": len(buffer) } )

    def bulb_on(self) -> APIResponse:
        """ Start bulb shooting mode until bulb_off() is called.
            This function is useful for taking long exposure as you like.
            Note:
            - The camera must be in manual mode (M), and shutter_speed must be set to "Bulb" for this function to work.
        """
        # normal case: perform S1ON -> S2_S1OFF sequence  with retry if needed
        if not self._retry_api_call( lambda: self._release_mode( XSDK_RELEASE_S1ON ),
                                     retry_interval=self._COMMAND_RETRY_INTERVAL, retry_count=self._COMMAND_RETRY_COUNT ):
            errer_string = "S1ON trigger failed: " + self._get_error_string()
            self._reset_release_status()
            self._print( errer_string )
            return self._api_error( errer_string )

        #self._trace( f"Release status after S1ON: {hex(self._get_release_status())}" )
        s1on_status = XSDK_RELEASE_STATUS_S1 # | XSDK_RELEASE_STATUS_AFL | XSDK_RELEASE_STATUS_AEL
        if not self._retry_api_call( lambda: (self._get_release_status() & s1on_status == s1on_status),
                                     retry_interval=self._COMMAND_RETRY_INTERVAL*10, retry_count=self._COMMAND_RETRY_COUNT ):
            errer_string = "S1ON status failed: " + self._get_error_string()
            self._reset_release_status()
            self._print( errer_string )
            return self._api_error( errer_string )
        self._trace( f"Release status ready : {hex(s1on_status)}" )

        if not self._retry_api_call( lambda: self._release_mode( XSDK_RELEASE_BULBS2_ON ),
                                     retry_interval=self._RELEASE_RETRY_INTERVAL, retry_count=self._RELEASE_RETRY_COUNT ):
            errer_string = "BULB ON trigger failed: " + self._get_error_string()
            self._reset_release_status()
            self._print( errer_string )
            return self._api_error( errer_string )

        self._trace( "Bulb shooting mode started, waiting for bulb_off() to end the shooting." )
        return self._api_success()

    def bulb_off(self, folder=None, filename=None, abort=False) -> APIResponseDict:
        """ Stop bulb shooting mode.
            This function should be called after bulb_on() to end the bulb shooting and save the image.
            If filename is not specified, it will be generated based on the current date/time automatically.
            If abort is True, the bulb shooting will be aborted and the image will not be saved.
        """
        if self._get_release_status() & XSDK_RELEASE_STATUS_BULB == 0:
            return self._api_error_dict( "Camera is not in bulb mode." )

        if not self._retry_api_call( lambda: self._release_mode( XSDK_RELEASE_N_BULBS1OFF ),
                                     retry_interval=self._RELEASE_RETRY_INTERVAL, retry_count=self._RELEASE_RETRY_COUNT ):
            return self._api_error_dict( "Failed to turn off BULB mode." )

        if abort:
            self._trace( "Bulb shooting aborted, image will not be saved." )
            time.sleep(1)  # wait a moment to ensure bulb off is completed before canceling release state
            self._release_mode(XSDK_RELEASE_CANCEL)  # cancel any remaining release state
            time.sleep(1)
            self._delete_image()
            return self._api_success_dict({})

        self._trace( "Bulb shooting completed, waiting for image to be ready for saving..." )
        if self._wait_for_image_ready( max_wait_seconds=self._BULB_PROCESSING_TIMEOUT )== False:
            return self._api_error_dict( "Bulb shooting completed but post processing aborted." )

        result = self._save_image_object(folder, filename, self._files_per_shot() )
        return result

    def shoot_from_camera(self, enable=True) -> APIResponse:
        """ Shoot image by camera operation and get the image data from camera buffer later.
            Caller can use get_status() to check if the image is ready, and then call aquire_images() to retrieve the image data.
        """
        self._delete_image()  # clear previous image if any

        priority_mode = XSDK_PRIORITY_CAMERA if enable else XSDK_PRIORITY_PC
        if not self._retry_api_call( lambda: self._lib.m_pfnSetPriorityMode(self._camera_handle, c_long(priority_mode))==XSDK_COMPLETE or self._load_error_code(),
                                     retry_interval=self._COMMAND_RETRY_INTERVAL, retry_count=self._COMMAND_RETRY_COUNT ):
            return self._api_error( "Shoot from camera failed." )
        return self._api_success()

    def acquire_images(self, folder=None, max_wait_seconds=5, max_image_count=100) -> APIResponseDict:
        """ Acquire image data from camera buffer after shoot_from_camera() is called and the image is ready.
            Filename will be generated based on the current date/time automatically.
        """
        #if not self._get_release_status() & XSDK_RELEASE_STATUS_SHOOTING:
        #    return self._api_error( "No image in camera buffer or image is not ready." )

        all_shots = []
        num = self._files_per_shot()
        #for i in range(count):
        while True:
            if not self._wait_for_image_ready( max_wait_seconds=max_wait_seconds, allow_timeout=True ):
                break
            if self._get_buffer_capacity()[0] == 0:
                self._trace( "No more image in camera buffer." )
                break
            each_shot = self._save_image_object(folder, None, num)    # save each shot to file(s) : filename, datasize, object
            if not each_shot.success or each_shot.data is None:
                break
            all_shots.append( each_shot.data )
            if len(all_shots) >= max_image_count:
                self._print( f"Reached maximum save images limit: {max_image_count}, stopping acquire." )
                break
        totalsize = sum( [ each_shot["datasize"] for each_shot in all_shots ] )
        self._trace( f"Saved images as files : {totalsize} bytes, objects = {all_shots}" )
        return self._api_success_dict( { "objects": all_shots, "datasize":totalsize } )

    def _generate_basename(self, filename=None) -> str:
        if filename is None or filename.strip() == "":
            # generate file name based on current date/time, e.g., "2023_0601_1234-5678"
            return datetime.now().strftime("%Y_%m%d_%H%M-%S%f")[:-4] 
        else:
            # use the specified filename without directory path and extension
            return os.path.splitext(filename)[1]

    def _validate_folder(self, folder) -> str:
        if folder is None or folder == "" :    # use current working directory if no folder specified
            folder = os.getcwd()
            self._trace( f"image files -> current directory: '{folder}'" )
        elif os.path.exists(folder) and os.path.isdir(folder):
            self._trace( f"image files -> target directory : '{folder}'" )
        else:
            self._print( f"Invalid folder path: '{folder}', using current directory instead." )
            folder = os.getcwd()
        return folder

    def _write_file(self, filename, buffer) -> bool:
        try:
            with open(filename, "wb") as img_file:
                img_file.write( bytearray(buffer) )
                return True
        except IOError as e:
            self._print( f"File write error: {filename} as {e} " )
            return False

    # get image data from camera buffer and save it to file(s)
    def _save_image_object(self, folder=None, filename=None, files_per_shot=1 ) -> APIResponseDict:
        # filename is basename without extension, and the extension is determined by the current image format setting of the camera.
        target_folder = self._validate_folder(folder)
        object_name = self._generate_basename(filename)
        output_files = []
        output_sizes = []
        for i in range(files_per_shot):     # save each image file in the shot (e.g., RAW + JPEG)
            buffer, dcf_type = self._get_image()
            if buffer is None or dcf_type is None:
                self._print( f"GetImage failed. Inner file type:{dcf_type}" )
                break
            # sidecar images have to be saved with the same base name but different extension
            object_file = object_name + dcf_type   # use the same base name but with the correct file extension
            if not self._write_file( os.path.join(target_folder, object_file), buffer ):
                self._print( f"Failed to save image:{object_file}." )
                break
            output_sizes.append( len(buffer))
            output_files.append( object_file )  # use the same base name but with the correct file extension
            self._trace( f"Image[{i}]: {output_files[i]}, size: {output_sizes[i]} bytes." )

        if len(output_files) < files_per_shot:
            self._reset_release_status()
            return self._api_error_dict( f"Failed to save images, saved {len(output_files)}/{files_per_shot}." )

        result_dict = {
            "folder": target_folder, "filename": object_name, "datasize": sum(output_sizes), "object": output_files
        }
        return self._api_success_dict(result_dict)

    def _release_mode(self, release_mode) -> bool:
        """ Release the camera with specified release mode, and return (success, is_af_failure).
            If success is False, it means the release failed due to some error or AF failure.
            If is_af_failure is True, it means the release failed due to AF failure.
            Caller has to cancel the release state according to the release mode used, e.g., if S1ON is used, then cancel with N_S1OFF
        """
        shot_option, shot_status = c_long(0), c_long(0)
        if self._lib.m_pfnRelease(self._camera_handle, c_long(release_mode), byref(shot_option), byref(shot_status)) != XSDK_COMPLETE:
            self._load_error_code()
            self._trace( f"Release mode {hex(release_mode)} failed." )  # ERRCODE_SHOOT_ERROR
            return False
        if shot_status.value == XSDK_RELEASE_AF_FAILURE:
            self._trace( f"Release mode {hex(release_mode)} failed with AF_FAILURE." )
            return False
        self._trace( f"Release mode {hex(release_mode)} executed successfully." )
        return True

    def _status_for_s2(self) -> int:
        status_flags = XSDK_RELEASE_STATUS_S1
        # if not manual focus, then AFL is expected after S1ON
        focus_mode = self.get_focus_mode()
        if focus_mode.success and focus_mode.value != XSDK_FOCUS_MANUAL:
            status_flags |= XSDK_RELEASE_STATUS_AFL
        # if not manual exposure, then AEL is expected after S1ON 
        ae_mode = self.get_program_mode()
        if ae_mode.success and ae_mode.value != XSDK_PROGRAMMODE_M:
            status_flags |= XSDK_RELEASE_STATUS_AEL
        return status_flags

    # Shoot Image with S1ON -> S2_S1OFF sequence, and wait for image ready in camera buffer
    # max_wait_seconds: maximum wait time for image ready in camera buffer, default is 10 seconds
    # s1on_status: expected release status after S1ON, default is S1|AFL|AEL for non-manual focus and non-manual exposure
    def _shoot(self, s1on_status=None) -> bool:
        if s1on_status is None:
            s1on_status = XSDK_RELEASE_STATUS_S1 | XSDK_RELEASE_STATUS_AFL | XSDK_RELEASE_STATUS_AEL

        # normal case: perform S1ON -> S2_S1OFF sequence  with retry if needed
        if not self._retry_api_call( lambda: self._release_mode( XSDK_RELEASE_S1ON ),
                                     retry_interval=self._COMMAND_RETRY_INTERVAL, retry_count=self._COMMAND_RETRY_COUNT ):
            self._release_mode( XSDK_RELEASE_N_S1OFF )
            self._print( "Image shot error, S1ON trigger failed." )
            return False

        #self._trace( f"Release status after S1ON: {hex(self._get_release_status())}" )
        if not self._retry_api_call( lambda: (self._get_release_status() & s1on_status == s1on_status),
                                     retry_interval=self._COMMAND_RETRY_INTERVAL, retry_count=self._COMMAND_RETRY_COUNT ):
            self._release_mode( XSDK_RELEASE_N_S1OFF )
            self._print( "Image shot error, S1ON not completed." )
            return False
        self._trace( f"Release status ready : {hex(s1on_status)}" )

        if not self._retry_api_call( lambda: self._release_mode( XSDK_RELEASE_S2_S1OFF ),
                                     retry_interval=self._RELEASE_RETRY_INTERVAL, retry_count=self._RELEASE_RETRY_COUNT ):
            self._print( "Image shot error, S2_S1OFF failed after retries." )
            self._release_mode( XSDK_RELEASE_N_S1OFF )  # cancel S1 if S2 failed
            return False

        self._trace( "Image shot successfully." )
        return True
    
    def _wait_for_image_ready(self, max_wait_seconds=0, allow_timeout=False) -> bool:
        # check more frequently for shorter wait time, and less frequently for longer wait time
        if max_wait_seconds <= 0:
            max_wait_seconds = self._CAPTURE_COMPLETION_TIMEOUT
        check_interval = 0.1 if max_wait_seconds < 60 else 1.0
        check_count = int( max_wait_seconds / check_interval ) 
        if max_wait_seconds > 60:   # trace for debugging long wait times
            self._trace( f"Waiting for image buffer : max {max_wait_seconds}sec, interval {check_interval}sec, max count {check_count}" )
        # wait until image is ready in camera buffer
        if not self._retry_api_call( lambda: (self._get_buffer_capacity()[0] > 0),
                                    retry_interval=check_interval, retry_count=check_count, allow_timeout=allow_timeout ):
            # cancel any remaining release state and delete image if image is not ready after waiting
            self._reset_release_status()
            time.sleep(1)
            self._delete_image()
            return False
        return True

    def _files_per_shot(self) -> int:
        # get number of files per shot, e.g., 1 for JPEG only, 2 for RAW+JPEG
        iqmode = self._get_prop(API_CODE.API_CODE_GetImageQuality)
        if iqmode is not None and iqmode in [XSDK_IMAGEQUALITY_RAW_NORMAL, XSDK_IMAGEQUALITY_RAW_FINE, XSDK_IMAGEQUALITY_RAW_SUPERFINE ]:
                return 2
        return 1

    # Read Full Image from camera
    def _get_image(self) -> tuple[Optional[bytes], Optional[str]]:
        # read image info in camera buffer
        image_info = ImageInformation()
        res = self._lib.m_pfnReadImageInfo(self._camera_handle, byref(image_info))

        # check if image info is valid
        #height   = image_info.image_pix_height  #  always 0
        #width    = image_info.image_pix_width
        data_size = image_info.data_size
        format    = image_info.format & XSDK_IMAGEFORMAT_MASK
        if res != XSDK_COMPLETE or data_size == 0 or format == XSDK_IMAGEFORMAT_NONE:
            self._print( f"ReadImageInfo error: res, {res}, data_size: {data_size}, format: {format}" )
            return (None, None)

        # extract file name 
        file_name = image_info.internal_name.decode("utf-8").rstrip('\x00') or "unknown.dat"
        # self._trace( f"Image Info - size: {data_size}, format: {format}, internal_name: {file_name}" )
        file_type = file_name[-4:] if len(file_name) >= 4 else ".dat"
        # file_type = ".jpg" if format == XSDK_IMAGEFORMAT_JPEG else ".raf" if format == XSDK_IMAGEFORMAT_RAW else ".dat"

        # read image data from camera
        data = create_string_buffer(data_size)
        if( self._lib.m_pfnReadImage(self._camera_handle, byref(data), c_long(data_size)) != XSDK_COMPLETE ):
            return (None, None)

        # success
        return (bytes(data), file_type)
    
    # Read Preview Image from camera
    def _get_preview_image(self) -> tuple[Optional[bytes], Optional[str]]:
        image_info = ImageInformation()
        res = self._lib.m_pfnReadImageInfo(self._camera_handle, byref(image_info))
        prev_size = image_info.preview_size
        format = image_info.format & XSDK_IMAGEFORMAT_MASK
        if res != XSDK_COMPLETE or prev_size == 0 or format == XSDK_IMAGEFORMAT_NONE:
            self._print( f"ReadImageInfo error: {res}, preview_size: {prev_size}, format: {format}" )
            return (None, None)

        # read preview image data from camera
        data = create_string_buffer(prev_size)
        if( self._lib.m_pfnReadPreview(self._camera_handle, byref(data), c_long(prev_size)) != XSDK_COMPLETE ):
            return (None, None)
        # success
        return (bytes(data), "preview_image.jpg")
    
    # Delete image from camera buffer
    def _delete_image(self) -> bool:
        # clear any remaining image in camera buffer
        count, total = self._get_buffer_capacity()
        while count>0:
            if self._lib.m_pfnDeleteImage(self._camera_handle) == XSDK_COMPLETE:
                self._trace( f"DeleteImage ... {count}/{total}" )
                count -= 1
            else:
                self._load_error_code()
                self._print( f"DeleteImage failed with {self._get_error_string()}" )
                break
        return True

    # ---------------------------------------------- 
    # Camera Settings (basic functionality)
    #  - Program AE Modes, Exposure Compensation, Aperture, Shutter Speed, ISO Sensitivity
    # ---------------------------------------------- 
    #
    # Program AE Modes P/S/A/M dial
    #  - get options, set value, get value
    #
    def get_program_mode_options(self) -> APIResponseList:
        """ Get the available program AE mode options for the camera.
            Camera must be set to 'P' mode befor connection, otherwise the program mode options will be restricted.
            The options values are defined in the FUJIFILM Camera Control SDK documentation, and can be used to set the program mode using set_program_mode().
        """
        # get number of options
        num_program_mode = c_long(0)
        if( self._lib.m_pfnCapAEMode(self._camera_handle, byref(num_program_mode), None) != XSDK_COMPLETE ):
            self._print( "Failed to get number of program mode options." )
            return self._api_error_list()

        # get option values
        value_list = (c_long * num_program_mode.value)()
        if( self._lib.m_pfnCapAEMode(self._camera_handle, byref(num_program_mode), value_list)!= XSDK_COMPLETE ):
            return self._api_error_list()
        
        # build options list
        program_mode_list = [ value_list[i] for i in range(num_program_mode.value) ]
        return self._api_success_list( options=program_mode_list )

    def set_program_mode(self, program_mode) -> APIResponse:
        """ Set the program AE mode for the camera.
            The program_mode parameter should be one of the available options obtained from get_program_mode_options().
        """
        self._trace( f"Setting program mode to {program_mode}" )
        success = self._retry_api_call( lambda: self._lib.m_pfnSetAEMode(self._camera_handle, c_long(program_mode))==XSDK_COMPLETE or self._load_error_code(),
                                        retry_interval=self._COMMAND_RETRY_INTERVAL, retry_count=self._COMMAND_RETRY_COUNT )
        return self._api_success() if success else self._api_error()

    def get_program_mode(self) -> APIResponseValue:
        """ Get the current program AE mode of the camera.
        """
        program_mode = c_long(0)
        if( self._lib.m_pfnGetAEMode(self._camera_handle, byref(program_mode)) != XSDK_COMPLETE ):
            return self._api_error_value()
        return self._api_success_value( program_mode.value )
    #
    # Exposure Compensation
    #  - get options, set value, get value
    #
    def get_exposure_compensation_options(self) -> APIResponseList:
        """ Get the available exposure compensation options for the camera.
            The options values are defined in the FUJIFILM Camera Control SDK documentation, and can be used to set the exposure compensation using set_exposure_compensation().
        """
        # get number of options
        num_exposure_compensation = c_long(0)
        if( self._lib.m_pfnCapExposureBias(self._camera_handle, byref(num_exposure_compensation), None) != XSDK_COMPLETE ):
            return self._api_error_list()

        # get option values
        value_list = (c_long * num_exposure_compensation.value)() 
        if( self._lib.m_pfnCapExposureBias(self._camera_handle, byref(num_exposure_compensation), value_list) != XSDK_COMPLETE ):
            return self._api_error_list()

        # build options list
        exposure_compensation_list = [ value_list[i] for i in range(num_exposure_compensation.value) ]
        return self._api_success_list( exposure_compensation_list )
    
    def set_exposure_compensation(self, exposure_compensation) -> APIResponse:
        """ Set the exposure compensation for the camera.
            The exposure_compensation parameter should be one of the available options obtained from get_exposure_compensation_options().
        """
        self._trace( f"Setting exposure compensation to {exposure_compensation}" )
        success = self._retry_api_call( lambda: self._lib.m_pfnSetExposureBias(self._camera_handle, c_long(exposure_compensation))==XSDK_COMPLETE or self._load_error_code(),
                                        retry_interval=self._COMMAND_RETRY_INTERVAL, retry_count=self._COMMAND_RETRY_COUNT )
        return self._api_success() if success else self._api_error()
    
    def get_exposure_compensation(self) -> APIResponseValue:
        """ Get the current exposure compensation of the camera.
        """
        exposure_compensation = c_long(0)
        if( self._lib.m_pfnGetExposureBias(self._camera_handle, byref(exposure_compensation)) != XSDK_COMPLETE ):
            return self._api_error_value()
        return self._api_success_value( exposure_compensation.value )
    #
    # Aperture Value
    #  - get options, set value, get value
    #
    def get_aperture_value_options(self) -> APIResponseList:
        """ Get the available aperture value options for the camera.
            The options values are defined in the FUJIFILM Camera Control SDK documentation, and can be used to set the aperture value using set_aperture_value().
            Note:
            - Aperture values are only changeable when the program AE mode is set to A (Aperture Priority) or M (Manual), so this function should be used after setting the program mode to A or M.
            - The available aperture values depend on the current zoom position of the lens, so this function should be used after the zoom position has changed.
        """
        # get lens position ( option depends on zoom position )
        lens_position = c_long(0)
        if self._lib.m_pfnGetLensZoomPos(self._camera_handle, byref(lens_position)) != XSDK_COMPLETE:
            return self._api_error_list()

        # get number of options
        num_aperture_value = c_long(0)
        if self._lib.m_pfnCapAperture(self._camera_handle, c_long(lens_position.value), byref(num_aperture_value), None) != XSDK_COMPLETE:
            return self._api_error_list()

        # get option values
        value_list = (c_long * num_aperture_value.value)()
        if self._lib.m_pfnCapAperture(self._camera_handle, c_long(lens_position.value), byref(num_aperture_value), value_list) != XSDK_COMPLETE:
            return self._api_error_list()

        # build options list
        aperture_value_list = [ value_list[i] for i in range(num_aperture_value.value) ]
        return self._api_success_list( aperture_value_list, is_reactive=True, is_volatile=True ) #  if self._lens_zoom_capability==0 ?

    def set_aperture_value(self, aperture_value) -> APIResponse:
        """ Set the aperture value for the camera.
            The aperture_value parameter should be one of the available options obtained from get_aperture_value_options().
        """
        self._trace( f"Setting aperture value to {aperture_value}" )
        success = self._retry_api_call( lambda: self._lib.m_pfnSetAperture(self._camera_handle, c_long(aperture_value))==XSDK_COMPLETE or self._load_error_code(),
                                        retry_interval=self._COMMAND_RETRY_INTERVAL, retry_count=self._COMMAND_RETRY_COUNT )
        return self._api_success() if success else self._api_error()
    
    def get_aperture_value(self) -> APIResponseValue:
        """ Get the current aperture value of the camera.
            The returned value is one of the available options obtained from get_aperture_value_options().
        """
        aperture_value = c_long(0)
        if( self._lib.m_pfnGetAperture(self._camera_handle, byref(aperture_value)) != XSDK_COMPLETE ):
            return self._api_error_value()
        return self._api_success_value( aperture_value.value )
    #
    # Shutter Speed
    #  - get options, set value, get value
    #
    def get_shutter_speed_options(self) -> APIResponseList:
        """ Get the available shutter speed options for the camera.
            The options values are defined in the FUJIFILM Camera Control SDK documentation, and can be used to set the shutter speed using set_shutter_speed().
            Note:
            - Shutter speed values are only changeable when the program AE mode is set to S (Shutter Priority) or M (Manual), so this function should be used after setting the program mode to S or M.
        """
        # get number of options
        num_shutter_speed = c_long(0)
        blub_capability = c_long(0)
        if self._lib.m_pfnCapShutterSpeed(self._camera_handle, byref(num_shutter_speed), None, None) != XSDK_COMPLETE:
            return self._api_error_list()
        
        # get option values
        value_list = (c_long * num_shutter_speed.value)()
        if self._lib.m_pfnCapShutterSpeed(self._camera_handle, byref(num_shutter_speed), value_list, byref(blub_capability)) != XSDK_COMPLETE:
            return self._api_error_list()

        # build options list
        shutter_speed_list = [ value_list[i] for i in range(num_shutter_speed.value) ]
        # if bulb_capability == 1 then shutter_speed_list[].append(XSDK_SHUTTER_SPEED_BULB) <- already included  
        return self._api_success_list( shutter_speed_list, is_reactive=True, is_volatile=False ) 

    def set_shutter_speed(self, shutter_speed=0) -> APIResponse:
        """ Set the shutter speed for the camera.
            The shutter_speed parameter should be one of the available options obtained from get_shutter_speed_options().
        """
        self._trace( f"Setting shutter speed to {shutter_speed}" )
        bulb_mode = 0 if shutter_speed != XSDK_SHUTTER_SPEED_BULB else 1
        success = self._retry_api_call( lambda: self._lib.m_pfnSetShutterSpeed(self._camera_handle, c_long(shutter_speed), c_long(bulb_mode))==XSDK_COMPLETE or self._load_error_code(),
                                        retry_interval=self._COMMAND_RETRY_INTERVAL, retry_count=self._COMMAND_RETRY_COUNT )
        return self._api_success() if success else self._api_error()

    def get_shutter_speed(self) -> APIResponseValue:
        """ Get the current shutter speed of the camera.
            The returned value is one of the available options obtained from get_shutter_speed_options(),
        """
        shutter_speed = c_long(0)
        bulb_mode = c_long(0)
        if( self._lib.m_pfnGetShutterSpeed(self._camera_handle, byref(shutter_speed), byref(bulb_mode)) != XSDK_COMPLETE ):
            return self._api_error_value()
        ss_value = shutter_speed.value if bulb_mode.value == 0 else XSDK_SHUTTER_SPEED_BULB
        # shutter_speed value includes bulb mode in this implementation
        return self._api_success_value( ss_value )
    #
    # ISO Sensitivity
    #  - get options, set value, get value
    #
    def get_iso_sensitivity_options(self) -> APIResponseList:
        """ Get the available ISO sensitivity options for the camera.
            The options values are defined in the FUJIFILM Camera Control SDK documentation, and can be used to set the ISO sensitivity using set_iso_sensitivity().
        """
        # get number of options
        num_iso_sensitivity = c_long(0)
        if self._lib.m_pfnCapSensitivity(self._camera_handle, byref(num_iso_sensitivity), None) != XSDK_COMPLETE:
            return self._api_error_list()
        
        # get option values
        value_list = (c_long * num_iso_sensitivity.value)()
        if self._lib.m_pfnCapSensitivity(self._camera_handle, byref(num_iso_sensitivity), value_list) != XSDK_COMPLETE:
            return self._api_error_list()
        
        # build options list
        iso_sensitivity_list = [ value_list[i] for i in range(num_iso_sensitivity.value) ]
        return self._api_success_list( iso_sensitivity_list )

    def set_iso_sensitivity(self, iso_sensitivity) -> APIResponse:
        """ Set the ISO sensitivity for the camera.
            The iso_sensitivity parameter should be one of the available options obtained from get_iso_sensitivity_options().
        """
        self._trace( f"Setting ISO sensitivity to {iso_sensitivity}" )
        success = self._retry_api_call( lambda: self._lib.m_pfnSetSensitivity(self._camera_handle, c_long(iso_sensitivity))==XSDK_COMPLETE or self._load_error_code(),
                                        retry_interval=self._COMMAND_RETRY_INTERVAL, retry_count=self._COMMAND_RETRY_COUNT )
        return self._api_success() if success else self._api_error()
    
    def get_iso_sensitivity(self) -> APIResponseValue:
        """ Get the current ISO sensitivity of the camera.
            The returned value is one of the available options obtained from get_iso_sensitivity_options().
        """
        iso_sensitivity = c_long(0)
        if( self._lib.m_pfnGetSensitivity(self._camera_handle, byref(iso_sensitivity)) != XSDK_COMPLETE ):
            return self._api_error_value()
        return self._api_success_value( iso_sensitivity.value )

    # ZoomLens (focus)
    def get_lens_zoom_capability(self) -> APIResponseDict:
        """ Get the available positions (focal length) of the zoomable lens for the camera.
            returns a dictionary containing available zoom positions and their corresponding actual and 35mm equivalent focal lengths.
        """
        # get number of options
        num_zoom_positions = c_long(0)
        if self._lib.m_pfnCapLensZoomPos(self._camera_handle, byref(num_zoom_positions), None,None,None) != XSDK_COMPLETE:
            return self._api_error_dict()
        
        # get option values
        value_list = (c_long * num_zoom_positions.value)()
        actual_list = (c_long * num_zoom_positions.value)()
        equiv35_list = (c_long * num_zoom_positions.value)()
        if self._lib.m_pfnCapLensZoomPos(self._camera_handle, byref(num_zoom_positions), value_list, actual_list, equiv35_list) != XSDK_COMPLETE:
            return self._api_error_dict()
        
        # build options list
        zoom_position_dict = {
            "ability": self._lens_zoom_capability,
            "options": [ value_list[i] for i in range(num_zoom_positions.value) ],
            # conversion list for position to actual focal length, 35mm equivalent focal length
            "actual_length": [ actual_list[i] for i in range(num_zoom_positions.value) ],
            "equiv35_length": [ equiv35_list[i] for i in range(num_zoom_positions.value) ]
        }
        return self._api_success_dict( zoom_position_dict )

    def get_lens_zoom(self) -> APIResponseValue:
        """ Get the current zoom lens position (focal length) of the camera.
        """
        zoom_position = c_long(0)
        if self._lib.m_pfnGetLensZoomPos(self._camera_handle, byref(zoom_position)) != XSDK_COMPLETE:
            return self._api_error_value()
        return self._api_success_value( zoom_position.value )

    def set_lens_zoom(self, zoom_position) -> APIResponse:
        """ Set the zoom lens position (focal length) for the camera.
            Available options can be obtained from get_zoom_position_capability().
            The zoom_position parameter should be one of the available options.
        """
        self._trace( f"Setting zoom position to {zoom_position}" )
        success = self._retry_api_call( lambda: self._lib.m_pfnSetLensZoomPos(self._camera_handle, c_long(zoom_position))==XSDK_COMPLETE or self._load_error_code(),
                                        retry_interval=self._COMMAND_RETRY_INTERVAL, retry_count=self._COMMAND_RETRY_COUNT )
        return self._api_success() if success else self._api_error()

    # Drive mode (single, continuous, bracketing, etc.)
    def get_drive_mode_options(self) -> APIResponseList:
        """ Get the available drive mode options for the camera.
            The options values are defined in the FUJIFILM Camera Control SDK documentation, and can be used to set the drive mode using set_drive_mode().
        """
        # get number of options
        num_drive_mode = c_long(0)
        if self._lib.m_pfnCapDriveMode(self._camera_handle, byref(num_drive_mode), None) != XSDK_COMPLETE:
            return self._api_error_list()
        
        # get option values
        value_list = (c_long * num_drive_mode.value)()
        if self._lib.m_pfnCapDriveMode(self._camera_handle, byref(num_drive_mode), value_list) != XSDK_COMPLETE:
            return self._api_error_list()
        
        # build options list
        drive_mode_list = [ value_list[i] for i in range(num_drive_mode.value) ]
        return self._api_success_list( drive_mode_list )
    
    def set_drive_mode(self, drive_mode) -> APIResponse:
        """ Set the drive mode for the camera.
            The drive_mode parameter should be one of the available options obtained from get_drive_mode_options().
        """
        self._trace( f"Setting drive mode to {drive_mode}" )
        success = self._retry_api_call( lambda: self._lib.m_pfnSetDriveMode(self._camera_handle, c_long(drive_mode))==XSDK_COMPLETE or self._load_error_code(),
                                        retry_interval=self._COMMAND_RETRY_INTERVAL, retry_count=self._COMMAND_RETRY_COUNT )
        return self._api_success() if success else self._api_error()
    
    def get_drive_mode(self) -> APIResponseValue:
        """ Get the current drive mode of the camera.
            The returned value is one of the available options obtained from get_drive_mode_options().
        """
        drive_mode = c_long(0)
        if( self._lib.m_pfnGetDriveMode(self._camera_handle, byref(drive_mode)) != XSDK_COMPLETE ):
            return self._api_error_value()
        return self._api_success_value( drive_mode.value )

    # ----------------------------------------------
    # Model dependent controlls (more functionality)
    # ----------------------------------------------
    # Property Control by cap/set/get property with 0, 1 or 2 parameters
    def _cap_prop(self, api_code, param1=None) -> list[int]:
        num_options = c_long(0)
        # query options with no additional parameters
        if param1 is None:
            self._trace(f"Querying capability {api_code.value} with no additional parameters")
            # get number of options
            if self._lib.m_pfnCapProp(self._camera_handle, api_code.value, 2, byref(num_options), None) == XSDK_COMPLETE:
                # get option values
                value_list = (c_long * num_options.value)()
                if self._lib.m_pfnCapProp(self._camera_handle, api_code.value, 2, byref(num_options), value_list) == XSDK_COMPLETE:
                    # build options list
                    return [ int(value_list[i]) for i in range(num_options.value) ]
        # query options with an additional parameter
        else:
            self._trace(f"Querying capability {api_code.value} with additional parameter {param1}")
            # get number of options
            if self._lib.m_pfnCapProp(self._camera_handle, api_code.value, 3, param1, byref(num_options), None ) == XSDK_COMPLETE:
                # get option values
                value_list = (c_long * num_options.value)()
                if self._lib.m_pfnCapProp(self._camera_handle, api_code.value, 3, param1, byref(num_options), value_list) == XSDK_COMPLETE:
                    # build options list
                    return [ int(value_list[i]) for i in range(num_options.value) ]
        # if any of the above calls fail, return empty list
        self._load_error_code()
        return []

    def _set_prop(self, api_code, value1=None, value2=None) -> bool:
        # two additional parameters available for SetProp 
        if value1 is None:
            api_call = lambda: self._lib.m_pfnSetProp(self._camera_handle, api_code.value, 0, 0)==XSDK_COMPLETE or self._load_error_code()
        elif value2 is None:
            api_call = lambda: self._lib.m_pfnSetProp(self._camera_handle, api_code.value, 1, value1)==XSDK_COMPLETE or self._load_error_code()
        else:
            api_call = lambda: self._lib.m_pfnSetProp(self._camera_handle, api_code.value, 2, value1, c_long(value2))==XSDK_COMPLETE or self._load_error_code()
        if self._retry_api_call( api_call, retry_interval=self._COMMAND_RETRY_INTERVAL, retry_count=self._COMMAND_RETRY_COUNT ):
            # success
            return True
        # failed to set property
        return False

    def _get_prop(self, api_code, param1=None) -> Optional[int]:
        value1 = c_long(0)
        # get property value with no additional parameters
        if param1 is None:
            self._trace(f"Getting property {api_code.name}")
            if self._retry_api_call( lambda: self._lib.m_pfnGetProp(self._camera_handle, api_code.value, 1, byref(value1) ) == XSDK_COMPLETE or self._load_error_code(),
                                    retry_interval=self._COMMAND_RETRY_INTERVAL, retry_count=self._COMMAND_RETRY_COUNT ):
                return value1.value
        # get property value with an additional parameter
        else:
            self._trace(f"Getting property {api_code.name} with param1={param1}")
            if self._retry_api_call( lambda: self._lib.m_pfnGetProp(self._camera_handle, api_code.value, 2, param1, byref(value1) ) == XSDK_COMPLETE or self._load_error_code(),
                                    retry_interval=self._COMMAND_RETRY_INTERVAL, retry_count=self._COMMAND_RETRY_COUNT ):
                return value1.value
        # failed to get property value
        return None

    # following settings can be implemented similarly using _set_prop and _get_prop functions according to the API documentation
    # Some options have to be set up on camera side before connecting to this API, such as:
    # - Image processing detail
    #       White Balance, Film Simulation, Dynamic Range, Highlight/Shadow Tone, Color, Sharpness, Noise Reduction, ...
    # - AE/AF detail settings 
    #       AE Metering mode, AF Mode with Face Detection,...

    # Focus Area functions (controll focus area on the screen and focus area size)
    def get_focus_area_options(self, cap_inspection=False) -> APIResponseDict:
        """ Get the available focus area options for the camera.
            If capability query is not supported by the target model, this function returns fullrange options list based on the maximum focus points.
            When cap_inspection flag is set to True, the function will try to inspect the available options by testing set_foucs_area(), which is less efficient but can provide more accurate options.
            Refer the FUJIFILM Camera Control SDK documentation for the options which can be used for setting focus area.
            Note:
            - The available focus area options depend on the camera model and current focus mode, so this function should be used after focus mode has been changed.
        """
        # get max focus points supported by camera, which can be used as reference to determine the range of focus area settings
        aspect_selector = self._get_prop(API_CODE.API_CODE_GetFocusPoints) or XSDK_FOCUS_POINTS_13X7  # 0x0001 minimum points
        h_points, v_points = FOCUS_POINTS_ASPECTS[aspect_selector]

        # get focus area capability
        direction = 0
        focus_area_min = FocusArea(0, 0, 0)
        focus_area_max = FocusArea(0, 0, 0)
        if self._lib.m_pfnCapProp(self._camera_handle, API_CODE.API_CODE_CapFocusArea.value, 3, c_long(direction), byref(focus_area_min), byref(focus_area_max)) != XSDK_COMPLETE:
            # In this case, the target models do not support CapFocusArea API
            self._trace("CapFocusArea not supported, using assertive default focus area settings.")

            # separate handling based on AFMode
            focus_mode = self._get_prop(API_CODE.API_CODE_GetFocusMode)
            if focus_mode is None:
                return self._api_error_dict( "GetFocusMode failed, cannot proceed configuration." )

            size_range_single = [1, 6]
            size_range_zone  = [17, 20]

            # focus_mode が MF なら focus_areaのh,v,size はfullrangeになる
            if focus_mode == XSDK_FOCUS_MANUAL:
                self._trace("Focus mode is MF, using full range for focus area.")
                focus_area_min = FocusArea(-h_points//2, -v_points//2, size_range_single[0])
                focus_area_max = FocusArea(h_points//2, v_points//2, size_range_single[1])

            # focus_mode が AF なら focus_areaのh,v,size は AFMode に依存する
            else:
                af_mode = self._get_prop(API_CODE.API_CODE_GetAFMode, 0)
                if af_mode == None:
                    return self._api_error_dict( "GetAFMode failed, cannot proceed configuration." )
                self._trace(f"Focus mode is AF, AFmode = {af_mode}")

                # WIDETRACKING and ALL(AUTO) mode have no options for focus area from API
                if af_mode == XSDK_AFMODE_WIDETRACKING or af_mode == XSDK_AFMODE_ALL:
                    self._trace("AFMode is WIDETRACKING or ALL(AUTO), no focus area options available.")

                # SINGLE and ZONE mode have focus area options based on current focus area size
                elif af_mode == XSDK_AFMODE_SINGLE or af_mode == XSDK_AFMODE_ZONE:
                    direction = 0
                    focus_area = FocusArea(0, 0, 0)
                    if( self._lib.m_pfnGetProp(self._camera_handle, API_CODE.API_CODE_GetFocusArea.value, 2, c_long(direction), byref(focus_area)) != XSDK_COMPLETE ):
                        return self._api_error_dict( "GetFocusArea failed, cannot proceed configuration." )

                    # initialize focus area baseline with current value 
                    size_min = size_range_single[0] if af_mode == XSDK_AFMODE_SINGLE else size_range_zone[0]
                    size_max = size_range_single[1] if af_mode == XSDK_AFMODE_SINGLE else size_range_zone[1]
                
                    if not cap_inspection:
                        focus_area_min = FocusArea( -(h_points//2), -(v_points//2), size_min )
                        focus_area_max = FocusArea( h_points//2, v_points//2, size_max )
                    else:
                        # Inspecting supported options manually by testing set focus area whether it succeeds or not.
                        focus_area_min.size = min(size_min, focus_area.size)
                        focus_area_max.size = max(size_max, focus_area.size)
                        self._trace( "FocusArea capability list not supported in this model, then inspecting available options..." )
                        for h in range(0, h_points//2 + 1):   # only need to test half of the points since the options should be symmetric for positive and negative values
                            if self.set_focus_area(h, 0, focus_area.size).success:
                                #self._trace( f"Focus Area Horizontal option supported: {-h} to {h}" )
                                focus_area_min.h = min(focus_area_min.h, -h)
                                focus_area_max.h = max(focus_area_max.h, h)
                        for v in range(0, v_points//2 + 1):   # only need to test half of the points since the options should be symmetric for positive and negative values
                            if self.set_focus_area(0, v, focus_area.size).success:
                                #self._trace( f"Focus Area Vertical option supported: {-v} to {v}" )
                                focus_area_min.v = min(focus_area_min.v, -v)
                                focus_area_max.v = max(focus_area_max.v, v)
                        # restore previous focus area
                        self._lib.m_pfnSetProp(self._camera_handle, API_CODE.API_CODE_SetFocusArea.value, 2, c_long(direction), byref(focus_area))

        area_options = {
            "h": [h for h in range(focus_area_min.h, focus_area_max.h+1)],
            "v": [v for v in range(focus_area_min.v, focus_area_max.v+1)],
            "size": [s for s in range(focus_area_min.size, focus_area_max.size+1)],
            "points": (h_points, v_points),
            "is_reactive": True,   # options may change depending on focus mode and other settings
            "is_volatile": False,  # options not changed by camera side without API call
        }
        self._trace( "FocusArea Options:", area_options )
        return self._api_success_dict( area_options )  # options may change depending on focus mode and other settings

    # get or set focus area settings (h, v, size)
    #  h and v are relative coordinates to the center of the screen, with negative values indicating left/down and positive values indicating right/up.
    #  size is an arbitrary unit representing the size of the focus area, with larger values indicating a larger area.
    def get_focus_area(self) -> APIResponseDict:
        """ Get the current focus area settings of the camera, including horizontal and vertical offsets and size.
            The returned values are based on the current focus area settings of the camera, and the range of the values can be determined by get_focus_area_options().
        """
        direction = 0
        focus_area = FocusArea(0, 0, 0)
        if( self._lib.m_pfnGetProp(self._camera_handle, API_CODE.API_CODE_GetFocusArea.value, 2, c_long(direction), byref(focus_area)) != XSDK_COMPLETE ):
            return self._api_error_dict()
        return self._api_success_dict( { "h": focus_area.h, "v": focus_area.v, "size": focus_area.size } )

    def set_focus_area(self, h=None, v=None, size=None) -> APIResponse:
        """ Set the focus area settings of the camera, including horizontal and vertical offsets and size.
            The values should be within the range returned by get_focus_area_options().
        """
        # get current focus area for default values if any of the parameters is not specified
        if h is None or v is None or size is None:
            direction = 0
            focus_area = FocusArea(0, 0, 0)
            if( self._lib.m_pfnGetProp(self._camera_handle, API_CODE.API_CODE_GetFocusArea.value, 2, c_long(direction), byref(focus_area)) != XSDK_COMPLETE ):
                return self._api_error()
            # update focus area values
            if h is None:
                h = focus_area.h
            if v is None:
                v = focus_area.v
            if size is None:
                size = focus_area.size

        # Set the focus area with retry mechanism to ensure the camera accepts the new settings.
        if self._retry_api_call(
            lambda: self._lib.m_pfnSetProp(self._camera_handle, API_CODE.API_CODE_SetFocusArea.value, 2, c_long(0), byref(FocusArea(h, v, size))) == XSDK_COMPLETE or self._load_error_code(),
            retry_interval=self._COMMAND_RETRY_INTERVAL,
            retry_count=self._COMMAND_RETRY_COUNT ) == False:
            return self._api_error()
        return self._api_success()

    # ThrougImage zoom
    def get_finder_crop_options(self) -> APIResponseList:
        """ Get available ThroughImage zoom (Digital Cropped live view) options for the camera.
            The options values can be used to set the digital zoom using set_finder_crop().
            Note:
            - Digital Cropping is only available in 2 cases (1. MF mode, 2. AF-S mode and SINGLE POINT AF without PreAF)
            - The options depend on the camera model and current focus mode above, so this function should be used after focus mode has been changed properly.
        """
        # get through image zoom options / model dependent
        zoom_list = self._cap_prop(API_CODE.API_CODE_CapThroughImageZoom)
        # set default zoom options if query failed, since some models do not support capability query properly
        if len(zoom_list) == 0: 
            # liveview zoom option is available only when AF SINGLE mode without PreAF, or MANUAL focus mode
            focus_mode = self._get_prop(API_CODE.API_CODE_GetFocusMode)
            if focus_mode == XSDK_FOCUS_MANUAL or \
               (focus_mode == XSDK_FOCUS_AFS and self._get_prop(API_CODE.API_CODE_GetAFMode, 0) ==  XSDK_AFMODE_SINGLE and self._get_prop(API_CODE.API_CODE_GetPreAFMode) ==  XSDK_OFF):
                # set default zoom options based on camera name
                if self._camera_name.find("GFX") >= 0:
                    zoom_list = [ XSDK_THROUGHIMAGE_ZOOM_10, XSDK_THROUGHIMAGE_ZOOM_20, XSDK_THROUGHIMAGE_ZOOM_40 ]
                else:
                    zoom_list = [ XSDK_THROUGHIMAGE_ZOOM_10, XSDK_THROUGHIMAGE_ZOOM_25, XSDK_THROUGHIMAGE_ZOOM_60 ]
                # Inspection actual capability using set/get property is not work properly for some models,
                #  since they may return XSDK_COMPLETE for unsupported zoom rates, so we will just use the default zoom options without verification
                #for zoom_rate in temp_list:
                #    if self._set_prop(API_CODE.API_CODE_SetThroughImageZoom, zoom_rate) and \
                #        self._get_prop(API_CODE.API_CODE_GetThroughImageZoom) == zoom_rate:
                #        zoom_list.append( zoom_rate )
                #zoom_list.reverse()
            else:
                # liveview zoom is not available in this case
                zoom_list = [ XSDK_THROUGHIMAGE_ZOOM_10 ]
        # build options list
        return self._api_success_list( zoom_list, is_reactive=True, is_volatile=False )  # options depend on focus mode and other settings, but not changed by camera side without API call

    def set_finder_crop(self, zoom_rate) -> APIResponse:
        """ Set the ThroughImage zoom (Digital Cropped live view) for the camera to assist focusing.
            This effectively crops the image to the focused area and enlarges it to fill the finder, and the zoomed view is only for preview and will not affect the captured image.
            The zoom_rate parameter should be one of the available options obtained from get_finder_crop_options().
            Note:
            - ThroughImage zoom is only available in 2 cases (1. focus mode MANUAL, 2. focus mode AF-S and SINGLE POINT AF without PreAF), so if the camera is not in one of these modes, setting zoom will fail.
        """
        self._trace( f"Setting ThroughImage zoom (Digital Crop) to {zoom_rate}" )
        success = self._set_prop(API_CODE.API_CODE_SetThroughImageZoom, zoom_rate)
        return self._api_success() if success else self._api_error()
    
    def get_finder_crop(self) -> APIResponseValue:
        """ Get the current ThroughImage zoom (Digital Cropped live view) setting for the camera.
            The returned zoom_rate value is one of the available options obtained from get_finder_crop_options().
        """
        zoom_rate = self._get_prop(API_CODE.API_CODE_GetThroughImageZoom)
        if zoom_rate is None:
            return self._api_error_value()
        return self._api_success_value( zoom_rate )

    # get AF mode options / model dependent
    def get_focus_mode_options(self) -> APIResponseList:
        """ Get the available focus mode options for the camera.
            The options values are defined in the FUJIFILM Camera Control SDK documentation, and can be used to set the focus mode using set_focus_mode().
        """
        focus_mode_list = self._cap_prop(API_CODE.API_CODE_CapFocusMode)
        if len(focus_mode_list) == 0:
            # standard focus mode options for all models
            focus_mode_list = [ XSDK_FOCUS_MANUAL, XSDK_FOCUS_AFC, XSDK_FOCUS_AFS ]
        return self._api_success_list( focus_mode_list )

    def get_focus_mode(self) -> APIResponseValue:
        """ Get the current focus mode of the camera
            The focus_mode value is one of the available options obtained from get_focus_mode_options().
            pre_af activity in AF-S/AF-C can be checked by get_status() function.
        """
        focus_mode = self._get_prop(API_CODE.API_CODE_GetFocusMode)
        return self._api_success_value( focus_mode ) if focus_mode is not None else self._api_error_value()

    # focus mode MANUAL, AF-S, AF-C can be set by this function, and PreAF can be enabled/disabled together with AF-S/AF-C mode since PreAF is only effective in AF-S/AF-C mode.
    def set_focus_mode(self, focus_mode, pre_af=None) -> APIResponse:
        """ Set the focus mode for the camera, including PreAF mode.
             The focus_mode parameter should be one of the available options obtained from get_focus_mode_options(), and the pre_af parameter indicates whether to enable PreAF mode or not.
             PreAF is only effective in AF-S/AF-C mode. If PreAF is not indicated, PreAF keeps the previous status. 
        """
        self._trace( f"Setting focus mode to {focus_mode}, PreAF={pre_af}" )
        if self._set_prop(API_CODE.API_CODE_SetFocusMode, focus_mode) == False:
            return self._api_error()
        if focus_mode == XSDK_FOCUS_MANUAL or pre_af is None:
            return self._api_success()
        # pre AF mode is only effective when AF mode is AF-S or AF-C, so we only set preAF mode when focus mode is AF-S or AF-C, otherwise we will ignore preAF parameter even if it's specified by caller
        pre_af_mode = XSDK_ON if pre_af else XSDK_OFF
        if self._set_prop(API_CODE.API_CODE_SetPreAFMode, pre_af_mode) == False:
            return self._api_error()
        return self._api_success()
    
    def get_focus_afmode_options(self) -> APIResponseList:
        """ Get the available AF mode options for the current focus mode.
            The options values are defined in the FUJIFILM Camera Control SDK documentation.
        """
        afmode_list = self._cap_prop(API_CODE.API_CODE_CapAFMode)
        if len(afmode_list) == 0:
            afmode_list = [XSDK_AFMODE_SINGLE, XSDK_AFMODE_ZONE, XSDK_AFMODE_WIDETRACKING]
        return self._api_success_list(afmode_list)

    def get_focus_afmode(self) -> APIResponseValue:
        """ Get the current AF mode for the camera.
            The returned value is one of the available options obtained from get_focus_afmode_options().
        """
        afmode = self._get_prop(API_CODE.API_CODE_GetAFMode, 0)
        if afmode is None:
            return self._api_error_value()
        return self._api_success_value(afmode)

    def set_focus_afmode(self, afmode) -> APIResponse:
        """ Set the AF mode for the camera.
            The afmode parameter should be one of the available options obtained from get_focus_afmode_options().
        """
        self._trace( f"Setting AF mode to {hex(afmode)}" )
        if self._set_prop(API_CODE.API_CODE_SetAFMode, 0, afmode) == False:
            return self._api_error()
        return self._api_success()

    def get_focus_distance_range(self) -> APIResponseDict:
        """ Get the available focusing distance range.
            Note:
            - Focus distance values are only changeable when the focus mode is set to MANUAL.
        """
        self._trace( "Getting focus distance range..." )

        focus_pos_caps = FocusPosCaps()
        caps_info_size = c_long(sizeof(focus_pos_caps))

        def cap_focuspos():
            if self._lib.m_pfnCapProp(self._camera_handle, API_CODE.API_CODE_CapFocusPos.value, 2, byref(caps_info_size), byref(focus_pos_caps)) != XSDK_COMPLETE:
                self._load_error_code()
                return False
            else:
                if focus_pos_caps.lFocusPlsFCSDepthCap == 0 and focus_pos_caps.lMinDriveStepMFDriveEndThresh == 0:
                    self._print( "Focus distance caps info is empty." )
                    return False
                return True
            
        if self._retry_api_call( cap_focuspos, retry_interval=self._COMMAND_RETRY_INTERVAL, retry_count=self._COMMAND_RETRY_COUNT ):
            focus_distance_range = {
                "inf": focus_pos_caps.lFocusPlsINF,
                "mod": focus_pos_caps.lFocusPlsMOD,
                "dof": focus_pos_caps.lFocusPlsFCSDepthCap,
                "step": focus_pos_caps.lMinDriveStepMFDriveEndThresh,
                "is_reactive": True,  # options may change depending on focus mode and other settings
                "is_volatile": True,  # options may changed by camera side without API call
            }
            return self._api_success_dict( focus_distance_range )
        return self._api_error_dict()

    def set_focus_distance(self, focus_distance) -> APIResponse:
        """ Set the focusing distance for the camera.
            Note:
            - Focus distance values are changeable when the focus mode is set to MANUAL.
        """
        self._trace( f"Setting focus distance to {focus_distance}" )
        if self._set_prop(API_CODE.API_CODE_SetFocusPos, focus_distance) == False:
            return self._api_error()
        return self._api_success()
    
    def get_focus_distance(self) -> APIResponseValue:
        """ Get the current focusing distance of the camera.
            Note:
            - If you adjust the focus ring on the lens directly, this value will be updated accordingly.
        """
        focus_distance = 0
        if self._retry_api_call( lambda: self._get_prop(API_CODE.API_CODE_GetFocusPos)!=focus_distance,
                                retry_interval=self._AF_RETRY_INTERVAL, retry_count=self._AF_RETRY_COUNT ):
            # Retry until the focus distance changes from the initial value
            focus_distance = self._get_prop(API_CODE.API_CODE_GetFocusPos)
        
        if focus_distance is None:
            return self._api_error_value()
        return self._api_success_value( focus_distance )

    # half-pressing the shutter button to focus
    #  - This will trigger autofocus and the camera will focus on the specified focus area.
    def perform_af(self, enable=True) -> APIResponse:
        """ Perform autofocus (AF) corresponding to half-pressing the shutter button.
            The behavior of operation depends on the current focus mode MANUAL/AF-S/AF-C and PreAF mode.
            Note:
            - If PreAF is active, the camera will automatically perform AF without trigger, so this function will have no effect while PreAF is active.
            - In AF-S mode, this function will trigger instant AF operation once
            - In AF-C mode, this function will start AF operation continuously until af_lock or perform_af(False).
        """
        self._trace( f"Performing autofocus (AF) operation, enable={enable}" )
        # if PreAF is active, the camera will automatically perform AF without needing to call this function
        if self._get_prop( API_CODE.API_CODE_GetPreAFMode ) == XSDK_ON:
            return self._api_error( "PreAF is active." )

        # Focus Mode should be set to AF-S or AF-C before calling this function
        focus_mode = self._get_prop( API_CODE.API_CODE_GetFocusMode )
        if focus_mode is None:
            return self._api_error()
        elif focus_mode == XSDK_FOCUS_AFC:
            # trigger start/stop continuous AF operation 
            shot_option, af_status = c_long(0), c_long(0)
            if enable:
                if self._retry_api_call( lambda: self._release_mode(XSDK_RELEASE_AF), retry_count=self._AF_RETRY_COUNT, retry_interval=self._AF_RETRY_INTERVAL ):
                    self._trace( "AF-C autofocus operation started" )
                    return self._api_success()
                self._release_mode(XSDK_RELEASE_N_AF)
                return self._api_error( "AF-C autofocus operation failed to start" )
            else:
                if self._retry_api_call( lambda: self._release_mode(XSDK_RELEASE_N_AF), retry_count=self._AF_RETRY_COUNT, retry_interval=self._AF_RETRY_INTERVAL ):
                    self._trace( "AF-C autofocus operation stopped" )
                    return self._api_success()
                return self._api_error( "AF-C autofocus operation failed to stop" )
        else:
            if focus_mode == XSDK_FOCUS_MANUAL:
                perform_on = XSDK_RELEASE_INSTANTAF
                perform_off = XSDK_RELEASE_N_INSTANTAF
            else:
                perform_on = XSDK_RELEASE_AF     #  S1ON
                perform_off = XSDK_RELEASE_N_AF  #  N_S1OFF
            # AF Trigger ON/OFF
            # make sure AF status before triggering ?
            if self._retry_api_call( lambda: self._release_mode(perform_on), retry_count=self._AF_RETRY_COUNT, retry_interval=self._AF_RETRY_INTERVAL ): 
                if self._retry_api_call( lambda: self._release_mode(perform_off), retry_count=self._COMMAND_RETRY_COUNT, retry_interval=self._COMMAND_RETRY_INTERVAL ):
                    self._trace( f"AF operation success in focus mode:{hex(focus_mode)}" )
                    return self._api_success()
            self._release_mode(perform_off)  # ensure AF is turned off after failure
            return self._api_error( f"AF operation failed in focus mode:{hex(focus_mode)}" )

    def af_lock(self, enable=True) -> APIResponse:
        """ Lock or unlock autofocus (AF) operation in AF-S/AF-C mode.
            This will lock the current focus distance and prevent the camera from refocusing until AF is unlocked.
            Note:
            - Once AF is locked, some functions may be restricted until AF is unlocked.
            - You can check the current status by get_status() function.
        """
        self._trace( f"Setting AF lock to {enable}" )
        lock_mode = XSDK_RELEASE_AFL if enable else XSDK_RELEASE_N_AFL
        if self._retry_api_call( lambda: self._release_mode(lock_mode), retry_count=self._AF_RETRY_COUNT, retry_interval=self._AF_RETRY_INTERVAL ):
            return self._api_success()
        return self._api_error()

    def ae_lock(self, enable=True) -> APIResponse:
        """ Lock or unlock auto exposure (AE) operation in program AE mode except for MANUAL.
            This will lock the current exposure settings and prevent the camera from adjusting exposure until AE is unlocked.
            Note:
            - Once AE is locked, some functions may be restricted until AE is unlocked.
            - You can check the current status by get_status() function.
        """
        self._trace( f"Setting AE lock to {enable}" )
        lock_mode = XSDK_RELEASE_AEL if enable else XSDK_RELEASE_N_AEL
        if self._retry_api_call( lambda: self._release_mode(lock_mode), retry_count=self._AF_RETRY_COUNT, retry_interval=self._AF_RETRY_INTERVAL ):
            return self._api_success()
        return self._api_error()

    def awb_lock(self, enable=True) -> APIResponse:
        """ Lock or unlock auto white balance (AWB) operation 
            This will lock the current white balance settings and prevent the camera from adjusting white balance until AWB is unlocked.
        """
        self._trace( f"Setting AWB lock to {enable}" )
        lock_mode = XSDK_RELEASE_WBL if enable else XSDK_RELEASE_N_WBL
        if self._retry_api_call( lambda: self._release_mode(lock_mode), retry_count=self._AF_RETRY_COUNT, retry_interval=self._AF_RETRY_INTERVAL ):
            return self._api_success()
        return self._api_error()

    # ----------------------------------------------
    # Live Image View Controls
    # - set/get LiveView options (quality, size, digitalcrop zoom)
    # - start/stop LiveView mode
    # - get LiveView image from camera buffer
    # ----------------------------------------------
    # LiveView ON/OFF
    # entering LiveView mode will start continuous image update in camera buffer,
    #  and the caller can get the latest LiveView image repeatedly by calling get_liveview_image() function.
    # In LiveView mode, some camera settings may not be changeable depending on camera model,
    #  and the caller should set up desired LiveView options before starting LiveView.
    def start_liveview(self) -> APIResponse:
        """ Enter LiveView mode to enable continuous update of the LiveView image in the camera buffer.
            You can get the latest LiveView image repeatedly by get_liveview_image() function.
            Note:
            - In LiveView mode, only following functions are available.
              get_liveview_image(), set/get_focus_area(), stop_liveview(), get_status(), is_connected()
        """
        success = self._set_prop(API_CODE.API_CODE_StartLiveView)
        return self._api_success() if success else self._api_error()

    def stop_liveview(self) -> APIResponse:
        """ Exit LiveView mode to stop continuous image update in camera buffer.
            To check if LiveView is active, you can use get_status() function.
        """
        success = self._set_prop(API_CODE.API_CODE_StopLiveView)
        return self._api_success() if success else self._api_error()
    
    # get available LiveView options about Image Quality
    def get_liveview_quality_options(self) -> APIResponseList:
        """ Get the available LiveView options of image quality (jpeg compression)
            The values are defined in the FUJIFILM Camera Control SDK documentation.
        """
        # get quality options / model dependent
        quality_list = self._cap_prop(API_CODE.API_CODE_CapLiveViewImageQuality)
        if len(quality_list) == 0:
            self._trace( "LiveView image quality capability not supported in this model, then return default options." )
            quality_list = [ XSDK_LIVEVIEW_QUALITY_FINE ]   # X-S10 only support FINE quality for liveview and return error for capability query.
        return self._api_success_list( quality_list )

    # get current LiveView mode (quality) from camera
    def get_liveview_quality(self) -> APIResponseValue:
        """ Get the current LiveView quality.
            The returned value is one of the available options obtained from get_liveview_quality_options().
        """
        quality = self._get_prop(API_CODE.API_CODE_GetLiveViewImageQuality)
        return self._api_success_value( quality ) if quality is not None else self._api_error_value()

    # set LiveView mode (quality) to camera
    def set_liveview_quality(self, quality) -> APIResponse:
        """ Set the LiveView quality (jpeg compression) option for the camera. 
            The option should be set up before starting LiveView.
        """
        self._trace( f"Setting LiveView mode: quality={quality}" )
        success = self._set_prop(API_CODE.API_CODE_SetLiveViewImageQuality, quality)
        return self._api_success() if success else self._api_error()

    # get available LiveView options about Image size (pixels)
    def get_liveview_size_options(self) -> APIResponseList:
        """ Get the available LiveView options of image size (pixels)
            The values are defined in the FUJIFILM Camera Control SDK documentation.
        """
        # get size options / model dependent
        size_list = self._cap_prop(API_CODE.API_CODE_CapLiveViewImageSize)
        if len(size_list) == 0:
            self._trace( "LiveView image size capability not supported in this model, then return default options." )
            size_list = [ XSDK_LIVEVIEW_SIZE_L, XSDK_LIVEVIEW_SIZE_M, XSDK_LIVEVIEW_SIZE_S ]
        return self._api_success_list( size_list )
 
    # get current LiveView mode ( size) from camera
    def get_liveview_size(self) -> APIResponseValue:
        """ Get the current LiveView size.
            The returned value is one of the available options obtained from get_liveview_size_options().
        """
        size = self._get_prop(API_CODE.API_CODE_GetLiveViewImageSize)
        return self._api_success_value( size ) if size is not None else self._api_error_value()

    # set LiveView mode (size) to camera
    def set_liveview_size(self, size) -> APIResponse:
        """ Set the LiveView size (pixels) option for the camera. 
            The option should be set up before starting LiveView.
        """
        self._trace( f"Setting LiveView mode: size={size}" )
        success = self._set_prop(API_CODE.API_CODE_SetLiveViewImageSize, size)
        return self._api_success() if success else self._api_error()

    # Get LiveView Image from camera
    #  - This function can be called repeatedly to get liveview images in a loop, and the caller can specify the desired interval between calls to control the frame rate.
    #  start_liveview() should be called before calling this function, and stop_liveview() should be called after finishing liveview.
    #  The function will wait until the liveview image is ready in camera buffer, and return the image data as byte array.
    #  If the image is not ready within the specified retry count and interval, it will return an error.

    def _check_liveview_buffer(self) -> int:
        image_info = ImageInformation()
        if self._lib.m_pfnReadImageInfo(self._camera_handle, byref(image_info)) == XSDK_COMPLETE:
            return image_info.data_size if (image_info.format & XSDK_IMAGEFORMAT_MASK) == XSDK_IMAGEFORMAT_LIVE else 0
        self._load_error_code()
        return -1    # error

    def get_liveview_image(self) -> APIResponseDict:
        """ Get the latest LiveView image from the camera and return the image data as byte array.
            This function can be called repeatedly to get liveview images in a loop to display.
            Note:
             - start_liveview() should be called before calling this function, and stop_liveview() should be called after finishing liveview.
             - If the image is not ready within the specified retry count and interval, it will return an error.
        """
        image_info = ImageInformation()
        if not self._retry_api_call( lambda: self._lib.m_pfnReadImageInfo(self._camera_handle, byref(image_info))==XSDK_COMPLETE \
                                        and (image_info.format & XSDK_IMAGEFORMAT_MASK) == XSDK_IMAGEFORMAT_LIVE,
                                     retry_count=self._LIVEVIEW_RETRY_COUNT, retry_interval=self._LIVEVIEW_RETRY_INTERVAL ):
            return self._api_error_dict()  # "ReadImageInfo (LIVE) timeout")

        data_size = image_info.data_size
        if data_size == 0:
            return self._api_error_dict( "LiveView image data size is 0" )

        data = create_string_buffer(data_size)
        if not self._retry_api_call( lambda: self._lib.m_pfnReadImage(self._camera_handle, byref(data), c_long(data_size))==XSDK_COMPLETE or self._load_error_code(),
                                     retry_count=self._LIVEVIEW_RETRY_COUNT, retry_interval=self._LIVEVIEW_RETRY_INTERVAL ):
            return self._api_error_dict()

        # success
        return self._api_success_dict( { "buffer": bytearray(data), "size": data_size } )

    def get_image_size_options(self) -> APIResponseList:
        """ Get the available image size options for the camera.
            The options depends on the camera model, and values are defined in the FUJIFILM Camera Control SDK documentation.
        """
        #image_format_list = self._cap_prop(API_CODE.API_CODE_CapImageFormat)
        image_size_list = self._cap_prop(API_CODE.API_CODE_CapImageSize)
        if len(image_size_list) == 0:
            self._trace( "Image size capability not supported in this model, then return default options." )
            image_size_list = [ XSDK_IMAGESIZE_L, XSDK_IMAGESIZE_M, XSDK_IMAGESIZE_S ]
        return self._api_success_list( image_size_list )

    def set_image_size(self, size) -> APIResponse:
        """ Set the image size for the camera.
            The size parameter should be one of the available options obtained from get_image_size_options().
        """
        self._trace( f"Setting image size to {size}" )
        if self._set_prop(API_CODE.API_CODE_SetImageSize, size) == False:
            return self._api_error()
        return self._api_success()

    def get_image_size(self) -> APIResponseValue:
        """ Get the current image size setting for the camera.
            The returned value is one of the available options obtained from get_image_size_options().
        """
        size = self._get_prop(API_CODE.API_CODE_GetImageSize)
        if size is None:
            return self._api_error_value()
        return self._api_success_value( size )

    def get_image_quality_options(self) -> APIResponseList:
        """ Get the available image quality options for the camera.
            The options depends on the camera model, and values are defined in the FUJIFILM Camera Control SDK documentation.
            for example, 'FINE', 'NORMAL', 'RAW+FINE', etc.
            This affects the saved image file of function capture_image(), capture_multi_images(), bulb_on/off().
        """
        image_quality_list = self._cap_prop(API_CODE.API_CODE_CapImageQuality)
        if len(image_quality_list) == 0:
            self._trace( "Image quality capability not supported in this model, then return default options." )
            image_quality_list = [ XSDK_IMAGEQUALITY_FINE, XSDK_IMAGEQUALITY_NORMAL, XSDK_IMAGEQUALITY_RAW_FINE, XSDK_IMAGEQUALITY_RAW_NORMAL ]
        return self._api_success_list( image_quality_list )

    def set_image_quality(self, quality) -> APIResponse:
        """ Set the image quality (jpeg compression) for the camera.
            The quality parameter should be one of the available options obtained from get_image_quality_options().
        """
        self._trace( f"Setting image quality to {quality}" )
        if self._set_prop(API_CODE.API_CODE_SetImageQuality, quality) == False:
            return self._api_error()
        return self._api_success()

    def get_image_quality(self) -> APIResponseValue:
        """ Get the current image quality setting for the camera.
            The returned value is one of the available options obtained from get_image_quality_options().
        """
        quality = self._get_prop(API_CODE.API_CODE_GetImageQuality)
        if quality is None:
            return self._api_error_value()
        return self._api_success_value( quality )

# helper function to check if the SDK is installed
def is_sdk_installed() -> bool:
    """ Check if the FUJIFILM Camera Control SDK is available.
    """
    path = _clickwrap.get_install_path(licenser=CAMERA_SDK_NAME)
    return path is not None and path != "" and\
          _clickwrap.is_license_accepted(licenser=CAMERA_SDK_NAME)

def install_sdk() -> FujiSDK|None:
    """ Attempt to install the FUJIFILM Camera Control SDK.
        Returns True if the installation was successful, False otherwise.
    """
    default_path = _clickwrap.get_install_path( licenser=CAMERA_SDK_NAME )
    install_path = default_path
    lib = None
    while( True ):
        lib = FujiSDK( sdk_path = install_path )
        if lib.get_error() == FUJI_SDK_ERR_OK and lib.m_pfnInit:
            break
        install_path = _clickwrap.guide_installation( licenser=CAMERA_SDK_NAME, url=CAMERA_SDK_SITE, default_path=install_path )
        time.sleep(1) 

    if install_path != default_path:
        print( f"Loaded {CAMERA_SDK_NAME} from: {install_path}" )
        _clickwrap.set_install_path(install_path, licenser=CAMERA_SDK_NAME)  # save the path for future use

    # if license agreement is not accepted, it will raise an exception and exit before initializing the library
    if not _clickwrap.confirm_clickwrap( licenser=CAMERA_SDK_NAME, language="en" ):
        time.sleep(1)  # wait a moment before showing error message, in case clickwrap dialog is still closing
        print( "License Agreement is rejected, process cannot continue." )
        return None
    # Return the initialized FujiSDK library instance
    return lib

# end of camera_api.py