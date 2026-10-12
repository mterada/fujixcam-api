"""Result dataclasses for fujixcam camera operations."""
# -----------------------------------------------------
# results.py :
#   Camera operation return result dataclasses
#
# Copyright 2026 Masahiro Terada (@mterada.com)
# This software is released under the MIT License.
# http://opensource.org/licenses/mit-license.php
# -----------------------------------------------------

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Tuple, Any

@dataclass
class ResultBase:
    """Base class for operation results.

    Contains common fields for all result types, such as success flag and error message.
    """
    success: bool = False
    error_message: Optional[str] = None

    @property
    def failed(self) -> bool:
        """Indicates whether the operation failed."""
        return not self.success

@dataclass
class CameraStatus:
    """Camera status information.

    Represents the current operational status of the camera.
    Returned by get_status()
    """
    is_ready: bool = False
    buffer_count: int = 0
    conditions: list[str] = field(default_factory=list)  
    # e.g., ["disconnected", "shooting", "forcusing", "af_locked", "liveviewing" ...]

@dataclass
class ExposureSettings:
    """Current exposure settings

    Represents the current exposure settings configured on the camera.
    Returned by get_config(), setup(), and used as reference for parameters in setup().
    """
    program_mode: Optional[str] = None
    iso_sensitivity: Optional[str] = None
    aperture: Optional[str] = None
    shutter_speed: Optional[str] = None
    exposure_compensation: Optional[str] = None
#    metering_mode: Optional[str] = None

@dataclass
class ExposureOptions:
    """Available exposure options.

    Represents the selectable values for camera settings,
    which may vary depending on the camera model and current settings.
    Returned by get_config() and setup(), and used as reference for parameters in setup().
    """
    program_mode: List[str] = field(default_factory=list)
    iso_sensitivity: List[str] = field(default_factory=list)
    aperture: List[str] = field(default_factory=list)
    shutter_speed: List[str] = field(default_factory=list)
    exposure_compensation: List[str] = field(default_factory=list)
#    metering_mode: List[str] = field(default_factory=list)

@dataclass
class FocusSettings:
    """Current focus settings.

    Represents the current focus-related parameters configured on the camera.
    Returned by get_config(), setup(), and used as reference for parameters in focus_on().
    """
    focus_mode: Optional[str] = None    # "AF-S", "AF-C", "MF"
    mf_distance: Optional[int] = None   # rangge(min, max, step) for manual focus distance, if applicable
    af_mode: Optional[str] = None       # "SINGLE", "ZONE", "WIDETRACKING"
    af_area_size: Optional[str] = None  # "Small", "Medium", "Large"
    af_point: Tuple = (0,0)             # (h, v) coordinates of the AF point, if applicable

@dataclass
class FocusOptions:
    """Available focus options.

    Represents the selectable values for focus-related parameters,
    which may vary depending on the camera model and current settings.
    Returned by get_config(), setup(), and used as reference for parameters in focus_on().
    """
    focus_mode: List[str] = field(default_factory=list)
    mf_distance: Tuple[int,int,int] = field(default_factory=lambda: (0, 0, 0))  # (min, max, step) for manual focus distance
    af_mode: List[str] = field(default_factory=list)
    af_area_size: List[str] = field(default_factory=list)
    af_point_h: List[int] = field(default_factory=list)  # list of horizontal coordinates for AF points
    af_point_v: List[int] = field(default_factory=list)  # list of vertical coordinates for AF points

@dataclass
class ImageSettings:
    """Current image settings.

    Represents the current image-related parameters configured on the camera.
    Returned by get_config(), setup().
    """
    image_quality: Optional[str] = None
    image_size: Optional[str] = None

@dataclass
class ImageOptions:
    """Available image options.

    Represents the selectable values for image-related parameters.
    Returned by get_config(), setup().
    """
    image_quality: List[str] = field(default_factory=list)
    image_size: List[str] = field(default_factory=list)

@dataclass
class LiveviewSettings:
    """Current liveview settings.

    Represents the current liveview-related parameters configured on the camera.
    """
    liveview_quality: Optional[str] = None
    liveview_size: Optional[str] = None
    liveview_zoom: Optional[str] = None

@dataclass
class LiveviewOptions:
    """Available liveview options.
    
    Represents the selectable values for liveview-related parameters.
    Returned by get_liveview_options(), and used as reference for parameters in start_liveview().
    """
    liveview_quality: List[str] = field(default_factory=list)
    liveview_size: List[str] = field(default_factory=list)
    liveview_zoom: List[str] = field(default_factory=list)

#@dataclass
#class ColorSettings:
#    """Current color settings.
#    """"
#    white_balance: Optional[str] = None
#    color_profile: Optional[str] = None
#    color_xxx: Optional[str] = None

#@dataclass
#class LensSettings:
#   zoom_position: int = 0  # current zoom position of the lens
#   focal_length: str = ""  # current focal length of the lens
#@dataclass
#class LensOptions:
#   zoom_capability: int = 0
#   zoom_position: List[int] = field(default_factory=list)  # available zoom positions for the lens

#@dataclass
#class MonitorOptions:
#    """Available monitor options.
#    
#    Returned by get_monitor_options() and used as reference for parameters in get_monitor_image().
#    """
#    monitor_zoom: List[str] = field(default_factory=list)
#    monitor_h: List[int] = field(default_factory=list)
#    monitor_v: List[int] = field(default_factory=list)

# --------------------------------------
# Result dataclasses for each operation
# --------------------------------------
@dataclass
class ResultStatus(ResultBase):
    """Result of a status query operation.

    Attributes:
        success: Whether the status query succeeded.
        error_message: Error message if query failed.
        camera_status: Current status of the camera (e.g., is_ready, conditions).
    """
    camera_status: CameraStatus = field(default_factory=CameraStatus)

@dataclass
class ResultConfig(ResultBase):
    """Result of a status query operation.

    Attributes:
        success: Whether the status query succeeded.
        error_message: Error message if query failed.
        settings: Dict[str, Any] = { "exposure": ExposureSettings(...), "focus": FocusSettings(...), "image": ImageSettings(...), ... }
        options: Dict[str, Any] = { "exposure": ExposureOptions(...), "focus": FocusOptions(...), "image": ImageOptions(...), ... }
    """
    settings: Dict[str, Any] = field(default_factory=dict) 
    options: Dict[str, Any] = field(default_factory=dict)  

@dataclass
class ResultFiles(ResultBase):
    """Result of a image capture operation that returns image file objects.

    return by capture(), bulk_capture()
    Attributes:
        success: Whether the capture operation succeeded.
        error_message: Error message if capture failed.
        
    """
    folder: str = ""
    last_image_file: Optional[str] = None                           # name of the last captured image file (e.g., "filename0001.jpg")
    image_files: list[str] = field(default_factory=list)  # list of RAW and/or JPEG image files captured
    total_bytes: int = 0  # size of the captured image file in bytes (sum of all files if multiple files are captured)

@dataclass
class ResultImage(ResultBase):
    """Result of a image capture operation that returns image data.

        monitor image, preview image, or liveview image.

    Attributes:
        success: Whether the operation succeeded.
        error_message: Error message if retrieval failed.
        image_data: Image data in bytes format (e.g., JPEG).
    """
    image_data: Optional[bytes] = None
    image_note: Dict[str, Any] = field(default_factory=dict)
