## Python Library using FUJIFILM Digital Camera SDK

### Overview:
PCに接続したデジタルカメラをpythonコードで手軽に制御可能にするパッケージです。\
安価なWebカメラでは困難なレンズ交換型ミラーレス一眼カメラならではの撮影領域（高速シャッターや長時間露光、高解像度、高感度やダイナミックレンジ、光学倍率等々）が活かせる場はたくさんありますが、メーカーが一般提供するSDKはC/C++用バイナリが主流なのでプライベートなニーズに合わせた活用のハードルが高くなっています。\
利用者の多いpythonの環境で容易に記述ができるインタフェースを整えることで、AIのアシストも利用しやすくなり、Webカメラのように手軽にデジタルカメラを活用できるようになることが目的です。

なお、本パッケージは富士フイルムのデジタルカメラX/GFXシリーズ（テザー撮影対応機種）専用です。\
実行にはメーカーが提供するSDKを使用しますが、SDKの利用規約（EULA）の制約でパッケージにバンドルできないため、利用者は各自でメーカーサイトからPCにダウンロードしていただく必要があります。\
また、本ソフトウェアはサードパーティ製の⾮公式ソフトウェアであり、富⼠フイルム株式会社とは関係ありません。

---
### Installation:
```bsh
# install from PyPI
pip install fujixcam
```

---
### Requirements:
```
Python 3.11+
Windows 11 or macOS 14+
```
---
### Structure: 
カメラメーカーのSDK（C/C++用APIライブラリのバイナリ）に接続する下位レイヤーと、より抽象化した上位レイヤーの2段階で構成し、用途に応じてレイヤーを選択できます。
- 標準的な使い方ならインタフェースをシンプルにした上位レイヤー（Cameraクラス）を使って短いステップで簡単に動作させることができます。
- より自由にカメラの操作を組み合わせて使いたい場合は下位レイヤー（CameraAPIクラス）を使用できます。

いずれかを初めて実行した時にSDKのバイナリファイルのパスをCONSOLEで聞いてきますので入手済みの保存場所を入力してください（2回目からは不要です）。

---
### Quick Start:
上位レイヤー（Cameraクラス）はカメラオブジェクトを作成することによってカメラとの接続が確立されます。\
機能の呼び出しは可読な文字列を引数に指定して行います。

```python
#
# capture photo by auto exposure mode
#
import fujixcam

# create Camera object
camera = fujixcam.Camera()  # wait for connection to the default camera and establish it, configure initial settings
camera.is_connected()   # -> True

# setup options and recieve current settings and options
result = camera.setup( program_mode = "P",  iso_sensitivity="ISO 400" )
print(f"{result.settings}\n{result.options}") if result.success else print(result.error_message)
# {'exposure':ExposureSettings(...), 'focus':FocusSettings(...), ...}
# {'exposure':ExposureOptions(...), 'focus':FocusOptions(...), ...}

# take picture and save as image file to PC storage
result = camera.capture()
print(result.image_files) if result.success else print(result.error_message)
# ['2026_0710_1201-302201.raw', '2026_0710_1201-302201.jpg']

# take a long exposure photo using bulb mode (settings are configured automatically)
result = camera.bulb_capture(exposure_time=15)      # exposure_time in seconds
print(result.image_files) if result.success else print(result.error_message)

camera.close()      # restore camera to initial state and close connection
```

---
### Advanced Usage Samples:
撮影モードを設定すると対応する設定項目が有効になったことが確認できます。
```python
result = camera.setup( program_mode="A", aperture="F2.8", focus_mode="AF-S" )
print(result.options["exposure"]) 
# ExposureOptions(..., iso_sensitivity=['ISO 80',...], aperture=['F2.0', 'F2.2', 'F2.5', ...], shutter_speed=[], exposure_compensation=['-5.0EV', '-4.67EV', ... ]

# Capturing by all available exposure compensation values
for ev in result.options["exposure"].exposure_compensation:
    camera.setup( exposure_compensation=ev )        # other settings remain unchanged
    result = camera.capture( folder="myfolder" )
    print( f"{ev}: {result.folder}/{result.image_files[-1]}" )
    # -5.0EV: myfolder/2026_0710_1201-302201.jpg
    # -4.67EV: myfolder/2026_0710_1201-...

# Focus settings can be adjusted similarly using the available options.
# - focus distance in manual focus mode (MF) is represented as a tuple (INF, MOD, STEP)
result = camera.setup( focus_mode="MF" )
print(result.options["focus"].mf_distance)  # -> (22, 1402, 5) 
for distance in result.options["focus"].mf_distance:    # (infinity, minimum object distance, step)
    camera.setup( mf_distance=distance )  # set manual focus distance to each available value

# - continuous auto-focus in AF-C mode
result = camera.setup( focus_mode="AF-C", af_mode="SINGLE" )
print(result.options["focus"])
# FocusOptions(..., af_mode=['SINGLE', 'ZONE',...], af_point_h=[-6, -5, ...], af_point_v=[..., 3, 4], ...)

# - move focus point and start continuous auto-focus and stop it
result = camera.focus_on( h=2, v=3, af_on=True) 
print(resut.camera_status)  # -> CameraStatus(..., conditions=['focusing', 'af_locked']))
result = camera.focus_off()
print(resut.camera_status)  # -> CameraStatus(..., conditions=[])
```
for more information, see GUIDE_Camera.md

---
### Advanced Usage with CameraAPI:
下位レイヤー（CameraAPIクラス）はオブジェクトの作成によってメーカーのSDKとリンクし通信経路を作ります。\
SDKのヘッダー定義値を使ってカメラとのコマンドのやりとりを行います。\
値の理解やコマンドによる状態遷移、モードに応じた制約条件などの知識が必要になります。\
そのぶん、SDKの粒度に近い操作が可能です。

```python
#
# capture photo by auto exposure mode
#
import fujixcam
xcam = fujixcam.CameraAPI()

# connect to default camera via USB
response = xcam.connect(0) 
# if not response.success:
#   repeat the connection attempt until success
print(response.data)
# {data={'camera_count': 1, 'camera_index': 0, 'camera_name': 'FUJIFILM X-S10', 'lens_name': 'XF35mmF2 R WR'})
xcam.is_connected()     # -> True

# check current camera status
response = xcam.get_status()
print(response.data)
# {'buffered': (0, 16), 'liveview': False, 'pre_af': False, 'shooting': False, 'bulb': False, 'S1': False, 'AF': False, 'AEL': False, 'AFL': False, 'WBL': False}

# turn to program mode 'P'
response = xcam.get_program_mode_options()
print(response.options)  # -> [1, 3, 4, 6]
response = xcam.set_program_mode(6)       # 6 is program mode 'P' (defined in the SDK header)

# change focus mode
response = xcam.get_focus_mode_options()
print(response.options)  # -> [1, 32769, 32770]   # 1: MF, 32769: AF-S, 32770: AF-C
response = xcam.set_focus_mode(0x8001)          # 0x8001(=32769) means AF-S

# if you need to restore the camera settings, you can call appropriate methods here before disconnecting
# xcam...

# disconnect from the camera
xcam.disconnect()       

#
# using api_dictionary, the code can be written as bellow. 
#
from fujixcam.camera_api_dictionary import *
response = xcam.set_program_mode( string_to_program_mode_value("P") )
response = xcam.set_focus_mode( string_to_focus_mode_value("AF-S") )
```
for more information, see GUIDE_CameraAPI.md

---
### Plan of this project:
このパッケージは下記の計画のステップ１です。
1. バイブコーディングでデジタルカメラを操作できるようにする
2. AIエージェントがMCP経由で高性能デジタルカメラを操れるようにする

ステップ2 では以下のようにMCPサーバーを導入できます。
```
# install from PyPI and run the server
pip install fujixcam-mcp
python -m fujixcam_mcp.server
```

Note:
- 本パッケージがサポートするのはSDKの一部の機能に限られますが、今後拡張する可能性があります。

---
### Config and Terms:
本パッケージのpythonコードはMITライセンスを適用します。\
但し本パッケージの動作にはpythonコードのほかにカメラメーカーが提供するSDKのバイナリコードが必要です。\
バイナリコードはバンドルしていませんので、利用者自身でメーカーのサイトからダウンロードしていただく必要があります。\
https://www.fujifilm-x.com/special/camera-control-sdk \
バイナリコードへは実行時に動的に接続しますので任意のフォルダに展開してください。\
ダブルライセンスへの対応として初回起動時にメーカーのSDKに関するクリックラップを行います。

---
### Known Issues
- 全ての機種での確認を行っているわけではありません。カメラにより異なる挙動や期待通りに動作しない場合があります。

---
### package includes:
- camera.py:　　単純化したカメラオブジェクトを提供する
- result.py:　　カメラ操作の結果を格納するオブジェクトを提供する
- camera_api.py:　	カメラSDKを呼び出す抽象度の低いAPIを提供する
- camera_api_dictionary.py:　カメラSDK用パラメータの意味を言語化する辞書を提供する

---
## repository and contributions

- Repository:
  - https://github.com/mterada/fujixcam-api
- Documentations:
  - https://github.com/mterada/fujixcam-api/README.md
  - https://github.com/mterada/fujixcam-api/GUIDE_Camera.md
  - https://github.com/mterada/fujixcam-api/GUIDE_CameraAPI.md
- Discussions:
  - https://github.com/mterada/fujixcam-api/discussions

Note:
- メンテナンスリソースが限られるため、GitHubでの Issue および Pull Request は制限しています。
- 本パッケージに関する質問や要望は、GitHub Discussions を利用してください。

---

