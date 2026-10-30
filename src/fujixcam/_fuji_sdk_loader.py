# -----------------------------------------------------
# fuji_sdk_loader.py
#
#  1. Provide parameter definitions and structures for Fuji SDK
#  (converted from FujiFilm XSDK headers "XAPI.h",...)
#  2. Load Fuji SDK library and bind functions
#  (modified from FujiFilm XSDK Sample "liveview")
# -----------------------------------------------------

#
#  1. Provide parameter definitions and structures for Fuji SDK
#
from enum import Enum
from ctypes import c_longlong, c_void_p, c_char_p, c_long, c_char, Structure, CDLL, byref, create_string_buffer, sizeof, cast, CFUNCTYPE, POINTER

# SDK Result
XSDK_COMPLETE = 0
XSDK_ERROR    = -1

# API Parameters

# DSC connect I/F
XSDK_DSC_IF_USB        = 0x00000001  # USB
XSDK_DSC_IF_WIFI_LOCAL = 0x00000010  # Wi-Fi within local segment
XSDK_DSC_IF_WIFI_IP    = 0x00000020  # Wi-Fi specified IPv4 address

XSDK_DSC_MODE_TETHER = 0x0001   # Tethered shooting mode required for this library's functions to work properly.
XSDK_DSC_MODE_WEBCAM = 0x0008

# Priority Mode
XSDK_PRIORITY_CAMERA = 0x0001  #Camera
XSDK_PRIORITY_PC     = 0x0002  #PC

# Media Record
XSDK_MEDIAREC_RAWJPEG = 0x0001
XSDK_MEDIAREC_RAW     = 0x0002
XSDK_MEDIAREC_JPEG    = 0x0003
XSDK_MEDIAREC_OFF     = 0x0004

# Drive Mode
XSDK_DRIVE_MODE_INVALID = 0xFFFF
XSDK_DRIVE_MODE_CH = 0x0002
XSDK_DRIVE_MODE_CL = 0x0003
XSDK_DRIVE_MODE_S  = 0x0004

# Program Mode
XSDK_PROGRAMMODE_M = 0x0001
XSDK_PROGRAMMODE_A = 0x0003
XSDK_PROGRAMMODE_S = 0x0004
XSDK_PROGRAMMODE_P = 0x0006

XSDK_SHUTTER_SPEED_BULB = -1
XSDK_SHUTTER_SPEED_LIMIT_MECHANICAL = 244   # 1/4000 sec Mechanical shutter speed limit
XSDK_SHUTTER_SPEED_THRESHOLD_SECONDS = 1000000   # 1 second or longer is considered as "slow shutter speed"
XSDK_SHUTTER_SPEED_THRESHOLD_MINUTES = 64000000  # 60 seconds or longer is considered as "minute-level shutter speed"

# Release Mode
XSDK_RELEASE_SHOOT       = 0x0100   # 単独では使えない SHOOT_S1OFF で使う
XSDK_RELEASE_S1ON        = 0x0200   # 半押しして撮影：S1ON -> S2_S1OFF  MF/AF-S/AF-Cすべて可
XSDK_RELEASE_N_S1OFF     = 0x0004   # 半押し解除（半押しして戻す：S1ON -> N_S1OFF）
XSDK_RELEASE_SHOOT_S1OFF = (XSDK_RELEASE_SHOOT | XSDK_RELEASE_N_S1OFF) # 0x0104　半押しせず一気に撮影 MF/AF-Sのみ
XSDK_RELEASE_S2          = 0x0300   # 単独では使えない S2_S1OFF で使う
XSDK_RELEASE_S2_S1OFF   = (XSDK_RELEASE_S2 | XSDK_RELEASE_N_S1OFF)   # 0x0304 半押し状態から撮影
XSDK_RELEASE_BULB_ON     = 0x0400
XSDK_RELEASE_N_BULBOFF   = 0x0008
XSDK_RELEASE_BULBS2_ON   = 0x0500   # 半押し状態からBULB開始
#XSDK_RELEASE_BULBS_S1OFF = (XSDK_RELEASE_BULBS_ON|XSDK_RELEASE_N_S1OFF)  # 0x0404
XSDK_RELEASE_N_BULBS1OFF = (XSDK_RELEASE_N_BULBOFF | XSDK_RELEASE_N_S1OFF) # 0x000C BULB終了
XSDK_RELEASE_CANCEL      = 0x000F   # 長時間露光時の中止
# Auto Lock (Exposure/Focus/White Balance)
XSDK_RELEASE_AEL         = 0x9000
XSDK_RELEASE_N_AEL       = 0x0002
XSDK_RELEASE_AFL         = 0x9100
XSDK_RELEASE_N_AFL       = 0x0001
XSDK_RELEASE_WBL         = 0x9200
XSDK_RELEASE_N_WBL       = 0x0040
# Perform AF (Auto Focus) operation
XSDK_RELEASE_AF          = 0x9300   # AF-C Autofocus開始 / AF-S Instant AF
XSDK_RELEASE_N_AF        = 0x0020   # AF-C Autofocus終了 / AF-S Instant AF解除
XSDK_RELEASE_INSTANTAF   = 0xA000   # MF で Instant AF
XSDK_RELEASE_N_INSTANTAF = 0x0010   # MF で Instant AF解除

# Release AFStatus
XSDK_RELEASE_OK          = 1           # AF OK or CWB_AE_NOERR
XSDK_RELEASE_AF_FAILURE  = 0           # !AF
XSDK_RELEASE_AF_UNCHECK  = 2           # AF not checked
XSDK_RELEASE_AF_NOMOVE   = 4           # AF no Movement

XSDK_RELEASE_CWB_AE_OVER = 2           # CWB Exposure Over
XSDK_RELEASE_CWB_AE_UNDER= 3           # CWB Exposure Under

# Release Status (return in bitmap)
XSDK_RELEASE_STATUS_S1   = 0x0200
XSDK_RELEASE_STATUS_BULB = 0x0400
XSDK_RELEASE_STATUS_AF   = 0x0800
XSDK_RELEASE_STATUS_AEL  = 0x4000
XSDK_RELEASE_STATUS_AFL  = 0x8000
XSDK_RELEASE_STATUS_WBL  = 0x2000
XSDK_RELEASE_STATUS_SHOOTING = 0x0100
XSDK_RELEASE_STATUS_NONE = 0x0000

# Focus mode
XSDK_FOCUS_MANUAL        = 0x0001
XSDK_FOCUS_AFS           = 0x8001
XSDK_FOCUS_AFC           = 0x8002

# Focus points
XSDK_FOCUS_POINTS_13X7	= 0x0001
XSDK_FOCUS_POINTS_25X13	= 0x0002
XSDK_FOCUS_POINTS_13X9	= 0x0003
XSDK_FOCUS_POINTS_25X17	= 0x0004

FOCUS_POINTS_ASPECTS = {
    0x0001: (13, 7),   # 13x7
    0x0002: (25, 13),  # 25x13
    0x0003: (13, 9),   # 13x9
    0x0004: (25, 17),  # 25x17
}

# AF mode
XSDK_AFMODE_SINGLE    = 0x8001      # AF Single/Area
XSDK_AFMODE_ZONE      = 0x8002      # AF Zone
XSDK_AFMODE_WIDETRACKING = 0x8003   # AF Wide/Tracking
XSDK_AFMODE_MULTI     = 0x0002      # AF Multi-Spot
XSDK_AFMODE_ALL       = 0x8004      # AF ALL

# PreAF mode etc.
XSDK_ON               = 0x0001
XSDK_OFF              = 0x0002

# Image Format(ReadImageInfo)
XSDK_IMAGEFORMAT_RAW  = 1
XSDK_IMAGEFORMAT_LIVE = 4
XSDK_IMAGEFORMAT_NONE = 5
XSDK_IMAGEFORMAT_JPEG = 7
XSDK_IMAGEFORMAT_HEIF = 18
XSDK_IMAGEFORMAT_MASK = 0xFF

# Image Quality
XSDK_IMAGEQUALITY_RAW           = 0x0001    # RAW without JPEG
XSDK_IMAGEQUALITY_FINE          = 0x0002
XSDK_IMAGEQUALITY_NORMAL        = 0x0003
XSDK_IMAGEQUALITY_RAW_FINE      = 0x0004    # RAW + JPEG Fine
XSDK_IMAGEQUALITY_RAW_NORMAL    = 0x0005    # RAW + JPEG Normal
XSDK_IMAGEQUALITY_SUPERFINE     = 0x0006
XSDK_IMAGEQUALITY_RAW_SUPERFINE = 0x0007    # RAW + JPEG Super Fine

# Image Size
XSDK_IMAGESIZE_S_3_2      =          1
XSDK_IMAGESIZE_S_16_9     =          2
XSDK_IMAGESIZE_S_1_1      =          3
XSDK_IMAGESIZE_M_3_2      =          4
XSDK_IMAGESIZE_M_16_9     =          5
XSDK_IMAGESIZE_M_1_1      =          6
XSDK_IMAGESIZE_L_3_2      =          7
XSDK_IMAGESIZE_L_16_9     =          8
XSDK_IMAGESIZE_L_1_1      =          9
XSDK_IMAGESIZE_S_4_3      =          10
XSDK_IMAGESIZE_S_65_24    =          11
XSDK_IMAGESIZE_S_5_4      =          12
XSDK_IMAGESIZE_S_7_6      =          13
XSDK_IMAGESIZE_L_4_3      =          14
XSDK_IMAGESIZE_L_65_24    =          15
XSDK_IMAGESIZE_L_5_4      =          16
XSDK_IMAGESIZE_L_7_6      =          17
XSDK_IMAGESIZE_M_4_3      =          18
XSDK_IMAGESIZE_M_65_24    =          19
XSDK_IMAGESIZE_M_5_4      =          20
XSDK_IMAGESIZE_M_7_6      =          21
XSDK_IMAGESIZE_L_3_4      =          22
XSDK_IMAGESIZE_L_17_6     =          23
XSDK_IMAGESIZE_M_3_4      =          24
XSDK_IMAGESIZE_M_17_6     =          25
XSDK_IMAGESIZE_S_3_4      =          26
XSDK_IMAGESIZE_S_17_6     =          27
XSDK_IMAGESIZE_L = XSDK_IMAGESIZE_L_3_2
XSDK_IMAGESIZE_M = XSDK_IMAGESIZE_M_3_2
XSDK_IMAGESIZE_S = XSDK_IMAGESIZE_S_3_2

# LiveView Mode
XSDK_LIVEVIEW_MODE1 = 0x0001
XSDK_LIVEVIEW_MODE2 = 0x0002

# LiveView Image Quality
XSDK_LIVEVIEW_QUALITY_FINE   = 0x0001  # Fine
XSDK_LIVEVIEW_QUALITY_NORMAL = 0x0002  # Normal
XSDK_LIVEVIEW_QUALITY_BASIC  = 0x0003  # Basic

# LiveView Image Size
XSDK_LIVEVIEW_SIZE_L = 0x0001  # L(1280)
XSDK_LIVEVIEW_SIZE_M = 0x0002  # M(800)
XSDK_LIVEVIEW_SIZE_S = 0x0003  # S(640)

# Through Image Zoom
XSDK_THROUGHIMAGE_ZOOM_10  = 0x0001  # x1.0
XSDK_THROUGHIMAGE_ZOOM_20  = 0x0007  # x2.0
XSDK_THROUGHIMAGE_ZOOM_25  = 0x0002  # x2.5
XSDK_THROUGHIMAGE_ZOOM_33  = 0x0008  # x3.3
XSDK_THROUGHIMAGE_ZOOM_40  = 0x0004  # x4.0
XSDK_THROUGHIMAGE_ZOOM_60  = 0x0003  # x6.0
XSDK_THROUGHIMAGE_ZOOM_66  = 0x0009  # x6.6
XSDK_THROUGHIMAGE_ZOOM_68  = 0x000F  # x6.8
XSDK_THROUGHIMAGE_ZOOM_80  = 0x0005  # x8.0
XSDK_THROUGHIMAGE_ZOOM_83  = 0x000D  # x8.3
XSDK_THROUGHIMAGE_ZOOM_120 = 0x0011  # x12.0
XSDK_THROUGHIMAGE_ZOOM_131 = 0x000A  # x13.1
XSDK_THROUGHIMAGE_ZOOM_140 = 0x0010  # x14.0
XSDK_THROUGHIMAGE_ZOOM_160 = 0x0006  # x16.0
XSDK_THROUGHIMAGE_ZOOM_170 = 0x000E  # x17.0
XSDK_THROUGHIMAGE_ZOOM_197 = 0x000C  # x19.7
XSDK_THROUGHIMAGE_ZOOM_240 = 0x000B  # x24.0
# 0x0001 - 0x0011 are defined

# API Codes
class API_CODE(Enum):
    API_CODE_Init                       = 0x1001
    API_CODE_Exit                       = 0x1002
    API_CODE_Detect                     = 0x1011    # 1010 is missing
    API_CODE_Close                      = 0x1022
    API_CODE_PowerOFF                   = 0x1023
    API_CODE_OpenEx                     = 0x1024

    API_CODE_GetErrorNumber             = 0x1031
    API_CODE_GetVersionString           = 0x1032
    API_CODE_GetErrorDetails            = 0x1033
    API_CODE_GetDeviceInfo              = 0x1041
    API_CODE_GetLensInfo                = 0x1044

    API_CODE_CapPriorityMode            = 0x1101
    API_CODE_SetPriorityMode            = 0x1102
    API_CODE_GetPriorityMode            = 0x1103
    API_CODE_CapRelease                 = 0x1111
    API_CODE_Release                    = 0x1112 
    API_CODE_GetReleaseStatus           = 0x1113
    API_CODE_CapReleaseEx               = 0x1115
    API_CODE_ReleaseEx                  = 0x1116
    API_CODE_CapReleaseStatus           = 0x1118
    API_CODE_GetBufferCapacity          = 0x1200
    API_CODE_ReadImageInfo              = 0x1201
    API_CODE_ReadPreview                = 0x1202
    API_CODE_ReadImage                  = 0x1203
    API_CODE_DeleteImage                = 0x1204

    API_CODE_CapAEMode                  = 0x1301
    API_CODE_SetAEMode                  = 0x1302
    API_CODE_GetAEMode                  = 0x1303
    API_CODE_CapShutterSpeed            = 0x1304
    API_CODE_SetShutterSpeed            = 0x1305
    API_CODE_GetShutterSpeed            = 0x1306
    API_CODE_CapExposureBias            = 0x1307
    API_CODE_SetExposureBias            = 0x1308
    API_CODE_GetExposureBias            = 0x1309
    API_CODE_CapSensitivity             = 0x1311
    API_CODE_SetSensitivity             = 0x1312
    API_CODE_GetSensitivity             = 0x1313
#    API_CODE_CapDynamicRange            = 0x1314
#    API_CODE_SetDynamicRange            = 0x1315
#    API_CODE_GetDynamicRange            = 0x1316
#    API_CODE_CapMeteringMode            = 0x1317
#    API_CODE_SetMeteringMode            = 0x1318
#    API_CODE_GetMeteringMode            = 0x1319
    API_CODE_CapLensZoomPos             = 0x1321
    API_CODE_SetLensZoomPos             = 0x1322
    API_CODE_GetLensZoomPos             = 0x1323
    API_CODE_CapAperture                = 0x1324
    API_CODE_SetAperture                = 0x1325
    API_CODE_GetAperture                = 0x1326
    API_CODE_CapWBMode                  = 0x1331
    API_CODE_SetWBMode                  = 0x1332
    API_CODE_GetWBMode                  = 0x1333
    API_CODE_CapWBColorTemp             = 0x1334
    API_CODE_SetWBColorTemp             = 0x1335
    API_CODE_GetWBColorTemp             = 0x1336

    API_CODE_CapMediaRecord             = 0x1351
    API_CODE_SetMediaRecord             = 0x1352
    API_CODE_GetMediaRecord             = 0x1353

    # BackupSettings
    API_CODE_SetBackupSettings          = 0x1375
    API_CODE_GetBackupSettings          = 0x1376

    # Model Dependent Function Call I/F
    API_CODE_CapProp                    = 0x1401
    API_CODE_SetProp                    = 0x1402
    API_CODE_GetProp                    = 0x1403

    # Live view control
    API_CODE_StartLiveView              = 0x3301
    API_CODE_StopLiveView               = 0x3302
    API_CODE_SetLiveViewImageQuality    = 0x3323
    API_CODE_GetLiveViewImageQuality    = 0x3324
    API_CODE_SetLiveViewImageSize       = 0x3325
    API_CODE_GetLiveViewImageSize       = 0x3326
    API_CODE_SetThroughImageZoom		= 0x3327
    API_CODE_GetThroughImageZoom		= 0x3328
    API_CODE_CapLiveViewImageQuality    = 0x3329
    API_CODE_CapLiveViewImageSize       = 0x332A
    API_CODE_CapThroughImageZoom		= 0x332B
    API_CODE_CapLiveViewStatus          = 0x332C
    API_CODE_GetLiveViewStatus          = 0x332D    # ON/OFF (depends on camera model)
#	API_CODE_CapLiveViewMode			= 0x332E
    API_CODE_SetLiveViewMode			= 0x332F
    API_CODE_GetLiveViewMode			= 0x3330
#	API_CODE_CapLiveViewImageRatio		= 0x3331
#	API_CODE_SetLiveViewImageRatio		= 0x3332
#	API_CODE_GetLiveViewImageRatio		= 0x3333
    #Image types
    API_CODE_SetImageSize               = 0x2101
    API_CODE_GetImageSize               = 0x2102
    API_CODE_SetImageQuality            = 0x2129
    API_CODE_GetImageQuality            = 0x2130
    API_CODE_CapImageSize				= 0x2180
    API_CODE_CapImageQuality			= 0x2185
    API_CODE_SetImageFormat             = 0x219E
    API_CODE_GetImageFormat             = 0x219F
    #Lens & Focus control
    API_CODE_SetFocusMode               = 0x2201
    API_CODE_GetFocusMode               = 0x2202
    API_CODE_SetAFMode                  = 0x2203
    API_CODE_GetAFMode                  = 0x2204
    API_CODE_SetFocusArea               = 0x2205
    API_CODE_GetFocusArea               = 0x2206
    API_CODE_SetFocusPos                = 0x2207
    API_CODE_GetFocusPos                = 0x2208
    API_CODE_CapFocusMode               = 0x2209
#    API_CODE_GetAFStatus                = 0x220A   # not documented in API reference
#    API_CODE_SetShutterPriorityMode     = 0x2217
#    API_CODE_GetShutterPriorityMode     = 0x2218
#    API_CODE_SetInstantAFMode           = 0x2219
#    API_CODE_GetInstantAFMode           = 0x2220
    API_CODE_SetPreAFMode               = 0x2221
    API_CODE_GetPreAFMode               = 0x2222
    API_CODE_CapAFMode                  = 0x2234
    API_CODE_CapFocusArea               = 0x2235
#    API_CODE_CapAFStatus                = 0x2236
#    API_CODE_CapShutterPriorityMode     = 0x2237
#    API_CODE_CapInstantAFMode           = 0x2238
    API_CODE_CapPreAFMode               = 0x2239
    API_CODE_CapFocusPoints             = 0x223E
    API_CODE_GetFocusPoints				= 0x2258
    API_CODE_CapFocusPos				= 0x2259

# Error Codes
class ERR_CODE(Enum):
    XSDK_ERRCODE_NOERR                  = 0x00000000
    XSDK_ERRCODE_SEQUENCE               = 0x00001001
    XSDK_ERRCODE_PARAM                  = 0x00001002
    XSDK_ERRCODE_INVALID_CAMERA         = 0x00001003
    XSDK_ERRCODE_LOADLIB                = 0x00001004
    XSDK_ERRCODE_UNSUPPORTED            = 0x00001005
    XSDK_ERRCODE_BUSY                   = 0x00001006
    XSDK_ERRCODE_AF_TIMEOUT             = 0x00001007
    XSDK_ERRCODE_SHOOT_ERROR            = 0x00001008
    XSDK_ERRCODE_FRAME_FULL             = 0x00001009
    XSDK_ERRCODE_STANDBY                = 0x00001010
    XSDK_ERRCODE_NODRIVER               = 0x00001011
    XSDK_ERRCODE_NO_MODEL_MODULE        = 0x00001012
    XSDK_ERRCODE_API_NOTFOUND           = 0x00001013
    XSDK_ERRCODE_API_MISMATCH           = 0x00001014
    XSDK_ERRCODE_INVALID_USBMODE        = 0x00001015
    XSDK_ERRCODE_FORCEMODE_BUSY         = 0x00001016
    XSDK_ERRCODE_RUNNING_OTHER_FUNCTION = 0x00001017
    XSDK_ERRCODE_COMMUNICATION          = 0x00002001
    XSDK_ERRCODE_TIMEOUT                = 0x00002002
    XSDK_ERRCODE_COMBINATION            = 0x00002003
    XSDK_ERRCODE_WRITEERROR             = 0x00002004
    XSDK_ERRCODE_CARDFULL               = 0x00002005
    XSDK_ERRCODE_HARDWARE               = 0x00003001
    XSDK_ERRCODE_INTERNAL               = 0x00009001
    XSDK_ERRCODE_MEMFULL                = 0x00009002
    XSDK_ERRCODE_UNKNOWN                = 0x00009100

# Structures for API parameters and return values
# - GETDEVICEINFO, GETLENSINFO, READIMAGEINFO, FOCUSAREA
class DeviceInformation(Structure):
    _fields_ = [('vender_name',   c_char * 256),
                ('manufacturer',  c_char * 256),
                ('product_name',  c_char * 256),
                ('firmware_name', c_char * 256),
                ('device_type',  c_char * 256),
                ('serial_number', c_char * 256),
                ('framework_id', c_char * 256),
                ('reserved',     c_char * 65),]

class LensInformation(Structure):
    _fields_ = [('model_name',      c_char * 20),
                ('product_name',    c_char * 100),
                ('seral_number',    c_char * 20),
                ('IS_capablity',    c_long),
                ('MF_capablity',    c_long),
                ('zoom_capability',  c_long) ,]

class ImageInformation(Structure):
    _fields_ = [('internal_name',    c_char * 32),
                ('format',           c_long),
                ('data_size',        c_long),
                ('image_pix_height', c_long),
                ('image_pix_width',  c_long),
                ('image_bit_depth',  c_long),
                ('preview_size',     c_long),
                ('image_handle',     c_void_p),]

class FocusArea(Structure):
    _fields_ = [('h',       c_long),
                ('v',       c_long),
                ('size',  c_long),]

class FocusPosCaps(Structure):
    _fields_ = [('lSizeFocusPosCap',       c_long),  # sizeof( SDK_FOCUS_POS_CAP )
                ('lStructVer',              c_long), # Fixed to 0x00010000 on this version
                ('lFocusPlsINF',            c_long), # INFINITY position
                ('lFocusPlsMOD',            c_long), # MOD position
                ('lFocusOverSearchPlsINF',  c_long), # Over search for INFINITY
                ('lFocusOverSearchPlsMOD',  c_long), # Over search for MOD
                ('lFocusPlsFCSDepthCap',    c_long), # DOF. If lFocusPlsFCSDepthCap==0, the information of this structure is invalid.
                ('lMinDriveStepMFDriveEndThresh', c_long),] # Minimum drive steps 

#
#  1. Load Fuji SDK library and bind functions
#
import os
import platform

FUJI_SDK_ERR_OK         = 0
FUJI_SDK_ERR_LOADSDK    = -1
FUJI_SDK_ERR_SDKVERSION = -2

class FujiSDK:
 
    def __init__(self, sdk_path: str = ""):
        self.m_module = None
        self.m_err = None
        
        try:
            os_name = platform.system()
            if os_name == "Windows":
                lib_path = ( sdk_path or "fuji_sdk" ) + "/XAPI.dll"
            elif os_name == "Darwin":
                lib_path = ( sdk_path or "fuji_sdk" ) + "/XAPI.bundle/Contents/MacOS/XAPI"
            elif os_name == "Linux":
                lib_path = ( sdk_path or "fuji_sdk" ) + "/XAPI.so"
            else:
                raise OSError(f"Unsupported OS: {os_name}")
            
            base = os.path.dirname(os.path.realpath(__file__))
            path = os.path.normpath(os.path.join(base, lib_path))
            self.m_module = CDLL(path)

            self._load_sdk_library()

        except OSError as e:
            self.m_module = None
    
    
    def __del__(self):
        if self.m_module is not None:
            self.m_module = None
    
    
    def _load_sdk_library(self):
        # helper function to link api entry points
        def api_entry(func_name, argtypes=None, restype=None):
            func = getattr(self.m_module, func_name, None)
            if func is None:
                # Raise an error if the function is not found in the SDK library.
                raise AttributeError(f"Function {func_name} not found in the SDK library.")
            func.argtypes = argtypes if argtypes is not None else []
            func.restype  = restype  if restype is not None else c_long
            return func

        try:
            #self.m_pfnInit = getattr(self.m_module, "XSDK_Init", None)
            self.m_pfnInit      = api_entry("XSDK_Init", argtypes=[c_void_p])
            self.m_pfnExit      = api_entry("XSDK_Exit", argtypes=[])
            self.m_pfnDetect    = api_entry("XSDK_Detect", argtypes=[c_long, c_char_p, c_char_p, POINTER(c_long)])
            self.m_pfnAppend    = api_entry("XSDK_Append", argtypes=[c_long, c_char_p, c_char_p, POINTER(c_long), c_void_p])  # structure
            self.m_pfnClose     = api_entry("XSDK_Close", argtypes=[c_longlong])
            self.m_pfnOpenEx    = api_entry("XSDK_OpenEx", argtypes=[c_char_p, POINTER(c_longlong), POINTER(c_long), c_long])
            self.m_pfnPowerOFF  = api_entry("XSDK_PowerOFF", argtypes=[])

            self.m_pfnGetErrorNumber    = api_entry("XSDK_GetErrorNumber", argtypes=[c_longlong, POINTER(c_long), POINTER(c_long)])
            self.m_pfnGetVersionString  = api_entry("XSDK_GetVersionString", argtypes=[c_longlong, c_char_p])
            self.m_pfnGetErrorDetails   = api_entry("XSDK_GetErrorDetails", argtypes=[c_longlong, POINTER(c_long)])
            self.m_pfnGetDeviceInfo     = api_entry("XSDK_GetDeviceInfo", argtypes=[c_longlong, POINTER(DeviceInformation)])
            self.m_pfnWriteDeviceName   = api_entry("XSDK_WriteDeviceName", argtypes=[c_longlong, c_char_p])
            self.m_pfnGetFirmwareVersion = api_entry("XSDK_GetFirmwareVersion", argtypes=[c_longlong, c_char_p])
            self.m_pfnGetLensInfo       = api_entry("XSDK_GetLensInfo", argtypes=[c_longlong, POINTER(LensInformation)])
            self.m_pfnGetLensVersion    = api_entry("XSDK_GetLensVersion", argtypes=[c_longlong, c_char_p])
            self.m_pfnGetDeviceInfoEx   = api_entry("XSDK_GetDeviceInfoEx", argtypes=[c_longlong, c_void_p, POINTER(c_long), POINTER(c_long)])  #structure

            self.m_pfnCapPriorityMode   = api_entry("XSDK_CapPriorityMode", argtypes=[c_longlong, POINTER(c_long), POINTER(c_long)])
            self.m_pfnSetPriorityMode   = api_entry("XSDK_SetPriorityMode", argtypes=[c_longlong, c_long])
            self.m_pfnGetPriorityMode   = api_entry("XSDK_GetPriorityMode", argtypes=[c_longlong, POINTER(c_long)])
            self.m_pfnCapRelease        = api_entry("XSDK_CapRelease", argtypes=[c_longlong, POINTER(c_long), POINTER(c_long)])
            self.m_pfnRelease           = api_entry("XSDK_Release", argtypes=[c_longlong, c_long, POINTER(c_long), POINTER(c_long)])
            self.m_pfnGetReleaseStatus  = api_entry("XSDK_GetReleaseStatus", argtypes=[c_longlong, POINTER(c_long)])
            self.m_pfnCapReleaseEx      = api_entry("XSDK_CapReleaseEx", argtypes=[c_longlong, POINTER(c_long), POINTER(c_long)])
            self.m_pfnReleaseEx         = api_entry("XSDK_ReleaseEx", argtypes=[c_longlong, c_long, POINTER(c_long), POINTER(c_long)])
            self.m_pfnCapReleaseStatus  = api_entry("XSDK_CapReleaseStatus", argtypes=[c_longlong, POINTER(c_long), POINTER(c_long)])
            self.m_pfnReadImageInfo     = api_entry("XSDK_ReadImageInfo", argtypes=[c_longlong, POINTER(ImageInformation)])
            self.m_pfnReadPreview       = api_entry("XSDK_ReadPreview", argtypes=[c_longlong, c_void_p, c_long])    # buffer
            self.m_pfnReadImage         = api_entry("XSDK_ReadImage", argtypes=[c_longlong, c_void_p, c_long])      # buffer
            self.m_pfnDeleteImage       = api_entry("XSDK_DeleteImage", argtypes=[c_longlong])
            self.m_pfnGetBufferCapacity = api_entry("XSDK_GetBufferCapacity", argtypes=[c_longlong, POINTER(c_long), POINTER(c_long)])

            self.m_pfnCapAEMode       = api_entry("XSDK_CapAEMode", argtypes=[c_longlong, POINTER(c_long), POINTER(c_long)])
            self.m_pfnSetAEMode       = api_entry("XSDK_SetAEMode", argtypes=[c_longlong, c_long])
            self.m_pfnGetAEMode       = api_entry("XSDK_GetAEMode", argtypes=[c_longlong, POINTER(c_long)])
            self.m_pfnCapShutterSpeed = api_entry("XSDK_CapShutterSpeed", argtypes=[c_longlong, POINTER(c_long), POINTER(c_long)])
            self.m_pfnSetShutterSpeed = api_entry("XSDK_SetShutterSpeed", argtypes=[c_longlong, c_long])
            self.m_pfnGetShutterSpeed = api_entry("XSDK_GetShutterSpeed", argtypes=[c_longlong, POINTER(c_long), POINTER(c_long)])
            self.m_pfnCapExposureBias = api_entry("XSDK_CapExposureBias", argtypes=[c_longlong, POINTER(c_long), POINTER(c_long)])
            self.m_pfnSetExposureBias = api_entry("XSDK_SetExposureBias", argtypes=[c_longlong, c_long])
            self.m_pfnGetExposureBias = api_entry("XSDK_GetExposureBias", argtypes=[c_longlong, POINTER(c_long)])
            self.m_pfnCapDynamicRange = api_entry("XSDK_CapDynamicRange", argtypes=[c_longlong, POINTER(c_long), POINTER(c_long)])
            self.m_pfnSetDynamicRange = api_entry("XSDK_SetDynamicRange", argtypes=[c_longlong, c_long])
            self.m_pfnGetDynamicRange = api_entry("XSDK_GetDynamicRange", argtypes=[c_longlong, POINTER(c_long)])
            self.m_pfnCapSensitivity  = api_entry("XSDK_CapSensitivity", argtypes=[c_longlong, POINTER(c_long), POINTER(c_long)])
            self.m_pfnSetSensitivity  = api_entry("XSDK_SetSensitivity", argtypes=[c_longlong, c_long])
            self.m_pfnGetSensitivity  = api_entry("XSDK_GetSensitivity", argtypes=[c_longlong, POINTER(c_long)])
            self.m_pfnCapMeteringMode = api_entry("XSDK_CapMeteringMode", argtypes=[c_longlong, POINTER(c_long), POINTER(c_long)])
            self.m_pfnSetMeteringMode = api_entry("XSDK_SetMeteringMode", argtypes=[c_longlong, c_long])
            self.m_pfnGetMeteringMode = api_entry("XSDK_GetMeteringMode", argtypes=[c_longlong, POINTER(c_long)])
            self.m_pfnCapLensZoomPos  = api_entry("XSDK_CapLensZoomPos", argtypes=[c_longlong, POINTER(c_long), c_void_p, c_void_p])
            self.m_pfnGetLensZoomPos  = api_entry("XSDK_GetLensZoomPos", argtypes=[c_longlong, POINTER(c_long)])
            self.m_pfnSetLensZoomPos  = api_entry("XSDK_SetLensZoomPos", argtypes=[c_longlong, c_long])
            self.m_pfnCapAperture     = api_entry("XSDK_CapAperture", argtypes=[c_longlong, c_long, POINTER(c_long), c_void_p])
            self.m_pfnSetAperture     = api_entry("XSDK_SetAperture", argtypes=[c_longlong, c_long])
            self.m_pfnGetAperture     = api_entry("XSDK_GetAperture", argtypes=[c_longlong, POINTER(c_long)])
            self.m_pfnCapWBMode       = api_entry("XSDK_CapWBMode", argtypes=[c_longlong, POINTER(c_long), POINTER(c_long)])
            self.m_pfnSetWBMode       = api_entry("XSDK_SetWBMode", argtypes=[c_longlong, c_long])
            self.m_pfnGetWBMode       = api_entry("XSDK_GetWBMode", argtypes=[c_longlong, POINTER(c_long)])
            self.m_pfnCapWBColorTemp  = api_entry("XSDK_CapWBColorTemp", argtypes=[c_longlong, POINTER(c_long), POINTER(c_long)])
            self.m_pfnSetWBColorTemp  = api_entry("XSDK_SetWBColorTemp", argtypes=[c_longlong, c_long])
            self.m_pfnGetWBColorTemp  = api_entry("XSDK_GetWBColorTemp", argtypes=[c_longlong, POINTER(c_long)])
            self.m_pfnCapMediaRecord  = api_entry("XSDK_CapMediaRecord", argtypes=[c_longlong, POINTER(c_long), POINTER(c_long)])
            self.m_pfnSetMediaRecord  = api_entry("XSDK_SetMediaRecord", argtypes=[c_longlong, c_long])
            self.m_pfnGetMediaRecord  = api_entry("XSDK_GetMediaRecord", argtypes=[c_longlong, POINTER(c_long)])
            self.m_pfnCapForceMode    = api_entry("XSDK_CapForceMode", argtypes=[c_longlong, POINTER(c_long), POINTER(c_long)])
            self.m_pfnSetForceMode    = api_entry("XSDK_SetForceMode", argtypes=[c_longlong, c_long])
            self.m_pfnSetBackupSettings = api_entry("XSDK_SetBackupSettings", argtypes=[c_longlong, c_long, c_void_p])
            self.m_pfnGetBackupSettings = api_entry("XSDK_GetBackupSettings", argtypes=[c_longlong, POINTER(c_long), c_void_p])
            self.m_pfnCapDriveMode    = api_entry("XSDK_CapDriveMode", argtypes=[c_longlong, POINTER(c_long), POINTER(c_long)])
            self.m_pfnSetDriveMode    = api_entry("XSDK_SetDriveMode", argtypes=[c_longlong, c_long])
            self.m_pfnGetDriveMode    = api_entry("XSDK_GetDriveMode", argtypes=[c_longlong, POINTER(c_long)])
            self.m_pfnCapMode         = api_entry("XSDK_CapMode", argtypes=[c_longlong, POINTER(c_long), POINTER(c_long)])
            self.m_pfnSetMode         = api_entry("XSDK_SetMode", argtypes=[c_longlong, c_long])
            self.m_pfnGetMode         = api_entry("XSDK_GetMode", argtypes=[c_longlong, POINTER(c_long)])

            self.m_pfnCapRecordingStatus   = api_entry("XSDK_CapRecordingStatus", None)
            self.m_pfnGetRecordingStatus   = api_entry("XSDK_GetRecordingStatus", None)
            self.m_pfnCapMovieShutterSpeed = api_entry("XSDK_CapMovieShutterSpeed", None)
            self.m_pfnSetMovieShutterSpeed = api_entry("XSDK_SetMovieShutterSpeed", None)
            self.m_pfnGetMovieShutterSpeed = api_entry("XSDK_GetMovieShutterSpeed", None)
            self.m_pfnCapMovieExposureBias = api_entry("XSDK_CapMovieExposureBias", None)
            self.m_pfnSetMovieExposureBias = api_entry("XSDK_SetMovieExposureBias", None)
            self.m_pfnGetMovieExposureBias = api_entry("XSDK_GetMovieExposureBias", None)
            self.m_pfnCapMovieSensitivity  = api_entry("XSDK_CapMovieSensitivity", None)
            self.m_pfnSetMovieSensitivity  = api_entry("XSDK_SetMovieSensitivity", None)
            self.m_pfnGetMovieSensitivity  = api_entry("XSDK_GetMovieSensitivity", None)
            self.m_pfnCapMovieAperture     = api_entry("XSDK_CapMovieAperture", None)
            self.m_pfnSetMovieAperture     = api_entry("XSDK_SetMovieAperture", None)
            self.m_pfnGetMovieAperture     = api_entry("XSDK_GetMovieAperture", None)
            self.m_pfnCapMovieDynamicRange = api_entry("XSDK_CapMovieDynamicRange", None)
            self.m_pfnSetMovieDynamicRange = api_entry("XSDK_SetMovieDynamicRange", None)
            self.m_pfnGetMovieDynamicRange = api_entry("XSDK_GetMovieDynamicRange", None)
            self.m_pfnCapMovieMeteringMode = api_entry("XSDK_CapMovieMeteringMode", None)
            self.m_pfnSetMovieMeteringMode = api_entry("XSDK_SetMovieMeteringMode", None)
            self.m_pfnGetMovieMeteringMode = api_entry("XSDK_GetMovieMeteringMode", None)
            self.m_pfnCapMovieWBMode       = api_entry("XSDK_CapMovieWBMode", None)
            self.m_pfnSetMovieWBMode       = api_entry("XSDK_SetMovieWBMode", None)
            self.m_pfnGetMovieWBMode       = api_entry("XSDK_GetMovieWBMode", None)
            self.m_pfnCapMovieWBColorTemp  = api_entry("XSDK_CapMovieWBColorTemp", None)
            self.m_pfnSetMovieWBColorTemp  = api_entry("XSDK_SetMovieWBColorTemp", None)
            self.m_pfnGetMovieWBColorTemp  = api_entry("XSDK_GetMovieWBColorTemp", None)

            self.m_pfnCapProp       = api_entry("XSDK_CapProp", argtypes=[c_longlong, c_long, c_long], restype=c_long )
            self.m_pfnSetProp       = api_entry("XSDK_SetProp", argtypes=[c_longlong, c_long, c_long], restype=c_long )
            self.m_pfnGetProp       = api_entry("XSDK_GetProp", argtypes=[c_longlong, c_long, c_long], restype=c_long )
            # Cast the generic property functions to specific function signatures
        #    self.m_pfnCapProp_PP  = cast(self.m_pfnCapProp, CFUNCTYPE(c_long, c_longlong, c_long, c_long, POINTER(c_long), POINTER(c_long)))
        #    self.m_pfnCapProp_LPP = cast(self.m_pfnCapProp, CFUNCTYPE(c_long, c_longlong, c_long, c_long, c_long, POINTER(c_long), POINTER(c_long)))
        #    self.m_pfnSetProp_L   = cast(self.m_pfnSetProp, CFUNCTYPE(c_long, c_longlong, c_long, c_long, c_long))
        #    self.m_pfnSetProp_LL  = cast(self.m_pfnSetProp, CFUNCTYPE(c_long, c_longlong, c_long, c_long, c_long, c_long))
        #    self.m_pfnGetProp_LP   = cast(self.m_pfnGetProp, CFUNCTYPE(c_long, c_longlong, c_long, c_long, POINTER(c_long)))
        #    self.m_pfnGetProp_LLP  = cast(self.m_pfnGetProp, CFUNCTYPE(c_long, c_longlong, c_long, c_long, c_long, POINTER(c_long)))
        #
        #    self.m_pfnCapProp_FocusArea = cast(self.m_pfnCapProp, CFUNCTYPE(c_long, c_longlong, c_long, c_long, c_long, POINTER(FocusArea), POINTER(FocusArea)))
        #    self.m_pfnSetProp_FocusArea = cast(self.m_pfnSetProp, CFUNCTYPE(c_long, c_longlong, c_long, c_long, c_long, POINTER(FocusArea)))
        #    self.m_pfnGetProp_FocusArea = cast(self.m_pfnGetProp, CFUNCTYPE(c_long, c_longlong, c_long, c_long, c_long, POINTER(FocusArea)))
        #    self.m_pfnCapProp_LensFocus = cast(self.m_pfnCapProp, CFUNCTYPE(c_long, c_longlong, c_long, c_long, POINTER(FocusPosCaps)))

            self.m_err = FUJI_SDK_ERR_OK
        except OSError as e:
            self.m_module = None
            self.err = FUJI_SDK_ERR_LOADSDK
        return

    def get_error(self):
        return self.m_err
    
    def get_module(self):
        return self.m_module
    
# end of code