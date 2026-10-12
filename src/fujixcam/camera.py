"""Camera class for FUJIFILM Camera control and operations."""
# -----------------------------------------------------
# camera.py :
#  Camera Class simplifies camera controls and operations 
#
# Copyright 2026 Masahiro Terada (@mterada.com)
# This software is released under the MIT License.
# http://opensource.org/licenses/mit-license.php
# -----------------------------------------------------
import time, copy, threading
from typing import Dict, Any
from dataclasses import dataclass, field, asdict

import logging
logger = logging.getLogger(__name__)
DEFAULT_LOG_LEVEL = "warning"

from fujixcam import CameraAPI
from fujixcam.results import *
from fujixcam.camera_api_dictionary import *

class Camera:
    """FUJIFILM X/GFX-Series Camera control interface.

    This class provides a high-level Python API for controlling FUJIFILM X/GFX-Series cameras connected via USB/Wifi.
    It wraps the manufacturer's SDK to provide simple, Pythonic access to camera operations.

    Example:
        >>> import fujixcam
        >>> camera = fujixcam.Camera()      # initialize and connect to camera
        >>> print(camera.get_config())      # get current camera settings and available options
        >>> camera.setup(program_mode="P", iso_sensitivity="ISO 6400", exposure_compensation="+1.0EV")
        >>> result = camera.capture()       # capture an image and transfer it to the computer storage
        >>> print(result.success, result.file_name, result.file_size)
    """
    _creation_lock: threading.Lock = threading.Lock()  # for thread-safe creation 
    _creation_time: float = time.time()

    @dataclass
    class _CameraSettings:
        exposure: ExposureSettings = field(default_factory=ExposureSettings)
        focus: FocusSettings = field(default_factory=FocusSettings)
        image: ImageSettings = field(default_factory=ImageSettings)
        #color: ColorSettings = field(default_factory=ColorSettings)  # not implemented yet
        liveview: LiveviewSettings = field(default_factory=LiveviewSettings)
    
    @dataclass
    class _CameraOptions:
        exposure: ExposureOptions = field(default_factory=ExposureOptions)
        focus: FocusOptions = field(default_factory=FocusOptions)
        image: ImageOptions = field(default_factory=ImageOptions)
        #color: ColorOptions = field(default_factory=ColorOptions)  # not implemented yet
        liveview: LiveviewOptions = field(default_factory=LiveviewOptions)

    @dataclass
    class SetupKeys:
        PROGRAM_MODE = "program_mode"
        ISO_SENSITIVITY = "iso_sensitivity"
        APERTURE = "aperture"
        SHUTTER_SPEED = "shutter_speed"
        EXPOSURE_COMPENSATION = "exposure_compensation"
        FOCUS_MODE = "focus_mode"
        AF_MODE = "af_mode"
        MF_DISTANCE = "mf_distance"
        AF_AREA_SIZE = "af_area_size"

    def __init__(self, device_id: Any = None, wait_for_connection: bool = True, keep_alive: bool = False, log_level: str = DEFAULT_LOG_LEVEL):
        """Initialize Camera object and connect to camera.

        Args:
            wait_for_connection: Whether to wait and retry until camera connection is successful (default: True)
            log_level: Logging level for camera operations (default: "warning", options: "info", "warning", "error", "none")

        Note: device_id and keep_alive are not used in the current implementation.
            device_id: Camera device ID string (optional:not used in current implementtation)
            keep_alive: Whether to keep the camera connection alive in a background thread (default: False)

        If not wait_for_connection when camera is not connected or if camera will disconnect after initialization,
            reconnect() method can be called manually to establish the connection.

        Raises:
            RuntimeError: If CameraAPI loading fails, or if camera initialization fails during operations.
        """
        level = {"debug":logging.DEBUG, "info":logging.INFO, "warning":logging.WARNING, "error":logging.ERROR, "none":logging.CRITICAL }.get(log_level, logging.WARNING)
        logging.basicConfig(format='[%(asctime)s] %(levelname)s: %(message)s')
        logging.getLogger().setLevel(level)

        # camera api handler
        self.product_name: str = "unknown"
        self._device_id: Any = device_id
        self._handle: CameraAPI

        # lens information
        self._zoom_position: int = 0
        self._zoom_options_dict: Dict[int,str] = {}

        # inner status flags
        self._live_pausing: bool = False     # live view is temporarily paused (e.g., for capturing preview image)

        # camera status flags
        self._camera_status = CameraStatus()  # camera status flags
        #   is_ready
        #   conditions 

        # cached settings and their available options
        self._settings = Camera._CameraSettings()
        #   exposure   = { "program_mode": "M", "aperture": "F2.8", "shutter_speed": "1/60", "exposure_compensation": "+0.0EV", "iso_sensitivity": "ISO 200" } 
        #   focus      = { "focus_mode": "AF-S", "af_point": (0,0), "af_area_size": 1 }
        #   image      = { "image_quality": "RAW+FINE", "image_size": "L 3:2" }
        #   liveview   = { "liveview_size": "L", "liveview_quality": "FINE", "liveview_zoom": "x1.0" }
        self._backup_settings = None  # backup of settings for restoring when disconnecting

        self._options  = Camera._CameraOptions()
        #   exposure   = { "program_mode": ["P", "A", "S", "M"], "aperture": ["F1.4", "F2.0", ...], "shutter_speed": ["1/4000", "1/2000", ...], "exposure_compensation": ["-3.0EV", "-2.7EV", ...], "iso_sensitivity": ["ISO 100", "ISO 200", ...] }
        #   focus      = { "focus_mode": ["AF-S", "AF-C", "MF"], "af_point_h": [-1, 0, 1], "af_point_v": [-1, 0, 1], "af_area_size": ["Small", "Medium", "Large"] }
        #   image      = { "image_quality": ["FINE", "NORMAL", "RAW+FINE"], "image_size": ["L 3:2", "M 3:2", "S 3:2"] }
        #   liveview   = { "liveview_size": ["L", "M", "S"], "liveview_quality": ["FINE", "NORMAL"], "liveview_zoom": ["x1.0", "x2.5", ...] }
        #   monitor    : not implemented yet, but can be added later if needed
        self._options_dict: Dict[str, Dict[str, int]] = { "aperture": {}, "shutter_speed": {} } 
        #   dict = { "aperture": {"F1.4": 140, "F2.0": 200, ...}, "shutter_speed": {...} }

        with Camera._creation_lock:
            self._lock = threading.Lock()  # for thread safety
            self._device_id = device_id
            try:
                self._handle = CameraAPI() 
                if self._handle is None:
                    raise RuntimeError("Failed to create camera API handle")
                logger.info("camera api/sdk loaded successfully")
                if log_level == "DEBUG":
                    self._handle._DEBUG_ = 2    # type: ignore
                elif log_level == "INFO":
                    self._handle._DEBUG_ = 1    # type: ignore
                self._connect( wait_for_connection=wait_for_connection, keep_alive=keep_alive, device_id=device_id )
            except Exception as e:
                logger.error(f"Failed to initialize camera API: {e}")
                self._disconnect()
                raise RuntimeError("Camera initialization failed") from e

    def _connect(self, wait_for_connection:bool, keep_alive:Optional[bool], device_id:Any )-> None:
        """Establish connection to camera (optional retrying until successful)
            and query initial settings and options to populate the cache.

        Raises:
            RuntimeError: If connection fails.
        """
        if wait_for_connection:
            logger.info(f"Waiting for camera connection ({device_id or 'default'})...")
        while True:
            connection_result = self._handle.connect()  # device_id is not supported in the current implementation
            if connection_result.success:
                # store CAMERA/LENS name as device name for display
                self.product_name = connection_result.data["camera_name"] + "/" + connection_result.data["lens_name"]
                logger.info(f"connected to Camera: {self.product_name}")
                break
            elif not wait_for_connection:
                #raise RuntimeError("Failed to connect to camera: " + connection_result.error_message)
                logger.info(f"camera is not connected ({device_id or 'default'}). Connect a camera then call reconnect() to retry.")
                return
            time.sleep(1)

        # query current settings and options to populate the cache, which will be used for validation and conversion in the operations
        self._query_settings()
        self._query_options()

        # log_level: debug
        self._debug_print_settings()
        self._debug_print_options()

        # backup current settings for restoring later if needed (e.g., when disconnecting)
        self._backup_settings = copy.deepcopy(self._settings)
        self.get_status()  # update camera status

        # keep_alive : Not implemented
        if keep_alive:
            logger.warning("keep_alive is requested but not implemented in the current version.")

        return

    def _disconnect(self, forced=False, shutdown=False) -> None:
        """Disconnect from camera and release SDK resources.
        shutdown: Whether to power off the camera after disconnection.
        forced: Whether to force disconnection without restoring settings.(on irregularly deleted camera object)

        1. restore settings from backup if needed
        2. Close camera connection
        3. Release resouces
        """
        if hasattr(self, "_handle") and self._handle is not None:
            if not forced:
                if self._handle.is_connected():
                    logger.info("Restoring camera settings from backup before disconnection.")
                    self._restore_settings_from_backup()
                else:
                    logger.info("Camera is not connected. Skipping restoration of settings.")
                self._handle.disconnect(shutdown=shutdown)  # shutdown option is available
            else:
                logger.warning("Forcing camera disconnection without restoring settings.")
                self._handle.disconnect(forced=forced)   # emergency disconnection without any commands

            logger.info("Camera connection closed. ({})".format("forced" if forced else "normal"))
            self.product_name = "Unknown"
            self._device_id = None
            self._handle = None  # type: ignore[assignment]

    #  query current settings and available options to initialize the cache
    def _query_settings(self):
        #
        # Exposure settings contains program mode, aperture, shutter speed, exposure compensation, and ISO sensitivity
        #
        res = self._handle.get_program_mode()
        if not res.success:
            logger.error(f"Failed to get program mode: {res.error_message}")
            return False
        self._settings.exposure.program_mode = program_mode_value_to_string(res.value )
        self._query_exposure_settings_by_program_mode()
        #
        # Focus settings contains focus mode, mf distance or af mode, af area size, and af point.
        #
        res = self._handle.get_focus_mode()
        if not res.success:
            logger.error(f"Failed to get focus mode: {res.error_message}")
            return False
        self._settings.focus.focus_mode = focus_mode_value_to_string(res.value)
        self._query_focus_settings_by_focus_mode()
        #
        # Image settings contains image format  (JPEG, RAW, ...)
        #
        self._settings.image.image_quality = image_quality_value_to_string(self._handle.get_image_quality().value)
        self._settings.image.image_size    = image_size_value_to_string(self._handle.get_image_size().value)
        #
        # liveview settings contains image quality and image size
        #
        self._settings.liveview.liveview_quality = liveview_quality_value_to_string(self._handle.get_liveview_quality().value)
        self._settings.liveview.liveview_size    = liveview_size_value_to_string(self._handle.get_liveview_size().value)
        # liveview_zoom setting is set by _query_focus_settings_by_focus_mode
        #
        # Zoom position
        self._zoom_position = self._handle.get_lens_zoom().value

        return True

    def _query_exposure_settings_by_program_mode(self):
        # Query exposure settings based on the current program mode
        program_mode = self._settings.exposure.program_mode
        logger.debug(f"Querying exposure settings for program mode: {program_mode}")
        # APERTURE setting is only available in Manual mode and Aperture Priority mode
        if program_mode in ['M', 'A']:
            self._settings.exposure.aperture = aperture_value_to_string(self._handle.get_aperture_value().value)
        # SHUTTER_SPEED setting is only available in Manual mode and Shutter Priority mode
        if program_mode in ['M', 'S']:
            self._settings.exposure.shutter_speed = shutter_speed_value_to_string(self._handle.get_shutter_speed().value)
        # EXPOSURE_COMPENSATION setting is only available in Program mode, Aperture Priority mode, and Shutter Priority mode
        if program_mode in ['P', 'A', 'S']:
            self._settings.exposure.exposure_compensation = exposure_compensation_value_to_string(self._handle.get_exposure_compensation().value)
        # ISO_SENSITIVITY setting is available in all modes (Manual, Aperture Priority, Shutter Priority, Program)
        if program_mode in ['M', 'A', 'S', 'P']:
            self._settings.exposure.iso_sensitivity = iso_sensitivity_value_to_string(self._handle.get_iso_sensitivity().value)
        return

    def _query_focus_settings_by_focus_mode(self):
        # Query focus settings based on the current focus mode
        focus_mode = self._settings.focus.focus_mode
        logger.debug(f"Querying focus settings for focus mode: {focus_mode}")
        # MF_DISTANCE is only relevant when focus mode is MF (manual focus)
        if focus_mode in ['MF']:
            self._settings.focus.mf_distance = self._handle.get_focus_distance().value
        # AF_MODE and AF_AREA settings are relevant for autofocus modes (except for instant AF in MF mode)
        if focus_mode in ['MF', 'AF-S', 'AF-C' ]:
            # if focus mode is MF, af_mode returns 'SINGLE' by default because instant AF behaves as single point AF
            self._settings.focus.af_mode = focus_afmode_value_to_string(self._handle.get_focus_afmode().value)
            self._query_focus_settings_by_af_mode()
        return

    def _query_focus_settings_by_af_mode(self):
        # Query focus settings based on the current AF mode
        af_mode = self._settings.focus.af_mode
        logger.debug(f"Querying focus settings for AF mode: {af_mode}")
        # if focus mode is MF, af_mode returns 'SINGLE' by default because instant AF behaves as single point AF
        data = {"size":0, "h":0, "v":0}
        if af_mode in [ 'SINGLE', 'ZONE']:
            res = self._handle.get_focus_area()
            if res.success:
                data.update( res.data )
        self._settings.focus.af_area_size = focus_size_value_to_string(data["size"])
        self._settings.focus.af_point = (data["h"], data["v"])
        # af_mode affects liveview zoom (finder crop) capability
        if af_mode in ['SINGLE']:  # SINGLE includes single point AF and MF
            self._settings.liveview.liveview_zoom = finder_crop_value_to_string(self._handle.get_finder_crop().value)
        else:
            self._settings.liveview.liveview_zoom = finder_crop_value_to_string(FINDER_CROP_DEFAULT)
        return

    def _debug_print_settings(self, settings: _CameraSettings|None=None):
        if settings is None:
            settings = self._settings
        logger.debug(f"Queried camera settings:\n\
            - program_mode={settings.exposure.program_mode},\n\
            - aperture={settings.exposure.aperture if settings.exposure.program_mode in ['M', 'A'] else 'AUTO'},\n\
            - shutter_speed={settings.exposure.shutter_speed if settings.exposure.program_mode in ['M', 'S'] else 'AUTO'},\n\
            - exposure_compensation={settings.exposure.exposure_compensation},\n\
            - iso_sensitivity={settings.exposure.iso_sensitivity},\n\
            - focus_mode={settings.focus.focus_mode},\n\
            - mf_distance={settings.focus.mf_distance if settings.focus.focus_mode == 'MF' else 'AUTO'},\n\
            - af_mode={settings.focus.af_mode},\n\
            - af_point={settings.focus.af_point}, size={settings.focus.af_area_size},\n\
            - liveview_zoom/size/quality={settings.liveview.liveview_zoom}/{settings.liveview.liveview_size}/{settings.liveview.liveview_quality},\n\
            - image_size/quality={settings.image.image_size}/{settings.image.image_quality}\n" )

    def _query_options(self):
        # query level: stable options/ reactive options / highly volatile options
        #
        # program mode options
        #
        program_mode = self._settings.exposure.program_mode
        res = self._handle.get_program_mode_options()
        if not res.success:
            logger.error(f"Failed to get program mode options: {res.error_message}")
            return False
        self._options.exposure.program_mode = [program_mode_value_to_string(s) for s in res.options]
        self._query_exposure_options_by_program_mode()
        #
        # fucus mode options
        #
        res = self._handle.get_focus_mode_options()
        if not res.success:
            logger.error(f"Failed to get focus mode options: {res.error_message}")
            return False
        self._options.focus.focus_mode = [focus_mode_value_to_string(v) for v in res.options]
        self._query_focus_options_by_focus_mode()
        #
        # Image settings contains image format  (JPEG, RAW, JPEG+RAW,...)
        #
        res = self._handle.get_image_quality_options()
        if not res.success:
            logger.error(f"Failed to get image quality options: {res.error_message}")
            return False
        self._options.image.image_quality = [image_quality_value_to_string(v) for v in res.options]

        res = self._handle.get_image_size_options()
        self._options.image.image_size = [image_size_value_to_string(v) for v in res.options]
        #
        # liveview size and quality options
        #
        res = self._handle.get_liveview_quality_options()                                       
        self._options.liveview.liveview_quality = [liveview_quality_value_to_string(v) for v in res.options]
        res = self._handle.get_liveview_size_options()
        self._options.liveview.liveview_size = [liveview_size_value_to_string(v) for v in res.options]
        # af_mode affects liveview zoom (finder crop) capability
        #
        # zoom lens options
        res = self._handle.get_lens_zoom_capability()
        self._zoom_options_dict = dict(zip(res.data["options"], [ str(v/100)+"mm" for v in res.data["actual_length"]]))

        return True

    def _query_exposure_options_by_program_mode(self):
        program_mode = self._settings.exposure.program_mode
        # APERTURE setting is only available in Manual mode and Aperture Priority mode
        if program_mode in ["M", "A"]:
            res = self._handle.get_aperture_value_options()   # Note: variable by lens zoom position
            if res.success: # and not res.is_volatile:
                self._options.exposure.aperture = [ aperture_value_to_string(v) for v in res.options ]
                self._options_dict["aperture"] = dict(zip(self._options.exposure.aperture, res.options))  # reverse mapping of the subset of APERTURE_DICT
                # record the current zoom position affecting aperture options
                self._zoom_position = self._handle.get_lens_zoom().value

        # SHUTTER_SPEED setting is only available in Manual mode and Shutter Priority mode
        if program_mode in ["M", "S"]:
            res = self._handle.get_shutter_speed_options()
            if res.success: # and not res.is_volatile:
                self._options.exposure.shutter_speed = [ shutter_speed_value_to_string(v) for v in res.options ]
                self._options_dict["shutter_speed"] = dict(zip(self._options.exposure.shutter_speed, res.options))  # reverse mapping of the subset of SHUTTER_SPEED_DICT

        # EXPOSURE COMPENSATION setting is only available in Program mode, Shutter Priority mode, and Aperture Priority mode
        if program_mode in ["P", "S", "A"]:
            res = self._handle.get_exposure_compensation_options()
            self._options.exposure.exposure_compensation = [exposure_compensation_value_to_string(v) for v in res.options ]

        # ISO_SENSITIVITY setting is available in all modes
        if program_mode in ["P", "S", "A", "M"]:
            res = self._handle.get_iso_sensitivity_options()
            self._options.exposure.iso_sensitivity = [iso_sensitivity_value_to_string(v) for v in res.options ]

    # _query_settings, _query_options must be called before this method to prepare the previous zoom position and options
    def _fetch_aperture_settings_and_options(self):
        # Fetch and update aperture settings and options based on the current zoom position.
        # User manipulation of the zoom lens may affect the current aperture settings and available options.
        if len(self._zoom_options_dict) > 1 and self._zoom_position != self._handle.get_lens_zoom().value:
            # Update aperture settings and options when zoom position changes
            self._zoom_position = self._handle.get_lens_zoom().value
            self._settings.exposure.aperture = aperture_value_to_string(self._handle.get_aperture_value().value)
            self._options.exposure.aperture= [aperture_value_to_string(v) for v in self._handle.get_aperture_value_options().options ]
            logger.info("Updated aperture settings and options based on zoom position change.")
        else:
            logger.debug("Aperture settings and options are up-to-date; no zoom position change detected.")

    def _query_focus_options_by_focus_mode(self):
        # MF_DISTANCE is only relevant when focus mode is MF (manual focus)
        focus_mode = self._settings.focus.focus_mode
        if focus_mode in ["MF"]:
            range = self._handle.get_focus_distance_range().data
            #self._options.focus.mf_distance = range.get("mod",0), range.get("inf",0), -max(range.get("step",0), range.get("dof",0), 1)
            self._options.focus.mf_distance = (range.get("inf",0), range.get("mod",0), max(range.get("step",0), range.get("dof",0), 1))
        else:
            self._options.focus.mf_distance = (0, 0, 0)  # not applicable in AF modes

        # AF_MODE options are relevant for autofocus modes (AF-S, AF-C)
        if focus_mode in ['AF-S', 'AF-C']:
            res = self._handle.get_focus_afmode_options()
            self._options.focus.af_mode = [focus_afmode_value_to_string(v) for v in res.options]
        else:
            self._options.focus.af_mode = []    # not applicable in MF mode
        # Query additional focus options based on the current AF mode
        self._query_focus_options_by_af_mode()

    def _query_focus_options_by_af_mode(self):
        # Query focus options based on the current AF mode
        af_mode = self._settings.focus.af_mode
        if af_mode in ['SINGLE', 'ZONE']:  # SINGLE and ZONE AF modes have configurable focus areas
            area_options = self._handle.get_focus_area_options().data   # including h:[], v:[], size:[], points
            self._options.focus.af_point_h   = area_options["h"]
            self._options.focus.af_point_v   = area_options["v"]
            self._options.focus.af_area_size = [focus_size_value_to_string(v) for v in area_options["size"]]
        else:
            self._options.focus.af_point_h   = []
            self._options.focus.af_point_v   = []
            self._options.focus.af_area_size = []
        # af_mode affects liveview zoom (finder crop) capability
        if af_mode in ['SINGLE']:   # SINGLE includes single point AF and MF
            res = self._handle.get_finder_crop_options()
            self._options.liveview.liveview_zoom = [finder_crop_value_to_string(v) for v in res.options]
        else:
            # not applicable in other AF modes
            self._options.liveview.liveview_zoom = [] # [finder_crop_value_to_string(FINDER_CROP_DEFAULT)] 
         
    def _debug_print_options(self, options: _CameraOptions|None=None):
        if options is None:
            options = self._options
        logger.debug(f"Queried camera options:\n\
            - program_mode={options.exposure.program_mode},\n\
            - aperture={options.exposure.aperture if self._settings.exposure.program_mode in ['M', 'A'] else 'AUTO'},\n\
            - shutter_speed={options.exposure.shutter_speed if self._settings.exposure.program_mode in ['M', 'S'] else 'AUTO'},\n\
            - exposure_compensation={options.exposure.exposure_compensation},\n\
            - iso_sensitivity={options.exposure.iso_sensitivity},\n\
            - focus_mode={options.focus.focus_mode},\n\
            - mf_distance={options.focus.mf_distance if self._settings.focus.focus_mode == 'MF' else 'AUTO'},\n\
            - af_mode={options.focus.af_mode},\n\
            - af_point=({options.focus.af_point_h},{options.focus.af_point_v}), size={options.focus.af_area_size},\n\
            - liveview_zoom/size/quality={options.liveview.liveview_zoom}/{options.liveview.liveview_size}/{options.liveview.liveview_quality},\n\
            - image_size/quality={options.image.image_size}/{options.image.image_quality}\n" )

    def _restore_settings_from_backup(self):
        # reset the camera to the original settings (best effort)
        if self._backup_settings == None:
            logger.warning("No backup settings available to restore.")
            return

        # restore shooting settings (program mode first since it affects the availability of other settings)
        self._handle.set_program_mode( string_to_program_mode_value(self._backup_settings.exposure.program_mode) )
        if self._backup_settings.exposure.aperture is not None:
            self._handle.set_aperture_value( self._convert_to_sdk_value("aperture", self._backup_settings.exposure.aperture) )
        if self._backup_settings.exposure.shutter_speed is not None:
            self._handle.set_shutter_speed( self._convert_to_sdk_value("shutter_speed", self._backup_settings.exposure.shutter_speed) )
        self._handle.set_exposure_compensation( string_to_exposure_compensation_value(self._backup_settings.exposure.exposure_compensation) )
        self._handle.set_iso_sensitivity( string_to_iso_sensitivity_value(self._backup_settings.exposure.iso_sensitivity) )

        # restore focus settings
        self._handle.set_focus_mode( string_to_focus_mode_value(self._backup_settings.focus.focus_mode) )
        focus_area_h, focus_area_v = self._backup_settings.focus.af_point
        focus_area_size            = string_to_focus_size_value(self._backup_settings.focus.af_area_size)
        self._handle.set_focus_area( focus_area_h, focus_area_v, focus_area_size )

        # restore image settings
        self._handle.set_image_quality( string_to_image_quality_value(self._backup_settings.image.image_quality) )
        self._handle.set_image_size( string_to_image_size_value(self._backup_settings.image.image_size) )
        return

    # Reason why this helper function required for aperture and shutter speed rather than string_to_sdk_value():
    #   Actual options is subset of the predefined dictionary, and the mapping is not always one-to-one in these parameters.
    def _convert_to_sdk_value(self, param_name, string_name ) -> Any:
        # ex.)_convert_to_sdk_value("shutter_speed", "1/60") -> 15625 (SDK value for 1/60sec)
        #     _options_dict["shutter_speed"] = { "1/60": 15625, ... }  (reverse mapping of the subset of SHUTTER_SPEED_DICT)
        sdk_value = self._options_dict[param_name].get(string_name, None)
        if sdk_value is None:
            logger.debug(f"{param_name} string '{string_name}' to value : not found in options dict.")
        return sdk_value

    def is_connected(self) -> bool:
        """Check if the camera is currently connected by actually querying the camera hardware.
        Returns:
            - True if connected, False otherwise
        """
        if self._handle is None:
            raise RuntimeError("Camera object is no longer valid. New Camera object required.")
            return False
        return self._handle.is_connected()  # update connection status

    def reconnect(self, wait_for_connection: bool = True, keep_alive: Optional[bool] = False) -> bool:
        """Reconnect to the camera if it is disconnected.
        Args:
            wait_for_connection: Whether to wait and retry until camera connection is successful (default: True)
            keep_alive: Not implemented in this version (default: False)
        
        Returns:
            - True if reconnection is successful, False otherwise
        """
        if self.is_connected():
            #self._handle.reset_status()
            self._handle.disconnect()  # disconnect first if already connected
        try:
            self._connect(wait_for_connection=wait_for_connection, keep_alive=keep_alive, device_id=self._device_id)
            return True
        except RuntimeError as e:
            logger.error(f"Failed to reconnect to camera: {e}")
            return False
    
    def get_status(self) -> ResultStatus:
        """Get camera status which indicates whether the camera is ready and what conditions it is in.
        Returns:
            - success: Operation success flag (always True for this method)
            - error_message: Error details if failed (always None for this method)
            - camera_status: Current camera status Whether the camera is ready for shooting, list of conditions
        """
        if not self.is_connected():
            return ResultStatus(success=True, error_message="Camera is not connected", 
                                camera_status=CameraStatus(is_ready=False, conditions=["disconnected"]) )

        #with self._lock:
        res = self._handle.get_status()     # camera_status = { "buffered":(0,0), "AFL":True/False, "LiveView":True/False, ... }
        if not res.success:
            return ResultStatus(success=False, error_message=res.error_message)

        device_status = res.data
        camera_status = CameraStatus()

        camera_status.buffer_count = device_status.get("buffered", (0,0))[1]    # get the number of empty images in the camera buffer
        if device_status.get("liveview", False):
            camera_status.conditions.append("liveviewing")
        if device_status.get("shooting", False):
            camera_status.conditions.append("shooting")
        if device_status.get("bulb", False):
            camera_status.conditions.append("bulb_capturing")
        if device_status.get("pre_af", False) or device_status.get("AF", False):
            camera_status.conditions.append("focusing")
        if device_status.get("AFL", False):
            camera_status.conditions.append("af_locked")
        if device_status.get("AEL", False):
            camera_status.conditions.append("ae_locked")
        if device_status.get("WBL", False):
            camera_status.conditions.append("awb_locked")

        camera_status.is_ready = camera_status.buffer_count > 0 and not device_status.get("shooting", False) and not device_status.get("bulb", False) 
        logger.info(f"Camera status: is_ready={camera_status.is_ready}, buffer_count={camera_status.buffer_count}, conditions={camera_status.conditions}")
        self._camera_status = camera_status
        return ResultStatus(success=True, error_message=None, camera_status=CameraStatus(**asdict(camera_status)))

    def get_config(self) -> ResultConfig:
        """Get cached camera settings and available options.

        This method NOT communicate with the camera hardware. Instead, it returns the cached information for quick access.
        The cache is updated whenever setup() is called to change settings, or can be manually refreshed by calling setup() with no changes.

        Returns:
            - success: Operation success flag
            - error_message: Error details if failed
            - settings: Current shooting parameters
                (settings["exposure"], settings["focus"], settings["image"] etc.)
            - options: Available options for each setting based on current camera state
                (options["exposure"], options["focus"], options["image"] etc.)
        Example:
            >>> result = camera.get_config()
            >>> print(result.settings["exposure"].program_mode)
            >>> print(result.options["exposure"].aperture)
        """
        # refresh the cached settings and options before returning them
        if not self.is_connected():
            return ResultConfig(success=False, error_message="Camera is not connected")

        with self._lock:
            self._query_settings()
            self._query_options()
            return self._build_config()

    def revert(self) -> ResultConfig:
        """Revert camera settings to the last connected state.

        Returns:
            - success: Operation success flag
            - error_message: Error details if failed
            - settings: Shooting parameters after reverting
            - options: Available options for each setting based on reverted camera state
        """
        if not self.is_connected():
            return ResultConfig(success=False, error_message="Camera is not connected")

        with self._lock:
            logger.info("Reverting camera settings to the last connected state.")
            self._handle.reset_status()
            self._restore_settings_from_backup()
            return self._build_config()


    def setup(self, **kwargs) -> ResultConfig:
        """Configure camera settings about shooting parameters.
            Settings are applied to the camera and persist for subsequent captures until changed.
            Available settings and their valid values can be queried using get_status().

        Args:
            **kwargs: Camera settings as keyword arguments.
                Common settings:
                - program_mode: Exposure program  (e.g., "P", "A", "S", "M")
                - iso_sensitivity: ISO mode       (e.g., "ISO 200", "ISO 400", "ISO 800")
                - aperture: Aperture f-stop value (e.g., "F2.8", "F4.0", "F5.6")
                - shutter_speed: Shutter speed    (e.g., "1/60")
                - exposure_compensation: +-EV     (e.g., "+1.0EV", "-0.7EV")
                - focus_mode: Focus mode          (e.g., "AF-S", "AF-C", "MF")
                - af_mode: af area mode           (e.g., "SINGLE", "ZONE", "WIDETRACKING")
                - af_area_size: AF area size      (e.g., "Small", "Medium", "Large")
        Returns:
            - success: Operation success flag
            - error_message: Error details if failed
            - settings: Updated shooting parameters after applying the changes
            - options: Updated available options for each setting based on new camera state

        Example:
            >>> camera = fujixcam.Camera()
            >>> camera.setup(program_mode="P", iso_sensitivity="ISO 400")
            >>> camera.setup(program_mode="M", aperture="F2.8", shutter_speed="1/125")
        """
        # check if the provided keys include any invalid setup keys
        unknown_keys = list(key for key in kwargs.keys() if key not in self.SetupKeys.__dict__.values())
        if len(unknown_keys)>0:
            logger.error(f"Unknown camera setup keys provided: {unknown_keys}")
            return ResultConfig(success=False, error_message="Unknown camera setup keys provided")

        if not self.is_connected():
            return ResultConfig(success=False, error_message="Camera is not connected")

        with self._lock:  # ensure thread safety
            logger.info(f"Configuring camera settings: {kwargs}")
            success = 0
            failed = 0
            error_message = ""
            # 
            # Exposure settings are handled first because they can affect the available options for other settings.
            #
            #self.SetupKeys.PROGRAM_MODE
            if "program_mode" in kwargs:
                program_mode_new = kwargs["program_mode"]
                program_mode_old = self._settings.exposure.program_mode
                # validate program mode value
                if program_mode_new in self._options.exposure.program_mode:
                    if program_mode_new != program_mode_old:
                        # try to update program mode
                        if self._handle.set_program_mode( string_to_program_mode_value(program_mode_new) ).success:
                            # update context and cache
                            self._settings.exposure.program_mode = program_mode_new
                            success += 1
                            logger.info(f"Set program mode to {program_mode_new} from {program_mode_old}")
                            self._query_exposure_settings_by_program_mode()
                            self._query_exposure_options_by_program_mode()
                        else:
                            failed += 1
                            logger.error(f"Failed to set program mode to {program_mode_new} from {program_mode_old} )")
                    else:
                        success += 1
                        logger.info(f"Remaining in program mode: {program_mode_new}.")
                else:
                    failed += 1
                    logger.error(f"Invalid program mode: {program_mode_new}, current mode:{program_mode_old} )")
            #
            # APERTURE setting is available in Manual mode and Aperture Priority mode
            #
            if self._settings.exposure.program_mode in ["M", "A"]:
                self._fetch_aperture_settings_and_options()
                if "aperture" in kwargs:
                    aperture_string = kwargs["aperture"]
                    aperture_value = self._convert_to_sdk_value("aperture", aperture_string)   # invalid string will be converted to default value
                    if aperture_value is None:
                        failed += 1
                        logger.error(f"Invalid aperture value: {aperture_string} (not found in options)")
                    elif self._handle.set_aperture_value( aperture_value ).success:
                        self._settings.exposure.aperture = aperture_string    # update cache
                        success += 1
                        logger.info(f"Set aperture to {aperture_string} (SDK value: {aperture_value})")
                    else:
                        failed += 1
                        logger.error(f"Failed to set aperture to {aperture_string} (SDK value: {aperture_value})")
            elif "aperture" in kwargs:
                failed += 1
                logger.warning(f"Aperture setting is not available in program mode: {self._settings.exposure.program_mode}")
            #
            # SHUTTER_SPEED setting is available in Manual mode or Shutter Priority mode
            #
            if self._settings.exposure.program_mode in ["M", "S"]:
                if "shutter_speed" in kwargs:
                    shutter_speed_string = kwargs["shutter_speed"]
                    shutter_speed_value = self._convert_to_sdk_value("shutter_speed", shutter_speed_string)  # get SDK value from options dict using helper function
                    if shutter_speed_value is None:
                        failed += 1
                        logger.error(f"Invalid shutter speed: {shutter_speed_string} (not found in options)") 
                    elif self._handle.set_shutter_speed( shutter_speed_value ).success:
                        self._settings.exposure.shutter_speed = shutter_speed_string  # cache the string value
                        success += 1
                        logger.info(f"Set shutter speed to {shutter_speed_string} (SDK value: {shutter_speed_value})")
                    else:
                        failed += 1
                        logger.error(f"Failed to set shutter speed to {shutter_speed_string} (SDK value: {shutter_speed_value})")
            elif "shutter_speed" in kwargs:
                failed += 1
                logger.warning(f"Shutter speed setting is not available in program mode: {self._settings.exposure.program_mode}")
            #
            # EXPOSURE COMPENSATION setting is available in all program modes
            #
            if self._settings.exposure.program_mode in ["P", "A", "S"]:
                if "exposure_compensation" in kwargs:
                    ev_string = kwargs["exposure_compensation"]
                    ev_value = string_to_exposure_compensation_value(ev_string ) # invalid string will be converted to default value
                    if self._handle.set_exposure_compensation( ev_value ).success:
                        self._settings.exposure.exposure_compensation = ev_string  # cache the string value
                        success += 1
                        logger.info(f"Set exposure compensation to {ev_string} (SDK value: {ev_value})")
                    else:
                        failed += 1
                        logger.error(f"Failed to set exposure compensation to {ev_string} (SDK value: {ev_value})")
            elif "exposure_compensation" in kwargs:
                failed += 1
                logger.warning(f"Exposure compensation setting is not available in program mode: {self._settings.exposure.program_mode}")
            #
            # ISO_SENSITIVITY setting is available in all program modes
            #
            if "iso_sensitivity" in kwargs:
                iso_string = kwargs["iso_sensitivity"]
                iso_value = string_to_iso_sensitivity_value(iso_string ) # invalid string will be converted to default value
                if self._handle.set_iso_sensitivity( iso_value ).success:
                    self._settings.exposure.iso_sensitivity = iso_string  # cache the string value
                    success += 1
                    logger.info(f"Set ISO sensitivity to {iso_string} (SDK value: {iso_value})")
                else:
                    failed += 1
                    logger.error(f"Failed to set ISO sensitivity to {iso_string} (SDK value: {iso_value})")
            #
            # Focus settings (focus_mode, mf_distance, af_mode, af_area_size)
            #
            #self.SetupKeys.FOCUS_MODE
            if "focus_mode" in kwargs:
                focus_mode_new = kwargs["focus_mode"]
                focus_mode_old = self._settings.focus.focus_mode
                if focus_mode_new in self._options.focus.focus_mode:
                    if focus_mode_new != focus_mode_old:
                        # try to update focus mode
                        if self._handle.set_focus_mode( string_to_focus_mode_value(focus_mode_new) ).success:
                            # update context and cache
                            self._settings.focus.focus_mode = focus_mode_new
                            success += 1
                            logger.info(f"Set focus mode to {focus_mode_new} from {focus_mode_old}")
                            self._query_focus_settings_by_focus_mode()
                            self._query_focus_options_by_focus_mode()
                        else:
                            failed += 1
                            logger.error(f"Failed to set focus mode to {focus_mode_new} from {focus_mode_old} )")
                    else:
                        success += 1
                        logger.debug(f"Focus mode is already set to {focus_mode_new}.")
                else:    
                    failed += 1
                    logger.error(f"Invalid focus mode: {focus_mode_new}, current mode:{focus_mode_old} )")

            if self._settings.focus.focus_mode in ["MF"]:
                if "mf_distance" in kwargs:
                    mf_distance_new = int(kwargs["mf_distance"])
                    mf_distance_min = min(self._options.focus.mf_distance[0], self._options.focus.mf_distance[1])
                    mf_distance_max = max(self._options.focus.mf_distance[0], self._options.focus.mf_distance[1])
                    if mf_distance_new < mf_distance_min or mf_distance_new > mf_distance_max:
                        failed += 1
                        logger.error(f"Invalid manual focus distance: {mf_distance_new} (must be between inf:{mf_distance_min} and mod:{mf_distance_max})")
                    if self._handle.set_focus_distance( mf_distance_new ).success:
                        self._settings.focus.mf_distance = mf_distance_new
                        success += 1
                        logger.info(f"Set manual focus distance to {mf_distance_new}")
                    else:
                        failed += 1
                        logger.error(f"Failed to set manual focus distance to {mf_distance_new}")    
            elif "mf_distance" in kwargs:
                failed += 1
                logger.warning(f"Manual focus distance setting is not available in focus mode: {self._settings.focus.focus_mode}")

            if self._settings.focus.focus_mode in ["AF-S", "AF-C"]:
                if "af_mode" in kwargs:
                    afmode_string = kwargs["af_mode"]
                    afmode_value = string_to_focus_afmode_value(afmode_string)
                    if self._handle.set_focus_afmode(afmode_value).success:
                        self._settings.focus.af_mode = afmode_string
                        success += 1
                        logger.info(f"Set AF mode to {afmode_string}")
                        self._query_focus_settings_by_af_mode()
                        self._query_focus_options_by_af_mode()
                    else:
                        failed += 1
                        logger.error(f"Failed to set AF mode to {afmode_string}")
            elif "af_mode" in kwargs:
                failed += 1
                logger.warning(f"AF mode setting is not available in focus mode: {self._settings.focus.focus_mode}")

            if self._settings.focus.af_mode in ['SINGLE', 'ZONE']: 
               if "af_area_size" in kwargs: 
                   afsize_string = kwargs["af_area_size"]
                   afsize_value = string_to_focus_size_value(afsize_string)
                   if self._handle.set_focus_area(size=afsize_value).success:
                       self._settings.focus.af_area_size = afsize_string
                       success += 1
                       logger.info(f"Set AF area size to {afsize_string}")
                       # Refresh focus options after changing AF area size
                       # ...
                   else:
                       failed += 1
                       logger.error(f"Failed to set AF area size to {afsize_string}")
            elif "af_area_size" in kwargs:
                failed += 1
                logger.warning(f"AF area size setting is not available in AF mode: {self._settings.focus.af_mode}")

            if failed>0:
                error_message = f"Failed to apply some settings. Check logs for details. success({success}), failed({failed})"
            #result = success>0 or failed==0
            result = (failed==0)
            return self._build_config(success=result, error_message=error_message)

    def _build_config(self, success=True, error_message="") -> ResultConfig:
        # build return data from cached settings and options
        self._debug_print_settings(self._settings)
        self._debug_print_options(self._options)

        override_exposure_settings = {}
        override_exposure_options = {}
        if self._settings.exposure.program_mode not in ["M", "A"]:
            override_exposure_settings["aperture"] = None  # AUTOMATICALLY CONTROLLED BY CAMERA
            override_exposure_options["aperture"] = []      # AUTOMATICALLY CONTROLLED BY CAMERA
        if self._settings.exposure.program_mode not in ["M", "S"]:
            override_exposure_settings["shutter_speed"] = None  # AUTOMATICALLY CONTROLLED BY CAMERA
            override_exposure_options["shutter_speed"] = [] # AUTOMATICALLY CONTROLLED BY CAMERA
        if self._settings.exposure.program_mode == "M":
            override_exposure_settings["exposure_compensation"] = None  # not applicable in manual mode
            override_exposure_options["exposure_compensation"] = [] # not applicable in manual mode

        override_focus_settings = {}
        override_focus_options = {}
        if self._settings.focus.focus_mode in ["AF-S", "AF-C"]:
            override_focus_settings["mf_distance"] = None  # not applicable in AF modes
            override_focus_options["mf_distance"] = (0, 0, 0)  # not applicable in AF modes
        if self._settings.focus.focus_mode == "MF":
            override_focus_settings["af_mode"] = "SINGLE"  # fixed to single in manual focus mode
            override_focus_options["af_mode"] = []  # not applicable in MF mode
        elif self._settings.focus.af_mode == "WIDETRACKING":
            override_focus_settings["af_area_size"] = None  # not applicable in wide tracking mode  
            override_focus_options["af_area_size"] = []  # not applicable in wide tracking mode  

        settings = { "exposure": ExposureSettings(**asdict(self._settings.exposure) | override_exposure_settings),
                        "focus": FocusSettings(**asdict(self._settings.focus)| override_focus_settings),
                        "image": ImageSettings(**asdict(self._settings.image)),}
        options = { "exposure": ExposureOptions(**asdict(self._options.exposure) | override_exposure_options),
                    "focus": FocusOptions(**asdict(self._options.focus) | override_focus_options),
                    "image": ImageOptions(**asdict(self._options.image)),}

        return ResultConfig(success=success, error_message=error_message, settings=settings, options=options)


    def capture(self, **kwargs) -> ResultFiles:
        """Capture image(s) and transfer to pc storage.

        Filename will be determined automatically from date/time
        When capturing multiple images and focus mode AF-S, autofocus will be performed before the first capture, and then autofocus will be locked for subsequent captures.

        Args:
            folder: Optional folder path to save the captured image(s). If not provided, current folder will be used.
            count: Optional number of images to capture (default is 1). If more than 1, multiple images will be captured in sequence.
            
        Returns:
            Result containing:
            - success: Operation success flag
            - error_message: Error details if failed
            - folder: Folder path where the captured image is saved
            - image_files: List of captured image files (if RAW+JPEG pair is captured, both files will be included)
            - total_bytes: Size of the captured image file in bytes (sum of all files if multiple files are captured)
            - last_image_file: the last file in the image_files list

        Example:
            >>> result = camera.capture()
            >>> result = camera.capture( folder = "/mypath/to/save", filename = "myfile" )
            >>> result = camera.capture( count = 3 )
            >>> print(result.image_files)  # the list of captured image files
        """
        if not self.is_connected():
            return ResultFiles(success=False, error_message="Camera is not connected")

        with self._lock:  # ensure thread safety
            folder = kwargs.get("folder", None)
            count  = int( kwargs.get("count", "1") )

            if count < 1 or count > self._camera_status.buffer_count:
                error_message = f"Invalid capture count: {count}. Must be between 1 and {self._camera_status.buffer_count}."
                logger.error(error_message)
                return ResultFiles(success=False, error_message=error_message)

            if count == 1:
            # Single capture mode
                res = self._handle.capture_image( folder=folder, filename=kwargs.get("filename", None) )
                if not res.success:
                    error_message = f"Failed to capture image: {res.error_message}"
                    logger.error(error_message)
                    return ResultFiles(success=False, error_message=error_message)
                #res.data = {"folder": target_folder, "filename": object_name, "datasize": sum(output_sizes), "object": output_files }
                all_files = res.data["object"]      # [ "file1.raf", "file1.jpg" ] or [ "file1.raf" ] or [ "file1.jpg" ]
                logger.info(f"Captured image file: {all_files}")
                return ResultFiles(success=True, error_message=None,
                                   folder=res.data["folder"], last_image_file=all_files[-1], total_bytes=res.data["datasize"], image_files=all_files )

            # Multiple capture mode
            af_lock = self._settings.focus.focus_mode=="AF-S" and not "af_locked" in self._camera_status.conditions
            # autofocus will be performed and locked for multiple capture in AF-S mode
            if af_lock:
                af_result = self._handle.perform_af()
                if not af_result.success:
                    error_message = f"Failed to perform autofocus before multiple capture: {af_result.error_message}"
                    logger.error(error_message)
                    return ResultFiles(success=False, error_message=error_message )
                self._handle.af_lock(True)   # lock autofocus for multiple capture

            res = self._handle.capture_multi_images( folder=folder, count=count )
            if af_lock:
                self._handle.af_lock(False)  # unlock autofocus if it was locked
            if not res.success:
                error_message = f"Failed to capture multiple images: {res.error_message}"
                logger.error(error_message)
                return ResultFiles(success=False, error_message=error_message)

            logger.info(f"Captured image successfully. {res.data}")
            #res.data = "objects": [ {...}, {...}, ... ]  # list of captured image files with folder, filename, datasize, object
            all_files = [y for r in res.data["objects"] for y in r["object"] ]  # flatten the list of lists
            return ResultFiles(success=True, error_message=None,
                               folder=res.data["objects"][0]["folder"], last_image_file=all_files[-1], total_bytes=res.data["datasize"], image_files=all_files )
            #jpg_files = [f for f in image_files if f.lower().endswith(".jpg")]
            #raw_files = [f for f in image_files if f.lower().endswith(".raf")]
            #is_raw_jpg_pair = len(jpg_files) > 0 and len(raw_files) > 0 and len(jpg_files) == len(raw_files)

    def preview(self) -> ResultImage:
        """Capture a small image for previewing the current camera settings without saving to file.
          (return a low-resolution image for test shot, approximately 1M pixels)
        Note:
            This method does not save the captured image to a file. It only returns the image data in memory.

        Returns:
            CaptureResult containing:
            - image_data: bytearray containing the JPEG data of the preview image
            - image_note: Additional information about the captured preview image (if available)
        """
        if not self.is_connected():
            return ResultImage(success=False, error_message="Camera is not connected")
            
        with self._lock:  # ensure thread safety
            result = self._handle.capture_preview()  
            if not result.success:
                error_message = f"Failed to capture preview image: {result.error_message}"
                logger.error(error_message)
                return ResultImage(success=False, error_message=error_message)

            logger.info("Captured test image for preview successfully. Refer to the returned buffer.")
            # af_success = ...
            return ResultImage(success=True, error_message=None,
                                   image_note={ "af_success": True },
                                   image_data=result.data["buffer"] )


    def bulb_capture(self, folder=None, exposure_time:int = 10, callback: Optional[Callable[[float, float], str]] = None, aperture=None, iso_sensitivity=None) -> ResultFiles:
        """Perform bulb capture for the specified duration in seconds.

        Args:
            folder: Optional folder path to save the captured image. If not provided, current folder will be used.
            exposure_time: Duration of the bulb capture in seconds (integer).
            callback: Optional callback function to receive progress updates during the bulb capture.
            The callback function should return one of the following values:
                - "continue": Continue the bulb capture operation until the specified duration is reached.
                - "finish": Finish early the bulb capture operation and save the captured image.
                - "cancel": Cancel the bulb capture operation. 
            aperture: Optional aperture value for the bulb capture. If not provided, the camera will use the highest-1 available aperture value.
            iso_sensitivity: Optional ISO sensitivity value for the bulb capture. If not provided, the camera will use the lowest available ISO value.

        Returns:
            Result containing:
            - success: Operation success flag
            - error_message: Error details if failed
            - folder: Folder path where the captured image is saved
            - image_files: List of captured image files (if RAW+JPEG pair is captured, both files will be included)
            - total_bytes: Size of the captured image file in bytes (sum of all files if multiple files are captured)
            - last_image_file: The last file in the image_files list
        """
        if not self.is_connected():
            return ResultFiles(success=False, error_message="Camera is not connected" )

        with self._lock:  # ensure thread safety
            duration = float(exposure_time)
            if duration <= 1.0:
                error_message = f"Invalid duration for bulb capture: {duration}. Duration must be greater than 1.0 seconds."
                logger.error(error_message)
                return ResultFiles(success=False, error_message=error_message)

            # setup bulb capture settings (program mode and shutter speed) before bulb_on()
            backup_ae = self._handle.get_program_mode().value
            self._handle.set_program_mode( string_to_program_mode_value("M") )  # set to manual mode for bulb capture
            backup_ss = self._handle.get_shutter_speed().value
            self._handle.set_shutter_speed( string_to_shutter_speed_value("BULB") )  # set shutter speed to BULB mode
            backup_av = self._handle.get_aperture_value().value
            self._handle.set_aperture_value( self._convert_to_sdk_value("aperture", aperture) \
                if aperture is not None else self._handle.get_aperture_value_options().options[-2] ) # get the highest-1 available aperture value for bulb capture
            backup_iso = self._handle.get_iso_sensitivity().value
            self._handle.set_iso_sensitivity( string_to_iso_sensitivity_value(iso_sensitivity) \
                if iso_sensitivity is not None else self._handle.get_iso_sensitivity_options().options[0] )  # get the lowest available ISO value for bulb capture
            backup_fm = self._handle.get_focus_mode().value
            self._handle.set_focus_mode( string_to_focus_mode_value("MF") )  # set focus mode to manual focus for bulb capture
            inf = self._handle.get_focus_distance_range().data.get("inf", None)  # get the focus distance range to check if infinity is supported
            backup_fd = self._handle.get_focus_distance().value
            if inf is not None:
                self._handle.set_focus_distance(inf)  # set focus distance to infinity for bulb capture

            def restore_settings():
                self._handle.set_focus_distance( backup_fd )  # restore original focus distance
                self._handle.set_focus_mode( backup_fm )  # restore original focus mode
                self._handle.set_iso_sensitivity( backup_iso )  # restore original ISO sensitivity
                self._handle.set_aperture_value( backup_av )  # restore original aperture value
                self._handle.set_shutter_speed( backup_ss )  # restore original shutter speed
                self._handle.set_program_mode( backup_ae )  # restore original program mode

            res = self._handle.bulb_on()
            if not res.success:
                error_message = f"Failed to perform bulb capture: {res.error_message}"
                logger.error(error_message)
                self._handle.reset_status()  # reset camera status to avoid being stuck in bulb mode
                restore_settings()
                return ResultFiles(success=False, error_message=error_message)

            def default_callback(elapsed_time:float, total_duration:float):
                logger.info(f"Bulb capture progress: {elapsed_time:.2f}/{total_duration:.2f} seconds")
                cont = input("Press Enter to continue, 'c' to cancel, or 'f' to finish early : ").strip().lower()
                if cont == "c":
                    return "cancel"  # Cancel the bulb capture operation
                elif cont == "f":
                    return "finish"  # Complete the bulb capture operation early
                return "continue"  # Continue the bulb capture operation

            if callback is not None and not callable(callback):
                callback = default_callback

            # Start a timer to track the duration of the bulb capture
            start_time = time.time()
            elapsed_time = 0.0
            while True:
                elapsed_time = time.time() - start_time

                if elapsed_time >= duration:
                    break

                if callback is not None:
                    callback_result = callback(elapsed_time, float(duration))
                    if callback_result == "finish":
                        break
                    elif callback_result == "cancel":
                        self._handle.bulb_off( abort=True )  # Abort the bulb capture operation
                        message = f"Bulb capture canceled by user ({elapsed_time:.2f}/{duration:.2f} seconds)"
                        logger.info(message)
                        restore_settings()
                        return ResultFiles(success=True, error_message=message)
                time.sleep(0.5)  # Sleep briefly to avoid busy waiting

            res = self._handle.bulb_off( folder=folder )
            restore_settings()

            if not res.success:
                error_message = f"Failed to complete bulb capture ({elapsed_time:.2f}/{duration:.2f} seconds): {res.error_message}"
                logger.error(error_message)
                return ResultFiles(success=False, error_message=error_message)

            logger.info(f"Bulb capture completed successfully ({elapsed_time:.2f}/{duration:.2f} seconds)")
            all_files = res.data["object"]      # [ "file1.raf", "file1.jpg" ] or [ "file1.raf" ] or [ "file1.jpg" ]
            logger.info(f"Captured image file: {all_files}")
            return ResultFiles(success=True, error_message=None,
                               folder=res.data["folder"], last_image_file=all_files[-1], total_bytes=res.data["datasize"], image_files=all_files )

    def focus_on(self, h:int, v: int, af_on: bool =False, hold_on: bool =False) -> ResultStatus:
        """Move focus area to specified horizontal and vertical position and perform autofocus if supported.
            Refer to options["foucs"]:FocusOptions for the valid range of h, v.
            options are provided in the result of get_config().

        Args:
            h: Horizontal position (center of screen is 0, left is negative, right is positive)
            v: Vertical position (center of screen is 0, down is negative, up is positive)

        Returns: Result containing:
            success: False if setting focus area or performing autofocus failed.
            error_message: Error details if failed
            camera_status: Current camera status after the operation (ready, focusing, af_locked, etc.) if successful else None
        """
        if not self.is_connected():
            return ResultStatus(success=False, error_message="Camera is not connected")

        with self._lock:  # ensure thread safety
            # current focus area
            focus_area_h = self._settings.focus.af_point[0] if h is None else h
            focus_area_v = self._settings.focus.af_point[1] if v is None else v
            focus_area_size = self._settings.focus.af_area_size     # allways keep the current value
            result = self._handle.set_focus_area( focus_area_h, focus_area_v, string_to_focus_size_value(focus_area_size) )

            # Failure to set focus area (invalid parameters or other reasons )
            if not result.success:
                error_message = f"Failed to set focus area to h:{focus_area_h}, v:{focus_area_v}, size:{focus_area_size}: {result.error_message}" 
                logger.error(error_message)
                return ResultStatus(success=False, error_message=error_message)
            
            # update cache with the new focus area settings
            self._settings.focus.af_point = (focus_area_h, focus_area_v)

            if af_on and not "focusing" in self._camera_status.conditions:
                # perform autofocus like as pressing the shutter halfway, and check if it is successful
                res_af = self._handle.perform_af(True)
                if not res_af.success:
                    error_message = f"Failed to perform autofocus at h:{focus_area_h}, v:{focus_area_v}, size:{focus_area_size}"
                    logger.error(error_message)
                    return ResultStatus(success=False, error_message=error_message)

                if hold_on:
                    # hold the shutter halfway to lock focus if requested
                    # - in AF-S mode, the camera will hold focus until the shutter is fully pressed or focus_off() is called.
                    # - in AF-C mode, the camera will continue to adjust focus until the shutter is fully pressed or focus_off() is called.
                    if self._settings.focus.focus_mode == "AF-S":
                        self._handle.af_lock(True)  # lock focus in AF-S mode

            # Successfully set focus area and perform autofocus, return the current focus settings and options
            return self.get_status()

    def focus_off(self) -> ResultStatus:
        """Turn off autofocus and set focus mode to manual.

        Returns:
            ResultConfig containing:
            - success: Operation success flag
            - error_message: Error details if failed
            - settings: Current focus settings after turning off autofocus if successful, else None
            - options: Current focus options after turning off autofocus if successful, else None
        """
        if not self.is_connected():
            return ResultStatus(success=False, error_message="Camera is not connected")

        with self._lock:
            if "focusing" in self._camera_status.conditions:
                self._handle.perform_af(False)  # cancel autofocus if it is currently focusing
            if "af_locked" in self._camera_status.conditions:
                self._handle.af_lock(False)  # unlock autofocus if it was locked
 
            return self.get_status()

#    def get_monitor_options(self) -> ResultConfig:
#        with self._lock:
#            return ResultConfig(success=True, error_message=None,
#                                settings=None,
#                                options={"monitor": MonitorOptions(**self._monitor_options)} )

    def get_monitor_image(self, point:Optional[tuple[int, int]]=None, size:Optional[str]=None, zoom:str="x1.0", perform_af:bool =False) -> ResultImage:
        """ Get live view image data for the specified area and zoom level without starting live view mode.
            (under development, undocumented in GUIDE_Camera.md, operation may not be stable)
        Args:
            point: position h, v (center of screen is 0, negative is left/down, positive is right/up)
            size: Live view image size string (default is the first available live view size)
            zoom: Zoom level string (default is "x1.0", same as available live view zoom )
            perform_af: Whether to perform autofocus before capturing the live view image. If True, the camera will attempt to focus on the specified area before capturing the image. The autofocus result will be included in the return data if performed.

        Returns:
            ResultImage containing:
            - success: Operation success flag
            - error_message: Error details if failed
            - image_data: bytearray containing the JPEG data of the captured image if successful, else None
            - image_note: Additional information about the captured image (if successful, else None)
        """
        if not self.is_connected():
            return ResultImage(success=False, error_message="Camera is not connected")

        with self._lock:
            # temporarily change focus mode to manual to enable focus area and zoom control, and restore it later.
            if self._settings.focus.focus_mode != "MF":
                response = self._handle.set_focus_mode( string_to_focus_mode_value( "MF" ) ) 
                if not response.success:
                    error_message = f"Failed to set focus mode to manual : {response.error_message}"
                    logger.error(error_message)
                    return ResultImage(success=False, error_message=error_message)

            if point is not None:
                h, v = point
                response =self._handle.set_focus_area( h, v )
                if not response.success:
                    error_message = f"Failed to set focus area : {response.error_message}"
                    logger.error(error_message)
                    self._handle.set_focus_mode( string_to_focus_mode_value( self._settings.focus.focus_mode ) )
                    return ResultImage(success=False, error_message=error_message)

            af_result= self._handle.perform_af() if perform_af else None

            error_message = None
            if size is None or not size in ["L", "M", "S"]: # self._options.liveview.liveview_size:
                    size = "L"  # default to large if size is not specified or invalid
            self._handle.set_liveview_size( string_to_liveview_size_value( size ) )
            self._handle.set_finder_crop( string_to_finder_crop_value( zoom ) )

            # capture live view image for the specified area and zoom level, we just want a single image.
            response = self._handle.start_liveview()
            if response.success:
                response = self._handle.get_liveview_image()
                if not response.success or response.data["buffer"] is None:
                    error_message = f"Failed to get live view image : {response.error_message}"
                    logger.error(error_message)
                self._handle.stop_liveview() 
            else:
                error_message = f"Failed to start live view: {response.error_message}"
                logger.error(error_message)
                self._handle.reset_status()

            # restore previous settings
            self._handle.set_finder_crop( string_to_finder_crop_value( "x1.0" ) ) 
            if point is not None:
                self._handle.set_focus_area( self._settings.focus.af_point[0], self._settings.focus.af_point[1] )
            if self._settings.focus.focus_mode != "MF":
                self._handle.set_focus_mode( string_to_focus_mode_value( self._settings.focus.focus_mode ) )

            if error_message is not None:
                error_message = f"Failed to get monitor image : {error_message}"
                logger.error(error_message)
                return ResultImage(success=False, error_message=error_message)
            
            logger.info(f"get monitor image zoom={zoom}")
            return ResultImage(success=True, image_data=response.data["buffer"] )   # type: ignore

    def get_liveview_config(self) -> ResultConfig:
        """ Get the live view settings and available options.
            Options include available resolutions, quality settings, and zoom levels for start_liveview.

        Returns:
            ResultConfig containing:
            - success: Operation success flag
            - error_message: Error details if failed
            - settings: Current live view settings
            - options: Available live view options
        """
        if not self.is_connected():
            return ResultConfig(success=False, error_message="Camera is not connected")

        with self._lock:
            return ResultConfig(success=True, error_message=None,
                                settings={"liveview": LiveviewSettings(**asdict(self._settings.liveview))},
                                options={"liveview": LiveviewOptions(**asdict(self._options.liveview))} )

    def start_liveview(self, size:str = "L", quality:str="FINE", zoom:str = "x1.0") -> ResultStatus:
        """Start live view mode.
            if live view is successfully started, camera_status.conditions includes "liveviewing": Live view mode is active.

        Returns:
            ResultStatus containing:
            - success: Operation success flag
            - error_message: Error details if failed
            - camera_status: Updated camera status after starting live view mode.
        """
        if not self.is_connected():
            return ResultStatus(success=False, error_message="Camera is not connected")

        with self._lock:
            # check if live view is already active
            if "liveview" in self._camera_status.conditions:            # using the cached value from the last status update
                logger.warning("Live view mode is already active.")
                return ResultStatus(success=True, error_message=None, camera_status=self.get_status().camera_status)

            # check if the camera is in a mode that supports stable live view (this requirement is tentative and may change based on future firmware updates)
            if not (self._settings.focus.focus_mode == "MF" or self._settings.focus.af_mode == "SINGLE"):
            #    return ResultStatus(success=False, error_message="Live view is only available in MF or SINGLE AF mode", camera_status=CameraStatus(**asdict(self._camera_status)))
                logger.warning("Live view may not be stable in the current focus mode. 'MF' or 'SINGLE' AF mode is recommended.")

            if size not in self._options.liveview.liveview_size:
                return ResultStatus(success=False, error_message=f"Invalid live view size: {size}", camera_status=CameraStatus(**asdict(self._camera_status)))
            if quality not in self._options.liveview.liveview_quality:
                return ResultStatus(success=False, error_message=f"Invalid live view quality: {quality}", camera_status=CameraStatus(**asdict(self._camera_status)))
            if zoom not in self._options.liveview.liveview_zoom:
                return ResultStatus(success=False, error_message=f"Invalid live view zoom: {zoom}", camera_status=CameraStatus(**asdict(self._camera_status)))

            logger.info("Starting live view mode.")

            # set live view image size and zoom level (crop ratio)
            res = self._handle.set_liveview_quality( string_to_liveview_quality_value( quality ) )  # X-S10 does not support quality options
            res = self._handle.set_liveview_size( string_to_liveview_size_value( size ) ) 
            res = self._handle.set_finder_crop( string_to_finder_crop_value( zoom ) )
            res = self._handle.start_liveview()  
            if not res.success:
                logger.error(f"Failed to start live view: {res.error_message}")
                self._handle.reset_status()
                return ResultStatus(success=False, error_message=res.error_message, camera_status=CameraStatus(**asdict(self._camera_status)))  

            return ResultStatus(success=res.success,
                                error_message=None if res.success else res.error_message,
                                camera_status=self.get_status().camera_status )

    def stop_liveview(self) -> ResultStatus:
        """Stop live view mode.
            if live view is successfully stopped, camera_status.conditions no longer includes "liveviewing".

        Returns:
            StatusResult containing:
            - success: Operation success flag
            - error_message: Error details if failed
            - camera_status: Updated camera status after stopping live view mode.
        """
        if not self.is_connected():
            return ResultStatus(success=False, error_message="Camera is not connected")

        with self._lock:
            # check if live view is already inactive
            #if self._handle.get_status().data.get("liveview", False):  # query directly from the camera status, instead of using the cached value
            if not "liveviewing" in self._camera_status.conditions:        # using the cached value from the last status update
                logger.warning("Live view not started yet.")
                return ResultStatus(success=True, error_message=None, camera_status=self.get_status().camera_status)

            logger.info("Stopping live view mode.")

            res = self._handle.stop_liveview()  

            # restore previous settings
            self._handle.reset_status()  # reset the camera status after stopping live view
            return ResultStatus(success=res.success,
                                error_message=None if res.success else res.error_message,
                                camera_status=self.get_status().camera_status )

    def get_liveview_image(self) -> ResultImage:
        """Get the latest live view image from the camera.
            start_liveview() must be called successfully before calling this method.
            stop_liveview() must be called after finishing live view to properly release resources.

        Returns:
            CaptureResult containing:
            - success: Operation success flag
            - error_message: Error details if failed
            - image_data: bytearray containing the JPEG data of the captured live view image if successful, else None.
            - image_note: Additional information about the captured live view image, usually None for live view images.
        """
        if not self.is_connected():
            return ResultImage(success=False, error_message="Camera is not connected")

        with self._lock:
            if not "liveviewing" in self._camera_status.conditions:        # using the cached value from the last status update
                error_message = "Live view not started yet."
                logger.error(error_message)
                return ResultImage(success=False, error_message=error_message, image_data=None)

            res = self._handle.get_liveview_image()  
            if not res.success:
                error_message = f"Failed to get live view image: {res.error_message}"
                logger.error(error_message)
                return ResultImage(success=False, error_message=error_message, image_data=None)

            # logger.info("Getting live view image.")
            return ResultImage(success=True, error_message=None, image_data=res.data["buffer"] )    # buffer is a bytes object containing the jpeg image data

    def close(self, forced=False, shutdown=False) -> None:
        """Explicitly and safely close camera connection.

        This method can be called manually to release camera resources.
        It's also called automatically on object deletion in context managers.

        Example:
            >>> camera = fujixcam.Camera()
            >>> # ... use camera ...
            >>> camera.close()
        """
        self._disconnect( forced=forced, shutdown=shutdown )

    def __enter__(self):
        """Context manager entry.
        Example:
            >>> with fujixcam.Camera() as camera:
            ...     result = camera.capture()
        """
        logger.debug("Entering camera context manager.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures camera disconnection."""
        logger.debug("Exiting camera context manager.")
        self.close()
        return False

    def __del__(self):
        """Destructor - ensures camera disconnection on object deletion."""
        self.close( forced=True )

    def __repr__(self) -> str:
        """String representation of Camera object."""
        if hasattr(self, "_handle") and self._handle is not None:
            status = "connected" if self.is_connected() else "disconnected"
        else:
            status = "unknown"
        return f"<Camera(device={self.product_name}, status={status})>"

# end of camera.py