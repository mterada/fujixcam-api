# ---------------------------------------------------------------------
# camera_api_dictionary.py :
#   Camera API parameter mappings for Fuji cameras
#
# This module defines various mappings
#  between camera SDK's parameter codes and human-readable text strings.
# Note: Available options depend on the camera maker and models.
# 
# These mappings facilitate easier usage of camera settings
#  for not only human but also AI Assistant.
#
# Copyright 2026 Masahiro Terada (@mterada.com)
# This software is released under the MIT License.
# http://opensource.org/licenses/mit-license.php
# ---------------------------------------------------------------------
from typing import Dict, Callable

# Dictionary for Exposure Program Mode Values
PROGRAM_MODE_DICT: Dict[int, str] = {
    0x0001: "M",  # Manual Exposure mode
    0x0003: "A",  # Aperture Priority AE mode
    0x0004: "S",  # Shutter Priority AE mode
    0x0006: "P",  # Program AE mode
}
PROGRAM_MODE_DEFAULT = 0x0006  # Program AE
PROGRAM_MODE_INVALID = 0x0000  # Unknown program mode
PROGRAM_MODE_STR2INT: Dict[str, int] = {v: k for k, v in PROGRAM_MODE_DICT.items()}  # for reverse lookup
program_mode_value_to_string = lambda v: PROGRAM_MODE_DICT.get(v, "UNKNOWN")
string_to_program_mode_value = lambda s: PROGRAM_MODE_STR2INT.get(s, PROGRAM_MODE_INVALID)

# Dictionary for Focus Mode Values
FOCUS_MODE_DICT: Dict[int, str] = {
    0x0001: "MF",  # Manual Focus
    0x8001: "AF-S", # Auto Focus Single
    0x8002: "AF-C", # Auto Focus Continuous
}
FOCUS_MODE_DEFAULT = 0x8001  # AF-S
FOCUS_MODE_INVALID = 0x0000  # Unknown focus mode
FOCUS_MODE_STR2INT: Dict[str, int] = {v: k for k, v in FOCUS_MODE_DICT.items()}  # for reverse lookup
focus_mode_value_to_string = lambda v: FOCUS_MODE_DICT.get(v, "UNKNOWN")
string_to_focus_mode_value = lambda s: FOCUS_MODE_STR2INT.get(s, FOCUS_MODE_INVALID)

# Dictionary for Exposure Compensation Values
EXPOSURE_COMPENSATION_DICT: Dict[int, str] = {
#   others: None
    -150: "-5.0EV",
    -140: "-4.67EV",
    -130: "-4.33EV",
    -120: "-4.0EV",
    -110: "-3.67EV",
    -100: "-3.33EV",
     -90: "-3.0EV",
     -80: "-2.67EV",
     -70: "-2.33EV",
     -60: "-2.0EV",
     -50: "-1.67EV",
     -40: "-1.33EV",
     -30: "-1.0EV",
     -20: "-0.67EV",
     -10: "-0.33EV",
       0: "0.0EV",
      10: "+0.33EV",
      20: "+0.67EV",
      30: "+1.0EV",
      40: "+1.33EV",
      50: "+1.67EV",
      60: "+2.0EV",
      70: "+2.33EV",
      80: "+2.67EV",
      90: "+3.0EV",
     100: "+3.33EV",
     110: "+3.67EV",
     120: "+4.0EV",
     130: "+4.33EV",
     140: "+4.67EV",
     150: "+5.0EV",
}
EXPOSURE_COMPENSATION_DEFAULT = 0   # 0.0EV
EXPOSURE_COMPENSATION_INVALID = -9999  # Unknown exposure compensation value
EXPOSURE_COMPENSATION_STR2INT: Dict[str, int] = { v: k for k, v in EXPOSURE_COMPENSATION_DICT.items() }  # for reverse lookup
exposure_compensation_value_to_string = lambda v: EXPOSURE_COMPENSATION_DICT.get(v, "UNKNOWN")
string_to_exposure_compensation_value = lambda s: EXPOSURE_COMPENSATION_STR2INT.get(s, EXPOSURE_COMPENSATION_INVALID)

# Dictionary for Shutter Speed Values
SHUTTER_SPEED_DICT: Dict[int, str] = {
#   others: None
    # Very fast shutter speeds (ES)
    5: "1/180000",
    6: "1/160000",
    7: "1/128000",
    9: "1/102400",
    12: "1/80000",
    15: "1/64000",      # Also covers 1/65000 and 1/60000
    19: "1/51200",      # Also covers 1/50000
    24: "1/40000",
    30: "1/32000",
    38: "1/25600",      # Also covers 1/25000
    43: "1/24000",
    48: "1/20000",
    61: "1/16000",
    76: "1/12800",      # Also covers 1/13000
    86: "1/12000",
    96: "1/10000",
    122: "1/8000",
    153: "1/6400",
    172: "1/6000",
    193: "1/5000",
    # Standard shutter speeds (MS)
    244: "1/4000",
    307: "1/3200",
    345: "1/3000",
    387: "1/2500",
    488: "1/2000",
    615: "1/1600",
    690: "1/1500",
    775: "1/1250",
    976: "1/1000",
    1230: "1/800",
    1381: "1/750",
    1550: "1/640",
    1953: "1/500",
    2460: "1/400",
    2762: "1/350",
    3100: "1/320",
    3906: "1/250",
    4921: "1/200",
    5524: "1/180",
    6200: "1/160",
    7812: "1/125",
    9843: "1/100",
    11048: "1/90",
    12401: "1/80",
    15625: "1/60",
    19686: "1/50",
    22097: "1/45",
    24803: "1/40",
    31250: "1/30",
    39372: "1/25",
    44194: "1/20",      # 1/20H
    49606: "1/20",
    62500: "1/15",
    78745: "1/13",
    88388: "1/10",      # 1/10H
    99212: "1/10",
    125000: "1/8",
    157490: "1/6",
    176776: "1/6",      # 1/6H
    198425: "1/5",
    250000: "1/4",
    314980: "1/3",
    353553: "1/3",      # 1/3H
    396850: "1/2.5",
    500000: "1/2",
    629960: "1/1.6",
    707106: "1/1.5",
    793700: "1/1.3",
    1000000: "1s",
    # Longer shutter speeds
    1259921: "1.3s",
    1587401: "1.6s",   # Also covers 1.5" and 1.6"
    2000000: "2s",
    2519842: "2.5s",
    2828427: "3s",     # 3H
    3174802: "3s",
    4000000: "4s",
    5039684: "5s",
    5656854: "6s",     # 6H
    6349604: "6.5s",     # Also covers 6.5"
    8000000: "8s",
    10079368: "10s",
    11313708: "10s",   # 10H
    12699208: "13s",
    16000000: "15s",
    20158736: "20s",
    22627416: "20s",   # 20H
    25398416: "25s",
    32000000: "30s",
    35000000: "35s",
    40000000: "40s",   # 40S
    40317473: "40s",
    45000000: "45s",
    50000000: "50s",   # 50S
    50796833: "52s",
    55000000: "55s",
    60000000: "60s",   # 60S
    64000000: "60s",
    80634947: "80s",
    101593667: "110s",
    64000030: "2m",     # 2M (120")
    128000000: "140s",
    161269894: "170s",
    203187334: "210s",
    64000060: "4m",     # 4M (240")
    256000000: "250s",
    322539788: "320s",
    406374669: "420s",
    64000090: "8m",     # 8M (480")
    512000000: "500s",
    645079577: "640s",
    812749338: "850s",
    64000120: "15m",    # 15M (900")
    1024000000: "1000s",
    1290159155: "1300s",
    1625498677: "1700s",
    64000150: "30m",    # 30M (1800")
    2048000000: "2000s",
    64000180: "60m",    # 60M (3600")
    -1: "BULB",
}
SHUTTER_SPEED_DEFAULT = 15625  # 1/60
SHUTTER_SPEED_INVALID = -2     # Unknown shutter speed
SHUTTER_SPEED_STR2INT: Dict[str, int] = {v: k for k, v in SHUTTER_SPEED_DICT.items()}
shutter_speed_value_to_string = lambda v: SHUTTER_SPEED_DICT.get(v, "UNKNOWN")
string_to_shutter_speed_value = lambda s: SHUTTER_SPEED_STR2INT.get(s, SHUTTER_SPEED_INVALID)

# Converter for Aperture Values
# for intermediate values like 220 (F2.2), use converter functions instead of dictionary
APERTURE_DICT: Dict[int, str] = {    
    2200: "F22",
    2000: "F20",
    1800: "F18",
    1600: "F16",
    1400: "F14",
    1300: "F13",
    1100: "F11",
    1000: "F10",
    900: "F9.0",
    800: "F8.0",
    710: "F7.1",
    640: "F6.4",
    560: "F5.6",
    500: "F5.0",
    450: "F4.5",
    400: "F4.0",
    350: "F3.5",
    280: "F2.8",
    240: "F2.4",
    200: "F2.0",
    180: "F1.8",
    140: "F1.4",
    120: "F1.2",
    100: "F1.0",
    90: "F0.9",
}
APERTURE_DEFAULT = 560  # depends on the lens, default value is tentative
APERTURE_INVALID = 0    # Unknown aperture value
APERTURE_STR2INT: Dict[str, int] = {v: k for k, v in APERTURE_DICT.items()}  # for reverse lookup
#aperture_value_to_string = lambda v: APERTURE_DICT.get(v, "UNKNOWN")
#string_to_aperture_value = lambda s: APERTURE_STR2INT.get(s, APERTURE_INVALID)
def aperture_value_to_string(aperture_value) -> str:
    if aperture_value in APERTURE_DICT:
        return APERTURE_DICT[aperture_value]
    elif aperture_value < 80:   # limit F0.8
        return "F0.0"   # UNKNOWN
    else:
        # 200 -> F2.0, 280 -> F2.8, 1000 -> F10, etc.
        aperture_number = aperture_value / 100
        if aperture_number >= 10 and aperture_number.is_integer():
            return f"F{int(aperture_number)}"   # no decimal place
        else:
            return f"F{aperture_number:.1f}"    # keep one decimal place

def string_to_aperture_value(aperture_string) -> int:
    if aperture_string in APERTURE_STR2INT:
        return APERTURE_STR2INT[aperture_string]
    elif aperture_string.startswith("F") or aperture_string.startswith("f"):
        try: # F2.0 -> 200, F2.2 -> 220, F2.8 -> 280, F3.5 -> 350, etc.
            aperture_value = int( float(aperture_string[1:]) * 100 )
            return aperture_value
        except ValueError:
            return APERTURE_INVALID
    return APERTURE_INVALID

# Dictionary for ISO Sensitivity Values
ISO_SENSITIVITY_DICT: Dict[int, str] = {
    # Positive ISO values (standard ISO settings)
    40: "ISO 40",
    50: "ISO 50",
    60: "ISO 60",
    64: "ISO 64",
    80: "ISO 80",
    100: "ISO 100",
    125: "ISO 125",
    160: "ISO 160",
    200: "ISO 200",
    250: "ISO 250",
    320: "ISO 320",
    400: "ISO 400",
    500: "ISO 500",
    640: "ISO 640",
    800: "ISO 800",
    1000: "ISO 1000",
    1250: "ISO 1250",
    1600: "ISO 1600",
    2000: "ISO 2000",
    2500: "ISO 2500",
    3200: "ISO 3200",
    4000: "ISO 4000",
    5000: "ISO 5000",
    6400: "ISO 6400",
    8000: "ISO 8000",
    10000: "ISO 10000",
    12800: "ISO 12800",
    16000: "ISO 16000",
    20000: "ISO 20000",
    25600: "ISO 25600",
    32000: "ISO 32000",
    40000: "ISO 40000",
    51200: "ISO 51200",
    64000: "ISO 64000",
    80000: "ISO 80000",
    102400: "ISO 102400",

    # Negative ISO values (AUTO settings)
    -1: "ISO AUTO (1)",
    -2: "ISO AUTO (2)",
    -3: "ISO AUTO (3)",
    -4: "ISO AUTO (4)",
    -10: "ISO AUTO",
    -400: "ISO AUTO 400",
    -800: "ISO AUTO 800",
    -1600: "ISO AUTO 1600",
    -3200: "ISO AUTO 3200",
    -6400: "ISO AUTO 6400",
}
ISO_SENSITIVITY_DEFAULT = 400  # ISO 400
ISO_SENSITIVITY_INVALID =   0  # Unknown ISO sensitivity value
ISO_SENSITIVITY_STR2INT: Dict[str, int] = {v: k for k, v in ISO_SENSITIVITY_DICT.items()}  # for reverse lookup
iso_sensitivity_value_to_string = lambda v: ISO_SENSITIVITY_DICT.get(v, "UNKNOWN")
string_to_iso_sensitivity_value = lambda s: ISO_SENSITIVITY_STR2INT.get(s, ISO_SENSITIVITY_INVALID)

# Dictionary for White Balance Values
#WHITE_BALANCE_MODES_DICT = {}

# Image Quality options
IMAGE_QUALITY_DICT = {
    0x0001: "RAW",
    0x0002: "FINE",
    0x0003: "NORMAL",
    0x0004: "RAW+FINE",
    0x0005: "RAW+NORMAL",
    0x0006: "SUPERFINE",
    0x0007: "RAW+SUPERFINE",
}
IMAGE_QUALITY_DEFAULT = 0x0002
IMAGE_QUALITY_INVALID = 0x0000  # Unknown image quality
IMAGE_QUALITY_STR2INT: Dict[str, int] = {v: k for k, v in IMAGE_QUALITY_DICT.items()}  # for reverse lookup
image_quality_value_to_string = lambda v: IMAGE_QUALITY_DICT.get(v, "UNKNOWN")
string_to_image_quality_value = lambda s: IMAGE_QUALITY_STR2INT.get(s, IMAGE_QUALITY_INVALID)

# Image Size options
IMAGE_SIZE_DICT: Dict[int, str] = {
    1  : "S 3:2",  
    2  : "S 16:9",
    3  : "S 1:1", 
    4  : "M 3:2",
    5  : "M 16:9",
    6  : "M 1:1",
    7  : "L 3:2",
    8  : "L 16:9", 
    9  : "L 1:1",
    10 : "S 4:3",
    11 : "S 65:24",
    12 : "S 5:4",
    13 : "S 7:6",
    14 : "L 4:3", 
    15 : "L 65:24",
    16 : "L 5:4",
    17 : "L 7:6",
    18 : "M 4:3",
    19 : "M 65:24",
    20 : "M 5:4",
    21 : "M 7:6",
    22 : "L 3:4",
    23 : "L 17:6",
    24 : "M 3:4",
    25 : "M 17:6", 
    26 : "S 3:4",
    27 : "S 17:6",
}
IMAGE_SIZE_DEFAULT = 7
IMAGE_SIZE_INVALID = 0  # Unknown image size
IMAGE_SIZE_STR2INT: Dict[str, int] = {v: k for k, v in IMAGE_SIZE_DICT.items()}  # for reverse lookup
image_size_value_to_string = lambda v: IMAGE_SIZE_DICT.get(v, "UNKNOWN")
string_to_image_size_value = lambda s: IMAGE_SIZE_STR2INT.get(s, IMAGE_SIZE_INVALID)

FOCUS_AFMODE_DICT: Dict[int, str] = {
    0x8001: "SINGLE",
    0x8002: "ZONE",
    0x8003: "WIDETRACKING",
    0x8004: "ALL"
}
FOCUS_AFMODE_DEFAULT = 0x8001
FOCUS_AFMODE_INVALID = 0  # Unknown AF mode
FOCUS_AFMODE_STR2INT: Dict[str, int] = {v: k for k, v in FOCUS_AFMODE_DICT.items()}  # for reverse lookup
focus_afmode_value_to_string = lambda v: FOCUS_AFMODE_DICT.get(v, "UNKNOWN")
string_to_focus_afmode_value = lambda s: FOCUS_AFMODE_STR2INT.get(s, FOCUS_AFMODE_INVALID)

FOCUS_SIZE_DICT: Dict[int, str] = {
    0: "Smallest",
    1: "Smaller",
    2: "Small",
    3: "Medium",
    4: "Large",
    5: "Larger",
    6: "Largest", 
    17: "ZONE Smallest",   
    18: "ZONE Small",
    19: "ZONE Large",
    20: "ZONE Largest",
}
FOCUS_SIZE_DEFAULT = 3  # Medium / ZONE Large
FOCUS_SIZE_INVALID = -1  # Unknown focus size
FOCUS_SIZE_STR2INT: Dict[str, int] = {v: k for k, v in FOCUS_SIZE_DICT.items()}  # for reverse lookup
focus_size_value_to_string = lambda v: FOCUS_SIZE_DICT.get(v, "UNKNOWN")
string_to_focus_size_value = lambda s: FOCUS_SIZE_STR2INT.get(s, FOCUS_SIZE_INVALID)

FINDER_CROP_DICT: Dict[int, str] = { # from SDK_THROUGHIMAGE_ZOOM_*
   0x0001: "x1.0",  # no cropping at single AF position
   0x0002: "x2.5",  # x2.5 cropping at single AF position
   0x0003: "x6.0",
   0x0004: "x4.0",
   0x0005: "x8.0",
   0x0006: "x16.0",
   0x0007: "x20.0",
   0x0008: "x33.0",
   0x0009: "x66.0",
    0x000A: "x131.0",
    0x000B: "x240.0",
    0x000C: "x197.0",
    0x000D: "x83.0",
    0x000E: "x170.0",
    0x000F: "x68.0",
    0x0010: "x140.0",
    0x0011: "x120.0",
}
FINDER_CROP_DEFAULT = 0x0001
FINDER_CROP_INVALID = 0  # Unknown finder crop
FINDER_CROP_STR2INT: Dict[str, int] = {v: k for k, v in FINDER_CROP_DICT.items()}  # for reverse lookup
finder_crop_value_to_string = lambda v: FINDER_CROP_DICT.get(v, "UNKNOWN")
string_to_finder_crop_value = lambda s: FINDER_CROP_STR2INT.get(s, FINDER_CROP_INVALID)

LIVEVIEW_SIZE_DICT: Dict[int, str] = {
    0x0001: "L",  # 1024 or 1280
    0x0002: "M",   # 640 or  800
    0x0003: "S",   # 320 or  640
}
LIVEVIEW_SIZE_DEFAULT = 0x0001
LIVEVIEW_SIZE_INVALID = 0  # Unknown liveview size
LIVEVIEW_SIZE_STR2INT: Dict[str, int] = {v: k for k, v in LIVEVIEW_SIZE_DICT.items()}  # for reverse lookup
liveview_size_value_to_string = lambda v: LIVEVIEW_SIZE_DICT.get(v, "UNKNOWN")
string_to_liveview_size_value = lambda s: LIVEVIEW_SIZE_STR2INT.get(s, LIVEVIEW_SIZE_INVALID)

LIVEVIEW_QUALITY_DICT: Dict[int, str] = {
    0x0001: "FINE",
    0x0002: "NORMAL",
    0x0003: "BASIC",
}
LIVEVIEW_QUALITY_DEFAULT = 0x0001
LIVEVIEW_QUALITY_INVALID = 0  # Unknown liveview quality
LIVEVIEW_QUALITY_STR2INT: Dict[str, int] = {v: k for k, v in LIVEVIEW_QUALITY_DICT.items()}  # for reverse lookup
liveview_quality_value_to_string = lambda v: LIVEVIEW_QUALITY_DICT.get(v, "UNKNOWN")
string_to_liveview_quality_value = lambda s: LIVEVIEW_QUALITY_STR2INT.get(s, LIVEVIEW_QUALITY_INVALID)

SDK_VALUE_TO_STRING: Dict[str, Callable[[int], str]] = {
    "program_mode": program_mode_value_to_string,
    "exposure_compensation": exposure_compensation_value_to_string,
    "shutter_speed": shutter_speed_value_to_string,
    "aperture": aperture_value_to_string,
    "iso_sensitivity": iso_sensitivity_value_to_string,
    "image_quality": image_quality_value_to_string,
    "image_size": image_size_value_to_string,
    "focus_mode": focus_mode_value_to_string,
    "focus_size": focus_size_value_to_string,
    "focus_afmode": focus_afmode_value_to_string,
    "finder_crop": finder_crop_value_to_string,
    "liveview_size": liveview_size_value_to_string,
    "liveview_quality": liveview_quality_value_to_string,
}
sdk_value_to_string = lambda category, value: SDK_VALUE_TO_STRING[category](value)

STRING_TO_SDK_VALUE: Dict[str, Callable[[str], int]] = {
    "program_mode": string_to_program_mode_value,
    "exposure_compensation": string_to_exposure_compensation_value,
    "shutter_speed": string_to_shutter_speed_value,
    "aperture": string_to_aperture_value,
    "iso_sensitivity": string_to_iso_sensitivity_value,
    "image_quality": string_to_image_quality_value,
    "image_size": string_to_image_size_value,
    "focus_mode": string_to_focus_mode_value, 
    "focus_size": string_to_focus_size_value,
    "focus_afmode": string_to_focus_afmode_value,
    "finder_crop": string_to_finder_crop_value,
    "liveview_size": string_to_liveview_size_value,
    "liveview_quality": string_to_liveview_quality_value,
}
string_to_sdk_value = lambda category, string: STRING_TO_SDK_VALUE[category](string)
