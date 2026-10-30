"""fujixcam - FUJIFILM Camera Control Package.

A Python library for controlling FUJIFILM X-Series digital cameras connected via USB/Wifi
wraps the manufacturer's C/C++ SDK to provide a high-level Python API for camera operations.

Example:
    >>> import fujixcam
    >>> camera = fujixcam.Camera()
    >>> camera.setup(program_mode="P", iso_sensitivity="ISO 400", exposure_compensation="+1.0EV")
    >>> result = camera.capture()
    >>> print(result) 
"""

from fujixcam.camera_api import is_sdk_installed, install_sdk
from fujixcam.camera_api import CameraAPI
from fujixcam.camera_api_dictionary import sdk_value_to_string, string_to_sdk_value
#   program_mode_value_to_string, string_to_program_mode_value_, exposure_compensation_value_to_string, string_to_exposure_compensation_value, iso_sensitivity_value_to_string, string_to_iso_sensitivity_value, shutter_speed_value_to_string, string_to_shutter_speed_value, aperture_value_to_string, string_to_aperture_value
#   focus_mode_value_to_string, string_to_focus_mode_value, image_quality_value_to_string, string_to_image_quality_value, image_size_value_to_string, string_to_image_size_value, liveview_quality_value_to_string, string_to_liveview_quality_value, liveview_size_value_to_string, string_to_liveview_size_value
from fujixcam.camera import Camera
# from fujixcam.results import * 
from fujixcam.results import ResultBase, ResultStatus, ResultConfig, ResultFiles, ResultImage
from fujixcam.results import CameraStatus, ExposureSettings, ExposureOptions, FocusSettings, FocusOptions, ImageSettings, ImageOptions, LiveviewSettings, LiveviewOptions

try:
    from fujixcam._version import __version__
except ImportError:
    __version__ = "0.0.0.dev0"

__author__ = "Masahiro Terada"
__all__ = [
    "CameraAPI",
    "sdk_value_to_string",
    "string_to_sdk_value",
    "Camera",
    "ResultBase",
    "ResultStatus",
    "ResultConfig",
    "ResultFiles",
    "ResultImage",
    "CameraStatus",
    "ExposureSettings",
    "ExposureOptions",
    "FocusSettings",
    "FocusOptions",
    "ImageSettings",
    "ImageOptions",
    "LiveviewSettings",
    "LiveviewOptions",
]
