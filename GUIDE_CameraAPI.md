**CameraAPI GUIDE**
---
# Get started
1. パッケージの入手
```bash
# install from PyPI
pip install fujixcam

``` 
2. カメラメーカーのSDKを入手\
https://www.fujifilm-x.com/special/camera-control-sdk \
カメラメーカーのWebサイトから規約に従ってSDKを入手しPC（Windows/Mac）の任意のフォルダに解凍する。\
展開したフォルダの REDISTRIBUTION フォルダの下位階層で xapi.dat ファイルのあるフォルダのパス名を確認しておく（この後で必要になります）。

3. python で CameraAPI モジュールを読み込む
```python
import fujixcam
xcam = fujixcam.CameraAPI()
# Exception:
#	RuntimeError("Failed to load FUJIFILM SDK library.")
#	RuntimeError("Multiple instances are not supported.")
```

4. クリックラップ  \
初回のインスタンス生成時にカメラSDKの場所を聞いてくるので、上記2.で確認したフォルダのパスを入力する。\
SDKのEULAに同意済みかを確認するダイアログが表示されるので、同意して「y」を入力する。\
クリックラップは初回のみで、次回以降は自動的にSDKがロードされる。
```python
xcam = fujixcam.CameraAPI()
#FUJIFILM_CAMERA_CONTROLL_SDK not found. / FUJIFILM_CAMERA_CONTROLL_SDK が見つかりませんでした。
# :   
#If you have already installed the SDK, please enter the installation path to load the library.
#入手済みであれば保存先のSDKモジュールのフォルダ名（フルパス）を教えてください。
# :
#Please enter the path to FUJIFILM_CAMERA_CONTROLL_SDK (or press Enter to retry): {xapi.datのあるフォルダのパス名}
# :
#Checking FUJIFILM_CAMERA_CONTROLL_SDK module in: ...
#Loaded FUJIFILM_CAMERA_CONTROLL_SDK from: ...
```
指定したフォルダのパスが正しければ、SDKがロードされ、CameraAPIのインスタンスが生成されます。

5. メソッドとレスポンス
```python
import fujixcam
xcam = fujixcam.CameraAPI()
response = xcam.connect() 
if response.success:
	print(f"data={response.data}")
	# data={'camera_count': 1, 'camera_index': 0, 'camera_name': 'FUJIFILM X-S10', 'lens_name': 'XF35mmF2 R WR'}
else:
	print(response.error_message)	# -> "No camera detected."
#	retry xcam.connect() until successful
# ...
# response = xcam.{method_name}
# response = xcam.{method_name}
# ...
xcam.disconnect()
```

# Interface overview
response と method の使い方は以下の通り。
## Response
method に応じた response が返される。
- 成功／失敗の情報のみを返すメソッド：APIResponse
	- response.success	= True/False
	- response.error_message = エラーに関する情報の文字列

- 数値を返すメソッド：APIResponseValue
	- response.success	= True/False
	- response.error_message
	- response.value = int値

- 数値のリストを返すメソッド：APIResponseList
	- response.success  = True/False
    - response.error_message
	- response.options = \[...\]  int値の配列

- 上記以外の情報を返すメソッド：APIResponseDict
	- response.success  = True/False
	- response.error_message
	- response.data = \{...\}	 辞書型データ
---
## Method list
### session and status management
|method|description|
|---|---|
|connect()	|	カメラに接続する。USBまたはWifi経由で接続可能。|
|is_connected() |	接続されているかを確認する。|
|disconnect()	|	カメラとの接続を終了する。|
|get_status()	|	カメラの状態パラメータを返す。|
|reset_status()	|	カメラの状態遷移を初期状態にリセットする。|

### Shooting operations
|method|description|
|---|---|
|capture_image()|1枚撮影して画像ファイルを保存する。|
|capture_multi_images()|連続撮影して複数画像ファイルを保存する。|
|capture_preview()|プレビュー用の小さいJPEG画像をバッファで取得する。|
|bulb_on()|バルブ撮影を開始する。|
|bulb_off()|バルブ撮影を終了し、必要に応じて画像を保存する。|
|perform_af()|AF動作（半押し相当）を実行／停止する。|
|af_lock()|AFロックを有効／解除する。|
|ae_lock()|AEロックを有効／解除する。|
|awb_lock()|AWBロックを有効／解除する。|
|shoot_from_camera()|カメラ本体のシャッターボタンを押して撮影する。|
|acquire_images()|カメラのシャッターボタンで撮影した画像を取得する。|

### Exposure settings and options
|method|description|
|---|---|
|get_program_mode_options()	|	選択可能なAEプログラムモード一覧を返す。|
|get_program_mode()	|	現在のAEプログラムモードを返す。|
|set_program_mode()	|	AEプログラムモードを設定する。|
|get_exposure_compensation_options()	|	選択可能な露出補正値の一覧を返す。|
|get_exposure_compensation()	|	現在の露出補正値を返す。|
|set_exposure_compensation()	|	露出補正値を設定する。|	
|get_shutter_speed_options()	|	選択可能なシャッター速度の一覧を返す。|
|get_shutter_speed()	|	現在のシャッター速度を返す。|
|set_shutter_speed()	|	シャッター速度を設定する。|
|get_aperture_value_options()	|	選択可能な絞り値の一覧を返す。|
|get_aperture_value()	|	現在の絞り値を返す。|
|set_aperture_value()	|	絞り値を設定する。|
|get_iso_sensitivity_options()	|	選択可能なISO感度の一覧を返す。|
|get_iso_sensitivity()	|	現在のISO感度を返す。|
|set_iso_sensitivity()	|	ISO感度を設定する。|

### Focus settings and options
|method|description|
|---|---|
|get_focus_mode_options()|選択可能なフォーカスモード一覧を返す。|
|get_focus_mode()|現在のフォーカスモードを返す。|
|set_focus_mode()|フォーカスモード（必要に応じてPreAF）を設定する。|
|get_focus_area_options()|選択可能なフォーカスエリア（h/v/size）の範囲を返す。|
|get_focus_area()|現在のフォーカスエリア（h/v/size）を返す。|
|set_focus_area()|フォーカスエリア（h/v/size）を設定する。|
|get_focus_distance_range()|フォーカス距離の設定可能範囲を返す。|
|get_focus_distance()|現在のフォーカス距離を返す。|
|set_focus_distance()|フォーカス距離を設定する。|
|get_focus_afmode_options()|選択可能なAFモードの一覧を返す。|
|get_focus_afmode()|現在のAFモードを返す。|
|set_focus_afmode()|AFモードを設定する。|

### Image quality settings and options
|method|description|
|---|---|
|get_image_quality_options()|選択可能な画質モードの一覧を返す。|
|get_image_quality()|現在の画質設定を返す。|
|set_image_quality()|画質設定を変更する。|
|get_image_size_options()|選択可能な画像サイズの一覧を返す。|
|get_image_size()|現在の画像サイズを返す。|
|set_image_size()|画像サイズを変更する。|

### Liveview acquisition
|method|description|
|---|---|
|get_liveview_quality_options()|選択可能なライブビュー画質オプションを返す。|
|get_liveview_quality()|現在のライブビュー画質を返す。|
|set_liveview_quality()|ライブビュー画質を設定する。|
|get_liveview_size_options()|選択可能なライブビューサイズオプションを返す。|
|get_liveview_size()|現在のライブビューサイズを返す。|
|set_liveview_size()|ライブビューサイズを設定する。|
|get_finder_crop_options()|選択可能なファインダークロップ（DigitalZoom）を返す。|
|get_finder_crop()|現在のファインダークロップ設定を返す。|
|set_finder_crop()|ファインダークロップ設定を変更する。|
|start_liveview()|ライブビューを開始する。|
|stop_liveview()|ライブビューを停止する。|
|get_liveview_image()|最新のライブビュー画像をバッファで取得する。|

### Other operations
|method|description|
|---|---|
|get_lens_zoom_capability()	|	レンズのズーム能力（選択可能なズーム位置の一覧など）を返す。|
|get_lens_zoom()	|	現在のレンズのズーム位置を返す。|
|set_lens_zoom()	|	レンズのズーム位置を設定する。|

---

# Interface details
## Camera connection and status management 
### connect
```
connect()
connect( index=0 )
connect( ip_address="xx.xx.xx.xx" )

response:APIResponseDict
	.success	   # True/False
	.error_message # エラーに関する情報の文字列
	.data = {
		"product_name":{接続したカメラとレンズの製品名文字列},
		...
	}
```
デフォルトではUSBで検出された最初のカメラに接続する。\
接続した時点のカメラの設定状態が引き継がれるため、メソッドでサポートしていない設定は必要に応じて事前にカメラ本体の操作で設定しておく。

- index\
USBに複数台のカメラが接続されている場合は、index=0,1,2,...で指定する。\
カメラの接続設定はテザーモード（USB AUTO）に設定し、静止画と動画のモードが分かれているカメラでは connect する前に静止画撮影モードにしておく必要がある。\
一定時間通信がないとカメラがスリープして接続が切れてしまうためカメラの電源設定はオートパワーOFFなしにしておく。

- ip_address\
Wifi経由で接続する場合に使用する。\
IPアドレスはカメラの設定画面で確認する。

### is_connected()
```
is_connected()

response:bool = {True|False}
```
接続されている場合は True を返す。接続されていない場合は False を返す。\
このメソッドは例外的に bool を返す。\
Note:\
このメソッドを呼ぶと状態の確認のためにカメラとの通信が発生するが、これによってカメラのスリープを抑止・解除することはできない。

### disconnect()
```
disconnect()
disconnect(shotdown=True)

response:APIResponse
	.success
	.error_message
```
カメラとの接続を終了する。shotdownを指定するとカメラは接続終了後に電源OFFされる。

### get_status()

```
get_status()

response:APIResponseDict
	.success
	.error_message
	.data = {
		"buffered": (i, n)	    使用済みバッファ数 i, 使用可能な撮影バッファ数 n
		"liveview": True/False  ライブビューの稼働状態
		"pre_af": True/False	常時オートフォーカス動作中
		"shooting": True/False	長時間露光等の撮影処理中
		"bulb": True/False   	Bulb撮影中
		"S1": True/False	シャッター半押し（撮影待ち）
		"AF": True/False	Continuous-AFのオートフォーカス動作中
		”AFL": True/False	AFロック中（撮影待ち）
		"AEL": True/False	AEロック中（撮影待ち）
		"WBL": True/False	ホワイトバランスロック中（撮影待ち）
	}
```
カメラの状態パラメータを返す。\
いずれかの状態がTrueのときは状態が解除されるまで、使用できるmethodが限られている。

### reset_status()
```
reset_status()

response:APIResponse
	.success
	.error_message
```
カメラを撮影待機状態にリセットする。
成功すれば get_status() が返す状態値はすべて False, 使用済みバッファ数は０にリセットされる。

## Shooting operations
### capture_image()
```
capture_image()
capture_image(folder={yourfolder})
capture_image(folder={yourfolder}, filename={filename}, long_exposure=False)

response:APIResponseDict
	.success
	.error_message
	.data = {
		"folder": 保存先のフォルダ名
		"filename": 保存したファイル名（拡張子なし）
		"datasize": 保存したバイト数（RAW+JPEGのときは合計サイズ）
		"object": [ RAWファイル名, JPEGファイル名 ]	（拡張子あり）
		あるいは
		"object": [ RAWファイル名 or JPEGファイル名 ] （拡張子あり）
	}
```
1枚撮影して指定したフォルダに自動的に新しいファイル名で保存する。\
ファイル名は yyyy_mmdd_hhmmssss.jpg の形式で保存される。\
戻り値の object はJPEGのみであっても要素数1のリストとなることに注意する。
- folder\
	保存先のフォルダ名を指定する。\
	フォルダを指定しない場合あるいは指定したフォルダがない場合はカレントフォルダに保存される。
- filename\
	ファイルのベースネームを指定して保存したい場合に指定する。\
	フォルダパスと拡張子を除いたファイル名のみを指定する必要がある。\
	(RAW+JPEGでは同一ファイル名で異なる拡張子が使用されるため) \
	同名のファイルがすでに存在する場合は上書きする。
- long_exposure\
	10秒以上の長時間露光時は long_exposure をTrueにする。\
	暗所でAE撮影を行うなど実行時にカメラ側でシャッター速度が決まる状況では異常判定のためのtimeout時間を長くする必要があるため。

### capture_multi_images()
```
capture_multi_images()
catpure_multi_images(folder={yourfolder})
catpure_multi_images(folder={yourfolder}, count={image_count}, interval={interval_sec})

response:APIResponseDict
	.success
	.error_message
	.data = {
		"datasize": 保存したバイト数の合計
		"objects": [	# capture_image の data 形式によるリスト
			{ "folder":フォルダ名, "filename":ファイル名, "datasize":バイト数, "object":[...] },
			{ "folder":フォルダ名, "filename":ファイル名, "datasize":バイト数, "object":[...] },
			...
		]
	}
```
複数枚を連続撮影してフォルダに自動的に新しいファイル名で保存する。\
カメラのバッファに溜めてからまとめて保存することで撮影間隔を短くするもので、カメラ本体の連写機能とは異なる。\
あらかじめフォーカスロックする、電子シャッターを使用するなどを組み合わせることで、高速な連写が可能になる。
- folder\
	保存先のフォルダ名を指定する。\
	フォルダを指定しない場合あるいは指定したフォルダがない場合はカレントフォルダに保存される。
- count\
	撮影する枚数を指定する。
	枚数のデフォルトは5枚、指定できる最大枚数は get_status()で得られるバッファ数まで。
- interval\
	前の撮影が終了してから次の撮影トリガーまでの待ち時間を調整する。\
	単位は秒で、デフォルトは0.01秒。

### capture_preview()
```
capture_preview()

response:APIResponseDict
	.success
	.error_message
	.data = {
		"buffer": bytearrayに変換されたJPEGデータ
		"size": バイナリでのデータバイト数
	}
```
1枚テスト撮影して小さいプレビュー画像のみをバッファで受け取る。\
capture_image()と同じ撮影設定が使用されるが、露出時間は10秒以内のみ対応、撮影画像は保存されない。

### bulb_on()
```
bulb_on()

response:APIResponse
	.success
	.error_message
```
バルブ撮影を開始する。\
マニュアル露出モードかつシャッター速度が"Bulb"に設定されているときのみ可能。\
バルブ撮影中は get_status() の bulb が True となる。\
バルブ撮影の中止または終了は bulb_off() で行う。

### bulb_off()
```
bulb_off( folder="yourfolder" )
bulb_off( abort=True )

response:APIResponseDict
	.success
	.error_message
	.data = {
		"folder": 保存先のフォルダ名
		"filename": 保存されたファイル名
		"datasize": 保存されたバイト数
		"object": [ RAWファイル名, JPEGファイル名 ]	（拡張子あり）
	}
```
バルブ撮影を終了して画像を指定のフォルダに保存する。\
保存終了、中止いずれの場合も、カメラ内での後処理の時間が必要で、制御が戻るまでに時間がかかる場合がある。
- folder\
	保存先のフォルダ名を指定する。\
	フォルダを指定しない場合あるいは指定したフォルダがない場合はカレントフォルダに保存される。
- abort\
	バルブ撮影を中止する。（ファイルは保存されない）

### perform_af()
```
perform_af()
perform_af(enable={True|False})

response:APIResponse
	.success
	.error_message
```
シャッター半押し相当のAF動作を実行する。\
マニュアルフォーカス、オートフォーカスいずれのモードでも使用可能。\
但し、オートフォーカスでPreAFが動作中は何もしない。
- enable\
	コンティニュアスAFモードのとき、TrueでAF動作を開始、FalseでAF動作を停止する。\
	AF動作を開始すると、AFを停止するまで get_status() の AF が True となる。\
	enbleを指定しない場合のデフォルト動作は、True（AF動作を開始する）である。

### af_lock()
```
af_lock()
af_lock({True|False})

response:APIResponse
	.success
	.error_message
```
オートフォーカスモード時にAFロックを有効／解除する。\
引数省略時のデフォルトは True（有効） である。\
AFロックが有効になると get_status() の AFL が True となる。\
AFロック中は設定変更等の操作が制限されるため、撮影が終了したら af_lock(False) で解除する。\
reset_status() によっても AFロックは解除される。

### ae_lock()
```
ae_lock()
ae_lock({True|False})

response:APIResponse
	.success
	.error_message
```
自動露出モード時にAEロックを有効／解除する。\
引数省略時のデフォルトは True（有効） である。\
AEロックが有効になると get_status() の AEL が True となる。\
AEロック中は設定変更等の操作が制限されるため、撮影が終了したら ae_lock(False) で解除する。\
reset_status() によっても AEロックは解除される。

### awb_lock()
```
awb_lock()
awb_lock({True|False})

response:APIResponse
	.success
	.error_message
```
オートホワイトバランスモード時にAWBロックを有効／解除する。\
引数省略時のデフォルトは True（有効） である。\
AWBロックが有効になると get_status() の WBL が True となる。\
AWBロック中は設定変更等の操作が制限されるため、撮影が終了したら awb_lock(False) で解除する。\
reset_status() によっても AWBロックは解除される。

###	shoot_from_camera()
```
shoot_from_camera()
shoot_from_camera({True|False})

response:APIResponse
	.success
	.error_message
```
カメラの操作を有効化してカメラ本体のシャッターボタンを押して撮影できるようにする。\
引数省略時のデフォルトは True である。\
この関数自体はすぐにリターンしてくるので撮影が完了したかどうかを get_status() の buffer で確認する。\
画像の取得は明示的に acquire_images() を呼び出す必要がある。\
PCからカメラの設定変更などを行うには shoot_from_camera(False) でカメラの操作権をPCに戻す必要がある。\
カメラのモデルによってはこの関数による明示的な操作権の切り替えが不要な場合がある。

### acquire_images()
```
acquire_images()
acquire_images(folder="yourfolder")
acquire_images(max_image_count={image_count}, max_wait_seconds={wait_sec})

response:APIResponseDict
	.success
	.error_message
	.data = {
		"datasize": 保存したバイト数の合計
		"objects": [
			{ "folder":フォルダ名, "filename":ファイル名, "datasize":バイト数, "object":[...] },
			...
		]
	}
```
max_wait_seconds で指定した秒数の間、カメラのバッファに次の画像が入るのを待って取得する。\
指定した秒数の間に画像が入らなければタイムアウトして終了する。デフォルトは 5秒。\
max_image_count で指定した枚数を上限として、カメラのバッファに入った画像を取得する。\
指定秒数もしくは指定枚数のいずれかに達した時点で終了する。デフォルトは 100枚。\
継続的に撮影する場合は、acquire_images() を繰り返し呼び出すことで画像取得と中止に分岐できる。\
acquire_images() が画像を取得する毎にカメラのバッファが解放されるため、バッファがフルになるまで、カメラ側では撮影を継続できる。\
レスポンスは capture_multi_images() と同じ形式で返される。

## Exposure settings and options
### get_program_mode_options()
```
get_program_mode_options()

response:APIResponseList
	.success 	   # True/False
	.error_message # エラーに関する情報の文字列
	.options = []  # AEモードの選択肢（リスト内の値のみ set/getできる）
```
選択可能なAEプログラムモード一覧の取得\
（マニュアル、プログラムオート、絞り優先オート、シャッター優先オート）\
SDKの定義値はヘルパー関数で文字列表現に変換できる。
```python
from fujixcam import sdk_value_to_string, string_to_sdk_value
sdk_value_to_string('program_mode',0x01)	# -> 'M'
string_to_sdk_value('program_mode','M')		# -> 1
```

### get_program_mode()
```
get_program_mode()

response:APIResponseValue
	.success
	.error_message
	.value	現在のAEモード値
```

### set_program_mode()
```
set_program_mode( value )

response:APIResponse
	.success
	.error_message
```
- value\
	AEプログラムモードを設定する。\
	選択可能な値は get_program_mode_options() で取得できる。

### get_exposure_compensation_options()
```
get_exposure_compensation_options()

response:APIResponseList
	.success
	.error_message
	.options = [...]	露出補正値の選択肢（リスト内の値のみ set/getできる）
```
選択可能な露出補正値の一覧の取得（自動露出モードのときのみ有効）
SDKの定義値はヘルパー関数で文字列表現に変換できる。
```python
from fujixcam import sdk_value_to_string, string_to_sdk_value
sdk_value_to_string('exposure_compensation',10)  # ->'+0.33EV'
string_to_sdk_value('exposure_compensation','+0.33EV')  # ->10
```

### get_exposure_compensation()
```
get_exposure_compensation()

response:APIResponseValue
	.success
	.error_message
	.value	現在の露出補正値
```

### set_exposure_compensation()
```
set_exposure_compensation( value )
	.success
	.error_message
```
- value\
	露出補正値を設定する。\
	選択可能な値は get_exposure_compensation_options() で取得できる。

### get_shutter_speed_options()
```
get_shutter_speed_options()

response:APIResponseList
	.success
	.error_message
	.options = [...]	シャッター速度の選択肢（リスト内の値のみ set/getできる）
```
選択可能なシャッター速度の一覧の取得（マニュアル露出モード or シャッター優先オートのときのみ有効）
SDKの定義値はヘルパー関数で文字列表現に変換できる。
```python
from fujixcam import sdk_value_to_string, string_to_sdk_value
sdk_value_to_string('shutter_speed',15625)  # -> '1/60'
string_to_sdk_value('shutter_speed','1/60')  # -> 15625
```

### get_shutter_speed()
```
get_shutter_speed()

response:APIResponseValue
	.success
	.error_message
	.value	現在のシャッター速度値
```

### set_shutter_speed()
```
set_shutter_speed( value )

response:APIResponse
	.success
	.error_message
```
- value\
	シャッター速度を設定する。\
	選択可能な値は get_shutter_speed_options() で取得できる。

### get_aperture_value_options()
```
get_aperture_value_options()

response:APIResponseList
	.success
	.error_message
	.options = [...]	絞り値の選択肢（リスト内の値のみ set/getできる）
```
選択可能な絞り値の一覧の取得（マニュアル露出モード or 絞り優先オートのときのみ有効）

### get_aperture_value()
```
get_aperture_value()

response:APIResponseValue
	.success
	.error_message
	.value	現在の絞り値
```

### set_aperture_value()
```
set_aperture_value( value)

response:APIResponse
	.success
	.error_message
```
- value\
	絞り値を設定する。\
	選択可能な値は get_aperture_value_options() で取得できる。

### get_iso_sensitivity_options()
```
get_iso_sensitivity_options()

response:APIResponseList
	.success
	.error_message
	.options = [...]	ISO感度の選択肢（リスト内の値のみ set/getできる）
```
選択可能なISO感度設定の一覧の取得
 
### get_iso_sensitivity()
```
get_iso_sensitivity()

return:APIResponseValue
	.success
	.error_message
	.value	現在のISO感度設定値
```

### set_iso_sensitivity()
```
set_iso_sensitivity( value)

response:APIResponse
	.success
	.error_message
```
- value\
	ISO感度を設定する。\
	選択可能な値は get_iso_sensitivity_options() で取得できる。

## Focus settings and options
### get_focus_mode_options()
```
get_focus_mode_options()

response:APIResponseList
	.success
	.error_message
	.options = [...]	フォーカスモードの選択肢（リスト内の値のみ set/getできる）
```
選択可能なフォーカスモード一覧の取得（マニュアルフォーカス、シングルAF、コンティニュアスAF）\
SDKの定義値はヘルパー関数で文字列表現に変換できる。
```python
from fujixcam import sdk_value_to_string, string_to_sdk_value
sdk_value_to_string('focus_mode',0x01)	 # -> 'MF'
string_to_sdk_value('focus_mode','MF')	 # -> 1
```

### get_focus_mode()
```
get_focus_mode()

response:APIResponseValue
	.success
	.error_message
	.value	現在のフォーカスモード値
```

### set_focus_mode()
```
set_focus_mode( value )
set_focus_mode( value, pre_af=False )

response:APIResponse
	.success
	.error_message
```
フォーカスモードを設定する。
- value\
	フォーカスモードを設定する。\
	選択可能な値は get_focus_mode_options() で取得できる。
- pre_af\
	フォーカスモードがAFのときに、常時オートフォーカス（PreAF）を有効にするかを指定する。\
	PreAFが動作しているかどうかは get_status() の pre_af で確認できる。

### get_focus_area_options()
```
get_focus_area_options()
get_focus_area_options( cap_inspection=True )

response:APIResponseDict
	.success
	.error_message
	.data = {
		"h": [...]	  # 水平方向のポジション値のリスト（リスト内の値のみ set/getできる）
		"v": [...]	  # 垂直方向のポジション値のリスト（リスト内の値のみ set/getできる）
		"size": [...] # フォーカスエリアサイズの選択肢（リスト内の値のみ set/getできる）
		"points": (水平方向の最大ポジション数, 垂直方向の最大ポジション数)
	}
```
- cap_inspection\
	条件に応じたCapabilityを返す機能がない旧機種の場合はフォーカスエリアの全域（最大ポジション数）をリスト化して返すことで代替しているが、ここでTrue指定すると実際に設定可能か検査を行って結果を返す。\
	動作に時間がかかるため推奨しない。デフォルトは False。

サイズ選択肢のSDK定義値はヘルパー関数で文字列表現に変換できる。
```python
from fujixcam import sdk_value_to_string, string_to_sdk_value
sdk_value_to_string('focus_size',0x01)		# -> 'Smaller'
string_to_sdk_value('focus_size','Smaller') # -> 1
```

### get_focus_area()
```
get_focus_area()

response:APIResponseDict
	.success
	.error_message
	.data = {
		"h": 水平方向のポジション値
		"v": 垂直方向のポジション値
		"size": フォーカスエリアサイズのSDK定義値
	}
```

### set_focus_area()
```
set_focus_area( h, v )
set_focus_area( h, v, size )

response:APIResponse
	.success
	.error_message
```
- h, v\
	フォーカスエリアの水平方向、垂直方向のポジション値を設定する。\
	選択可能な値は get_focus_area_options() で取得できる。
- size\
	フォーカスエリアのサイズを設定する。\
	選択可能な値は get_focus_area_options() で取得できる。\
	ポジションとサイズの組み合わせが不正な場合はエラーとなる。\
	（サイズを大きくすると設定可能なポジションの範囲が狭くなることに注意）

### get_focus_distance_range()
```
get_focus_distance_range()

response:APIResponseDict
	.success
	.error_message
	.data = {
		"mod": 最短フォーカス距離のSDK定義値
		"inf": 無限遠フォーカス距離のSDK定義値
		"dof": 被写界深度のSDK定義値
		"step": フォーカス距離のステップ値のSDK定義値
	}
```
マニュアルフォーカスで指定できる距離値の範囲を返す。\
SDKが定義する距離値の数字は inf が小さく mod が大きい。例）inf:22, mod:1400 \
距離値を増減させるときの刻み幅は、step値 か dof値を参考にする。\
レンズによって距離値の範囲が変わるため、レンズ交換式カメラでは実際に装着しているレンズで取得する必要がある。

### get_focus_distance()
```
get_focus_distance()

response:APIResponseValue
	.success
	.error_message
	.value	現在のフォーカス距離のSDK定義値
```
マニュアルフォーカスでの距離値が返る。\
但し、マニュアルフォーカスモードではレンズのフォーカスリングを回すことでも距離値が変化するため、最後に set_focus_distance() で設定した値が返るとは限らない。


### set_focus_distance()
```
set_focus_distance( value )

response:APIResponse
	.success
	.error_message
```
マニュアルフォーカスでの距離値を設定できる。\
但し、レンズのフォーカスリングを直接手で回すことでも距離値が変化することに注意する。
- value\
	フォーカス距離を設定する。\
	選択可能な値は get_focus_distance_range() で取得できる。\
	マニュアルフォーカスモードのときのみ有効で、AFモードのときはエラーとなる。

### get_focus_afmode_options()
```
get_focus_afmode_options()

response:APIResponseList
	.success
	.error_message
	.options = [...]	AFモードの選択肢（リスト内の値のみ set/getできる）
```
選択可能なAFモードの一覧の取得。\
オートフォーカス（AF-C, AF-S）のときのみ有効である。\
AFモードが　"SINGLE", "ZONE" ではそれぞれ選択可能なAFエリアの大きさとポジションが異なる。

### get_focus_afmode()
```
get_focus_afmode()

response:APIResponseValue
	.success
	.error_message
	.value	現在のAFモードのSDK定義値
```
現在のAFモードを取得する。\
マニュアルフォーカスのモード時は、インスタントAFを行うときのAFエリアである”SINGLE"モードが返る。

### set_focus_afmode()
```
set_focus_afmode( value )

response:APIResponse
	.success
	.error_message
```
- value\
	AFモードを設定する。\
	選択可能な値は get_focus_afmode_options() で取得できる。

AFモードが "SINGLE", "ZONE" ではそれぞれ選択可能なAFエリアの大きさとポジションの範囲が異なる。\
AFモードを "WIDETRACKING" ではAFエリアの大きさとポジションは選べない。\
したがって、AFモードを切替えた場合、AFエリアの大きさとポジションの範囲も取得し直す必要がある。

## Image quality settings and options
### get_image_quality_options()
```
get_image_quality_options()

response:APIResponseList
	.success
	.error_message
	.options = [...]	画質モードの選択肢（リスト内の値のみ set/getできる）
```
選択可能な画質モードの一覧の取得（RAW/JPEG/RAW+JPEG）\
このモードによって capture_image(), capture_multi_images(), bulb_off() で保存される画像ファイルの種類とサイズが変わる。\
SDKの定義値はヘルパー関数で文字列表現に変換できる。
```python
from fujixcam import sdk_value_to_string, string_to_sdk_value
sdk_value_to_string('image_quality',0x04)	# -> 'RAW+FINE'
string_to_sdk_value('image_quality','RAW+FINE') # -> 4
```

### get_image_quality()
```
get_image_quality()

response:APIResponseValue
	.success
	.error_message
	.value	現在の画質モードのSDK定義値
```
画質モードを取得する。

### set_image_quality()
```
set_image_quality( value )

response:APIResponse
	.success
	.error_message
```
- value\
	画質モードを設定する。\
	選択可能な値は get_image_quality_options() で取得できる。

#### get_image_size_options()
```
get_image_size_options()

response:APIResponseList
	.success
	.error_message
	.options = [...]	画像サイズの選択肢（リスト内の値のみ set/getできる）
```
選択可能な画像サイズの一覧の取得 (L 3:2 / M 16:9 / ... )\
このモードによって capture_image(), capture_multi_images(), bulb_off() で保存される画像ファイルの画素数が変わる。\
サイズとアスペクト比の組み合わせたモード値になっており、SDKの定義値はヘルパー関数で文字列表現に変換できる。\
モードによって撮影画像の画素数のサイズが変わるが、具体的な画素数はカメラの機種（センサー）によって異なるため、SDKでは定義されていない。

```python
from fujixcam import sdk_value_to_string, string_to_sdk_value
sdk_value_to_string('image_size',0x07)	# -> 'L_3:2'
string_to_sdk_value('image_size','L_3:2') # -> 7
```

### get_image_size()
```
get_image_size()

response:APIResponseValue
	.success
	.error_message
	.value	現在の画像サイズのSDK定義値
```

### set_image_size()
```
set_image_size( value )

response:APIResponse
	.success
	.error_message
```
- value\
	画像サイズ（アスペクト比を組み合わせたモード値）を指定する。\
	選択可能な値は get_image_size_options() で取得できる。

## Liveview acquisition
### get_liveview_quality_options()
```
get_liveview_quality_options()

response:APIResponseList
	.success
	.error_message
	.options = [...]	ライブビュー画質の選択肢（リスト内の値のみ set/getできる）
```
設定可能なライブビュー画質モードの一覧の取得（FINE/NOMAL/BASIC）\
このモードによって get_liveview_image() で取得できるライブビュー画像の画質（JPEGの圧縮率）が変わる。\
SDKの定義値はヘルパー関数で文字列表現に変換できる。
```python
from fujixcam import sdk_value_to_string, string_to_sdk_value
sdk_value_to_string('liveview_quality',0x01)	# -> 'FINE'
string_to_sdk_value('liveview_quality','FINE')  # -> 1
```

### get_liveview_quality()
```
get_liveview_quality()

response:APIResponseValue
	.success
	.error_message
	.value	現在のライブビュー画質のSDK定義値
```

### set_liveview_quality()
```
set_liveview_quality( value )

response:APIResponse
	.success
	.error_message
```
liveview動作中は変更することができない。\
start_liveview() でライブビューを開始する前に設定する必要がある。

- value\
	ライブビュー画質モードを設定する。\
	選択可能な値は get_liveview_quality_options() で取得できる。

### get_liveview_size_options()
```
get_liveview_size_options()

response:APIResponseList
	.success
	.error_message
	.options = [...]	ライブビューサイズの選択肢（リスト内の値のみ set/getできる）
```
選択可能なライブビューサイズの一覧の取得（L/M/Sモード）\
このモードによって get_liveview_image() で取得できるライブビュー画像の画素数が変わる。\
画素数の目安として LモードはXGA、MモードはSVGA、SモードはVGA 程度の画素数になる。\
SDKの定義値はヘルパー関数で文字列表現に変換できる。
```python
from fujixcam import sdk_value_to_string, string_to_sdk_value
sdk_value_to_string('liveview_size',0x01)	# -> 'L'
string_to_sdk_value('liveview_size','L')	# -> 1
```

### get_liveview_size()
```
get_liveview_size()

response:APIResponseValue
	.success
	.error_message
	.value	現在のライブビューサイズのSDK定義値
```

### set_liveview_size()
```
set_liveview_size( value )

response:APIResponse
	.success
	.error_message
```
liveview動作中は変更することができない。\
start_liveview() でライブビューを開始する前に設定する必要がある。
- value\
	ライブビューサイズモードを設定する。\
	選択可能な値は get_liveview_size_options() で取得できる。

### get_finder_crop_options()
```
get_finder_crop_options()

response:APIResponseList
	.success
	.error_message
	.options = [...]	ファインダークロップの選択肢（リスト内の値のみ set/getできる）
```
ファインダーのライブビュー画像の一部を拡大して表示し、フォーカス確認をしやすくする機能をデジタルズームとして利用できる。\
クロップ倍率の選択肢を取得する。\
フォーカスポイントを中心にクロップされるため、フォーカスポイントの位置を変更することでズーム窓を移動することができる。\
この機能はシングルスポットAF、もしくはマニュアルフォーカスのときのみ有効で、中心が変化する ZONE や WIDE では等倍のみとなる。\
SDKの定義値はヘルパー関数で文字列表現に変換できる。

```python
from fujixcam import sdk_value_to_string, string_to_sdk_value
sdk_value_to_string('finder_crop',0x03)	  # -> 'x6.0'
string_to_sdk_value('finder_crop','x6.0') # -> 3
```

### get_finder_crop()
```
get_finder_crop()

response:APIResponseValue
	.success
	.error_message
	.value	現在のファインダークロップのSDK定義値
```

### set_finder_crop()
```
set_finder_crop( value )

response:APIResponse
	.success
	.error_message
```
- value\
	ファインダークロップ倍率を設定する。\
	選択可能な値は get_finder_crop_options() で取得できる。
liveview動作中は変更することができない。\
start_liveview() でライブビューを開始する前に設定する。

### start_liveview()
```
start_liveview()

response:APIResponse
	.success
	.error_message
```
カメラのバッファからライブビュー画像を連続転送するモードに入る。\
このモードに入ると、get_liveview_image() で最新のライブビュー画像を連続的に取得できるようになる。\
ただしライブビュー動作中は、ライブビュー画像の取得ほか一部の機能のみが実行可能で、通常の撮影操作はできない。\
ライブビュー動作中かどうかは get_status() の liveview で確認でき、stop_liveview() で停止する。
```
ライブビュー中に使用できるメソッド:
	get_liveview_image(), stop_liveview(),
	get_focus_area(), set_focus_area()
	is_connected(),	get_status(), reset_status()
```

### stop_liveview()
```
stop_liveview()

response:APIResponse
	.success
	.error_message
```
ライブビューを停止する。\
ライブビュー動作中は、ライブビュー画像の取得ほか一部の機能のみが実行可能で、通常の撮影操作はできないため、設定変更や撮影操作を行う場合は一旦ライブビューを停止してから行い、再度ライブビューを開始する必要がある。

### get_liveview_image()
```
get_liveview_image()

response:APIResponseDict
	.success
	.error_message
	.data = {
		"buffer": bytearrayに変換されたJPEGデータ
		"bytes": バイナリでのデータバイト数
	}
```
最新のライブビュー画像をバッファで取得する。\
start_liveview() でライブビューを開始しているときのみ有効で、ライブビュー動作中は通常の撮影操作はできない。\
取得される画像の画質やサイズはライブビュー開始前に set_liveview_quality(), set_liveview_size() で設定した値による。

## Other operations

### get_lens_zoom_capability()
```
get_lens_zoom_capability()

response:APIResponseDict
	.success
	.error_message
	.data = {
		"ability": 0,  # ズーム能力のSDK定義値
		"options": [...]		選択可能なズーム位置の一覧
		"actual_length": [...]	実際の焦点距離の一覧（mm値x100）
		"equiv35_length": [...]	35mm換算焦点距離の一覧（mm値x100）
	}
```
単焦点レンズの場合、ズーム能力は 0 となり、選択可能なズーム位置は 1 つのみとなる。\
手動ズームレンズの場合も、ズーム能力は 0 だが、ズーム範囲の情報は取得できる。\
optionsとactual_lengthおよびequiv35_lengthの対応関係はインデックスで一致している。

### get_lens_zoom()
```
get_lens_zoom()

response:APIResponseValue
	.success
	.error_message
	.value	現在のズーム位置  get_lens_zoom_capability() で取得できる選択可能なズーム位置のいずれか
```
ユーザーが操作してズーム位置を変更した場合、get_lens_zoom() で取得できる現在のズーム位置は変化する。\
レンズのタイプによっては、ズーム位置で絞り値が変化したり、絞り値の設定範囲が変化することがある。

### set_lens_zoom()
```
set_lens_zoom( value )

response:APIResponse
	.success
	.error_message
```
電動かつホストから制御可能なレンズに対してズーム位置を設定できる。\
選択可能な値は get_lens_zoom_capability() で取得できる。

---
**end of document**