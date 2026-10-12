**Camera GUIDE**
---
# Get started
1. パッケージの入手

```bash
# Install from PyPI
pip install fujixcam
``` 

2. カメラメーカーのSDKを入手

https://www.fujifilm-x.com/special/camera-control-sdk \
カメラメーカーのWebサイトから規約に従ってSDKを入手しPC（Windows/Mac）の任意のフォルダに解凍する。\
展開したフォルダの REDISTRIBUTION フォルダの下位階層で xapi.dat ファイルのあるフォルダのパス名を確認しておく（この後で必要になります）。

3. python で Camera オブジェクトを生成する

```python
import fujixcam
camera = fujixcam.Camera()
# Exception:
#	RuntimeError("Failed to load FUJIFILM SDK library.")
#	RuntimeError("Multiple instances are not supported.")
```

4. クリックラップ

初回のインスタンス生成時にカメラSDKの場所を聞いてくるので、上記2.で確認したフォルダのパスを入力する。\
カメラSDKのEULAに同意済みかを確認するダイアログが表示されるので、同意して「y」を入力する。\
クリックラップは初回のみで、次回以降は自動的にSDKがロードされる。\
このステップは下位レイヤーの CameraAPI が行っている。（既にCameraAPIを使用済みならここはスキップされる。）
```python
camera = fujixcam.Camera()
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
指定した場所からSDKがロードできない場合は、"Checking FUJIFILM_CAMERA_CONTROLL_SDK module in: ..." の後に再度パスを聞いてくるので正しいパスを入力する。\
指定したフォルダのパスが正しければ、SDKがロードされ、Cameraオブジェクトが生成される。

5. カメラとのセッション開始・終了

Camera オブジェクトを生成すると自動的にカメラを探して接続しにいく。\
カメラが見つかるまでループするため、あらかじめカメラの電源を入れてテザーモードでUSB/Wifi接続しておくか、この時点で接続するとセッションが開始して次に進む。\
Camera オブジェクトが破棄されるとセッションも終了する。

```python
import fujixcam
camera = fujixcam.Camera()  # session open
camera.is_connected()	# -> True if connected, False otherwise
#result = camera.{method_name}
camera.close()  # session close
del camera
```
あるいは
```python
from fujixcam import Camera
with Camera() as camera:
	# session open
	camera.is_connected()	# -> True if connected, False otherwise
	#result = camera.{method_name}
	# automatically closed at the end of the with block
```
Note:
接続時のカメラの設定状態がセッションに引き継がれるため、メソッドでサポートしていない設定は必要に応じて事前にカメラ本体の操作で設定しておく。\
また、一定時間操作を行わないとカメラがスリープして接続が切れてしまうためカメラの電源設定はオートパワーOFFなしを推奨する。\
スリープで接続が切れた場合はカメラの復帰後に reconnect で再接続できるが最初に接続したときの状態には戻らない。\
明示的なcloseはセッション開始時の設定に戻して終了させる効果があり（ベストエフォート）、withブロックの終了時には自動的にcloseが呼ばれる。\
強制終了した場合は接続を終了する直前の状態がカメラに残る。


6. メソッドとレスポンス

セッションが開始したら、Camera オブジェクトのメソッドを呼び出すことでカメラを操作できる。\
セッション中は、カメラの制御はPCからの指示によって行われるため、シャッターボタンを含むカメラ本体の操作は一部を除いて無効になる。\
セッション中も操作できるのは、マニュアルレンズのズームリング操作、マニュアルフォーカスモード時のフォーカスリング操作などである。\
接続したときのカメラの設定値を引き継いで１枚撮影して画像保存する最小限のコードサンプルは以下のようになる。
```python
from fujixcam import Camera
camera = Camera()
result = camera.capture()
if result.success:
    print(f"Saved as {result.image_files}")
else:
    print("Error : ", result.error_message)
```
カメラの記録設定がRAW+JPEGの場合、一度の撮影で2つのファイルが保存される。\
形式を合わせるために image_filesはリストになっていて、JPEGのみの設定でも要素数１のリストで返される。

---

# Interface overview

method と result の具体的な仕様は以下の通り。

## Camera object
カメラオブジェクトの生成によってカメラとのセッションが開始される。\

```python
camera = Camera()
camera = Camera( wait_for_connection={True|False}, log_level={mode} )

camera   # -> <Camera(device=FUJIFILM X-S10/XF35mmF2 R WR, status=connected)>
camera.product_name	 # -> "FUJIFILM X-S10/XF35mmF2 R WR"
```
デフォルトではUSB接続でカメラが見つかるまで待ち、最初に見つかったカメラに接続する。\
現在のバージョンではUSB接続のカメラのみを対象とし、同時に生成できるインスタンスは１つのみである。
- wait_for_connection\
    True の場合はカメラが見つかるまで待つ。(default)\
    False の場合はカメラが見つからなければすぐ結果を返す。\
- log_level\
    コンソールへのログ出力のモードを指定する。\
    "none"  出力しない。\
    "error"  エラーのみ出力する。\
	"warning"  エラーと警告メッセージを出力する。（デフォルト設定）\
    "info"   エラーと警告と途中情報を出力する。

## Result object
method に応じた dataclass が返る。

### カメラの状態を返すメソッド -> ResultStatus
```python
from fujixcam import ResultStatus
from fujixcam import CameraStatus
result: ResultStatus = camera.get_status()
#	- result.success : bool
#	- result.error_message : str
#	- result.camera_status : CameraStatus   # カメラの現在の状態を表すDataClass
#		.is_ready : bool 		# 撮影可能状態かどうか
#		.buffer_count : int		# 連写可能な撮影バッファ数
#    	.conditions : list[str] # 内部状態を表す文字列のリスト
```
conditions に含まれる文字列の意味は以下の通りである。
- "liveviewing" : ライブビューの稼働状態
- "focusing" : Continuous-AFのオートフォーカス動作中 or PreAF動作中
- "shooting" : 長時間露光中あるいは撮影後の画像処理・画像保存のシーケンス実行中
- "bulb_capturing" : Bulb撮影のシーケンス実行中
- "af_locked" : AFロック中
- "ae_locked" : AEロック中

### 現在の設定値と設定可能なオプション情報の一式を返す -> ResultConfig
```python
from fujixcam import ResultConfig
from fujixcam import ExposureSettings, FocusSettings, ImageSettings, ExposureOptions, FocusOptions, ImageOptions
result: ResultConfig = camera.get_config()
#	- result.success : bool
#   - result.error_message : str
#	- result.settings = {
#        "exposure": ExposureSettings,   # 露出制御に関する設定値のDataClass
#        "focus": FocusSettings,         # フォーカス制御に関する設定値のDataClass
#        "image": ImageSettings,         # 画像データに関する設定値のDataClass
#      }
#    - result.options = {
#        "exposure": ExposureOptions,    # 露出制御に関する設定可能なオプションのDataClass
#        "focus": FocusOptions,          # フォーカス制御に関する設定可能なオプションのDataClass
#        "image": ImageOptions,          # 画像データに関する設定可能なオプションのDataClass
#      }
```

### 撮影保存した結果を返す -> ResultFiles
```python
from fujixcam import ResultFiles
result: ResultFiles = camera.capture()
#	- result.success : bool
#	- result.error_message : str
#	- result.folder : str				# 保存先のフォルダ
#	- result.image_files : list[str]	# [ file1, file2, ... ]  保存したファイルのリスト
#	- result.total_bytes : int			# 保存したファイルの合計バイト数
```

### 画像データのバッファを返す -> ResultImage
```python
from fujixcam import ResultImage
result = camera.get_liveview_image()
#	- result.success : bool
#	- result.error_message : str
#	- result.image_data : bytearray	# 画像データ（通常はJPEGデータ）
#	- result.image_note : Dict		# 画像データの付帯情報（通常はNone）
```

---
## Method list
### session and status management
|method|description|
|---|---|
|is_connected() |	接続されているかを確認する。|
|reconnect()	|	カメラに再接続して状態遷移を初期状態にリセットする。|
|get_status() |	カメラの状態パラメータを返す。|
|close() |	カメラとの接続を終了する。|

### Shooting operations
|method|description|
|---|---|
|capture()|撮影して画像ファイルを保存する。|
|preview()|試し撮りで小さいJPEG画像をバッファで取得する。|
|bulb_capture()|バルブ撮影して画像ファイルを保存する。|
|focus_on()|フォーカスエリアを移動しAF動作（半押し相当）を実行する。|
|focus_off()|AFロックを解除あるいはコンティニュアスAF動作を停止する。|

### Camera settings and options
|method|description|
|---|---|
|get_config()	|現在の設定パラメータと設定可能なオプション情報の一式を返す。|
|setup()	|露出・フォーカス・画質のパラメータを設定する。|

### Liveview operations
|method|description|
|---|---|
|get_liveview_config()|選択可能なライブビュー画質オプションを返す。|
|start_liveview()|ライブビューを開始する。|
|stop_liveview()|ライブビューを停止する。|
|get_liveview_image()|最新のライブビュー画像をバッファで取得する。|

### Other operations
|method|description|
|---|---|
Not implemented yet.

---

# Interface details
## session and status management 
### is_connected()
カメラが接続されているかを確認する。
```
is_connected()

result: bool = {True|False}
```
接続されている場合は True を返す。接続されていない場合は False を返す。\
このメソッドは bool を直接返す。\
camera = Camera( wait_for_connection=False ) で接続できなかった場合や、接続後にカメラの電源OFFなどの理由で接続が途中で切れた場合は、camera.is_connected() が False になる。

### reconnect()
カメラを接続し直して状態遷移を初期状態にリセットする。
```
reconnect()
reconnect(wait_for_connection={True|False})

result:bool = {True|False}
```
カメラを接続し直して状態遷移を初期状態にリセットする。\
カメラの状態遷移をリセットしたい場合や、カメラの電源OFF/ONなどから接続を復帰したい場合に使用する。\
Camera( wait_for_connection=False ) で接続できなかった場合もこのメソッドを使用して再接続を試みる。\
このメソッドは bool を直接返す。
- wait_for_connection\
	True の場合はカメラが見つかるまで待つ。(default)\
	False の場合はカメラが見つからなければすぐ結果を返す。

### get_status()
```
get_status()

result: ResultStatus
	.success = False	# カメラの状態が確認できない場合
	.error_message = エラーメッセージ
    .condition = None 

result: ResultStatus
    .success = True 	# connected状態の確認に成功した場合
    .error_message = ""
	.is_ready = True/False	# 撮影可能状態かどうか
	.buffer_count		# 連写可能な撮影バッファ数
    .conditions = [...]	# カメラの状態を表す文字列のリスト
```
カメラの状態パラメータを返す。\
いずれかの状態がTrueのときは状態が解除されるまで、使用できるmethodが限られている。

### close()
```
close()
close( shutdown={True|False} )
```
カメラと接続したときの各種設定値に戻して接続を終了する。

shutdown が True の場合は、カメラは接続を終了した後に電源OFF になる。\
カメラの電源をOFFすると、再度電源ONするまで reconnect() で再接続はできない。\
明示的な close() をせずカメラオブジェクトが破棄された場合は設定値の復帰は行われない。 \
但し、with 文を使ってカメラオブジェクトを管理する場合は、ブロックを抜けると自動的に close() が呼ばれる。

## Shooting operations
### capture()
```python
capture()
capture( folder={your_folder} )
capture( folder={your_folder}, filename={filename} )
capture( folder={your_folder}, count={number_of_shots} )

result: ResultObjects
	.success
	.error_message
	.folder : str		# 保存先のフォルダ名
	.total_bytes : int		# 保存された画像ファイルの合計バイト数
	.image_files = [	# 保存された画像ファイル名のリスト(RAW/JPEG問わず同じリストに含む)
		"sample1.raf",
		"sample1.jpg",
		:
	]
```
撮影して指定したフォルダに自動的に新しいファイル名で保存する。\
ファイル名は yyyy_mmdd_hhmmssss.jpg の形式で保存される。
- folder\
	保存先のフォルダ名を指定する。\
	フォルダを指定しない場合あるいは指定したフォルダがない場合はカレントフォルダに保存される。\
	デフォルトでは日付時刻を用いて重複しない自動ファイル名で保存する。
- filename\
	保存するファイル名を指定したい場合に使用する。\
	撮影モードによってRAW/JPEG/RAW+JPEGがありえるため、拡張子を除いたファイル名のみを指定すること。\
	指定したファイル名がすでに存在する場合は上書きする。\
    count を指定した場合は自動ファイル名になり filename は使えない。
- count\
    指定枚数をベストエフォートで連続撮影する。\
	カメラのバッファに溜めてからまとめて保存することで撮影間隔を短くするもので、カメラ本体の連写機能とは異なる。\
    枚数のデフォルトは5枚、指定できる最大枚数は get_status()で得られるバッファ数まで。\
	フォーカスロックして電子シャッターを使う等の組み合わせで高速な連写が可能。\
	AF-Sモードで連続撮影する場合は、撮影前にオートフォーカスを実行してフォーカスをロックする。\
	既にAFロックした状態で呼び出した場合は、ロックしたフォーカスが維持される。

### preview()
```
preview()

result:ResultImage
	.success
	.error_message
	.image_data : bytearray # JPEGデータ
	.image_note : dict  	# 画像データの付帯情報（通常はNone）
```
1枚テスト撮影して小さいプレビュー画像のみをバッファで受け取る。\
10秒以上の長時間露光はできない。

### bulb_capture()
```python
bulb_capture()
bulb_capture( folder={your_folder} )
bulb_capture( exposure_time=20.0 )
bulb_capture( exposure_time=20.0, callback={your_function} )
bulb_capture( exposure_time=20.0, aperture="F2.8", iso_sensitivity="ISO 800" )

result:ResultFiles
	.success
	.error_message
	.folder : str		# 保存先のフォルダ名
	.total_bytes : int	# 保存したバイト数の合計
	.image_files = [	# 保存された画像ファイル名のリスト(RAW/JPEG問わず同じリストに含む)
		"sample1.raf",
		"sample1.jpg",
	]
```
自動的にマニュアル露出モードかつシャッター速度"Bulb"に切り替えてバルブ撮影を行う。\
バルブ撮影中は get_status() の condition に "bulb_capturing" が返る。\
撮影時間は露出時間を指定するか、コールバック関数で終了の仕方を返すことで制御する。

- folder\
	capture() と同じ。

- exposure_time\
	バルブ撮影の露出時間を秒単位で指定する。\
	指定した時間が経過すると自動的にシャッターが閉じられて撮影が終了する。\
	指定時間が経過するまでバルブ撮影の中止はできないが、callback を指定することで、任意のタイミングで撮影を終了することができる。

- callback\
	バルブ撮影中に呼び出されるコールバック関数を指定できる。\
	約0.5秒ごとにコールバック関数が呼び出され、戻り値として以下のいずれかを返すことで撮影の継続・終了を制御できる。
	```
	def your_function(elapsed_time: float, exposure_time: float):
	    # 撮影の継続・終了を制御する処理をここに記述する
		# elapsed_time: 経過時間（秒）
		# exposure_time: 指定された露出時間（秒）
	    return "continue"  # "finish" または "abort" を返すことも可能
	```
	- return "finish"\
		バルブ撮影を終了して撮影画像を保存する。\
		露光を終了してシャッターを閉じても、カメラ内での画像処理を行う時間があるため、ここで returnしてから bulb_capture() を抜けるまでに時間がかかる場合がある。

	- return "abort"\
		バルブ撮影を中止する。（ファイルは保存されない）
		露光を中止しても、カメラの内部処理があるため、ここで return してから bulb_capture() を抜けるまでに時間がかかる場合がある。

	- return "continue" (デフォルト)\
		バルブ撮影を継続する。\
		再びコールバック関数が呼び出される。

- aperture\
	バルブ撮影時の絞り値を指定する。例: "F2.8"\
	省略した場合は自動的に最も深い絞り値の1段前の値が使用される。例: "F14"

- iso_sensitivity\
	バルブ撮影時のISO感度を指定する。例: "ISO 400"\
	省略した場合は自動的に最も低いISO感度が使用される。例: "ISO 80"

### focus_on()
```python
focus_on( x, y )
focus_on( x, y, af_on={True|False}, hold_on={True|False} )

result:ResultStatus
	.success
	.error_message
	.is_ready = True|False	# 撮影可能状態かどうか
	.conditions = [...]		# カメラの状態を表す文字列のリスト
	:
```
シングルポイントAFのフォーカス点を移動し、指定したAF動作を実行する。\
フォーカスモードが MF, AF-S, AF-C　いずれの場合であってもオートフォーカスを実行できるがモードによって挙動が異なる。\
ライブビューでズーム中にフォーカス点を移動すると、ズームの中心を移動できる。
- x, y
	x:水平方向、y:垂直方向にフォーカス点を移動する。\
	フォーカス点の位置はスクリーン中央を原点とし、左/下がマイナス、右/上がプラスである。\
	指定可能な値域は get_config() の options で知ることができる。\
	但し、値域内であっても、フォーカスエリアのsizeが大きい場合は上下左右端まで移動できないことがある。
- af_on
	True を指定すると、フォーカスエリアを変更後にオートフォーカスを実行する。\
	デフォルトは False（フォーカスエリアの変更のみ行いAF動作はしない）。\
	MF/AF-S/AF-CモードのいずれであってもAF動作をさせることができる。\
	AF動作後の状態は hold_on オプションの指定によりモードごとに異なる。
	- MFの場合：　シングルポイントAFを実行してフォーカス距離を変更する。
	- AF-Sの場合：　現在のAF設定に従ってAFを1回だけ実行する。
	- AF-Cの場合：　現在のAF設定に従ってContinuous-AFを開始する。（停止指示をするまでContinuous-AFの動作を続ける）\
- hold_on
	af_on が True の場合に使用するオプション。\
	Trueを指定すると以下のようになる。デフォルトは False。
	- MF の場合：　効果なし。
	- AF-Sの場合：　AF動作後にフォーカスをロックする。
	- AF-Cの場合：　このフラグに関係なく Continuous-AF動作は継続する。\
	フォーカスロックやコンティニュアスAF動作の解除は focus_off() を使う。\
	フォーカスロック中やコンティニュアスAF動作中は focus_on() で設定を変えることはできない。
	
### focus_off()
```python
focus_off()

result:ResultStatus
	.success
	.error_message
	.is_ready = True|False	# 撮影可能状態かどうか
	.conditions = [...]		# カメラの状態を表す文字列のリスト
```
focus_on() でフォーカスロックした場合や、コンティニュアスAF動作中の場合に、フォーカスロックを解除あるいはコンティニュアスAF動作を停止する。

## Camera settings and options
### get_config()
カメラの撮影機能に関する設定値の一式、および設定可能なオプション情報の一式を返す。\
```python
get_config()

result: ResultSettings
	.success
	.error_message
	.settings = {
		"exposure": ExposureSettings,   # 露出制御に関する設定値のDataClass
		"focus": FocusSettings,         # フォーカス制御に関する設定値のDataClass
		"image": ImageSettings,         # 画像データに関する設定値のDataClass
	}
	.Options = {
		"exposure": ExposureOptions,	# 露出制御に関する設定可能なオプションのDataClass
		"focus": FocusOptions,			# フォーカス制御に関する設定可能なオプションのDataClass
		"image": ImageOptions,			# 画像データに関する設定可能なオプションのDataClass
	}
```
設定値とオプション情報はグルーピングされて DataClass で定義されている。\
すべての設定値とオプション情報が一括で取得される。\
設定値の DataClass は ExposureSettings, FocusSettings, ImageSettings で定義される。\
オプションの DataClass は ExposureOptions, FocusOptions, ImageOptions で定義される。\
定義値の殆どは str 型による可読な文字列を用い、一部、bool, int 型のものがある。\
カメラの設定画面に表示される文字列表現をほぼ踏襲している。
```
- settings["exposure"] : ExposureSettings
	.program_mode : str				# プログラムモード ex. "P", "A", "S", "M"
	.exposure_compensation : str	# 露出補正値 ex. "+1.0EV", "-0.3EV"
	.shutter_speed : str			# シャッター速度 ex. "1/125", "30s", "5m"
	.aperture : str					# 絞り値 ex. "F2.8", "F5.6"
	.iso_sensitivity : str			# ISO感度 ex. "ISO 200", "ISO 6400"

- settings["focus"] : FocusSettings
	.focus_mode : str				# フォーカスモード ex. "MF", "AF-S", "AF-C"
	.mf_distance : int				# フォーカス距離（内部値）
	.af_mode : str					# オートフォーカスモード ex. "SINGLE", "ZONE", "WIDETRACKING"
	.af_area_size : str				# AFエリアの大きさ ex. "Small", "Medium", "Large"
	.af_point: (int, int)			# AF点の位置 (x, y)

- settings["image"] : ImageSettings
	.image_quality : str			# 画像品質 ex. "Fine", "Normal", "RAW"
	.image_size : str				# 画像サイズ ex. "L", "M", "S"

- options["exposure"] : ExposureOptions
	.program_mode : list[str]		# プログラムモードの選択肢 ex. ["P", "A", "S", "M"]
	.exposure_compensation : list[str]	# 露出補正値の選択肢
	.shutter_speed : list[str]		# シャッター速度の選択肢
	.aperture : list[str]			# 絞り値の選択肢
	.iso_sensitivity : list[str]	# ISO感度の選択肢

- options["focus"] : FocusOptions
	.focus_mode : list[str]			# フォーカスモードの選択肢 ex. ["MF", "AF-S", "AF-C"]
	.mf_distance : (int, int, int)	# フォーカス距離の範囲 (min_distance, max_distance, step_distance)
	.af_mode : list[str]			# AFモードの選択肢	ex. ["SINGLE", "ZONE", "WIDETRACKING"]
	.af_area_size : list[str]		# AFエリアの大きさの選択肢
	.af_point_h : list[int]			# AF点の水平方向の位置の選択肢
	.af_point_v : list[int]			# AF点の垂直方向の位置の選択肢

- options["image"] : ImageOptions
	.image_quality : list[str]		# 画像品質の選択肢 ex. ["Fine", "Normal", "RAW"]
	.image_size : list[str]			# 画像サイズの選択肢 ex. ["L", "M", "S"]
```
現在のバージョンでは ホワイトバランスやカラープロファイルの設定はサポートされていない。

### setup()
カメラの設定を変更する。
```python
setup()
setup( program_mode={program_mode}, exposure_compensation={exposure_compensation}, shutter_speed={shutter_speed}, aperture={aperture}, iso_sensitivity={iso_sensitivity} )
setup( focus_mode={focus_mode}, mf_distance={mf_distance}, af_mode={af_mode}, af_area_size={af_area_size} )

result: ResultConfig
	.success
	.error_message
	.settings = {
		"exposure": ExposureSettings,   # 露出制御に関する設定値のDataClass
		"focus": FocusSettings,         # フォーカス制御に関する設定値のDataClass
		"image": ImageSettings,         # 画像データに関する設定値のDataClass
	}
	.options = {
		"exposure": ExposureOptions,    # 露出制御に関する設定可能なオプションのDataClass
		"focus": FocusOptions,          # フォーカス制御に関する設定可能なオプションのDataClass
		"image": ImageOptions,          # 画像データに関する設定可能なオプションのDataClass
	}
```
必要なパラメータだけを指定して設定を変更できる。\
同時に変えたい場合は複数のパラメータを組み合わせて指定する。\
ResultConfig の settings と options は、設定した結果に応じて変化した設定値とオプション情報が返る。\
何も指定しない空の setup() は、現在のオブジェクト内のキャッシュしている設定値とオプション情報を返す。

- program_mode, exposure_compensation, shutter_speed, aperture, iso_sensitivity \
	露出制御に関する設定値を変更する。\
	必要なパラメータのみを指定して変更することができ、省略したパラメータは現在の設定値を維持する。\
	指定可能な値は get_config() の options で知ることができる。\
	プログラムモードに対して指定できない設定項目を組み合わせるとエラーとなる。（例：プログラムモードが "P" の場合にシャッター速度や絞りを指定する）

- focus_mode, mf_distance, af_mode, af_area_size\
	フォーカス制御に関する設定値を変更する。\
	必要なパラメータのみを指定して変更することができ、省略したパラメータは現在の設定値を維持する。\
	指定可能な値は get_config() の options で知ることができる。\
	フォーカスモードに対して指定できない設定項目を組み合わせるとエラーとなる。（例：フォーカスモードが "MF" の場合に AFモードを指定する）\
	AFモードを ZONE や WIDETRACKING に変更した場合、AFエリアの大きさは制約される。\
	AFエリアの移動は focus_on() で行う。AFエリアの大きさに応じて移動範囲が制約される。

- image_quality, image_size\
	現在のバージョンでは参照のみ可能。カメラ接続時のカメラの状態を引き継ぐ。

## Liveview operations
### get_liveview_config()
選択可能なライブビュー画質オプションを返す。
```python
get_liveview_config()

result: ResultConfig
	.success
	.error_message
	.settings = {
		"liveview": LiveviewSettings,   # ライブビュー制御に関する設定値のDataClass
	}
	.options = {
		"liveview": LiveviewOptions,    # ライブビュー制御に関する設定可能なオプションのDataClass
	}
```
liveview の設定値とオプション情報はグルーピングされて DataClass で定義されている。\
```
- settings["liveview"] : LiveviewSettings
	.liveview_quality : str			# ライブビュー画質 ex. "FINE", "NORMAL"
	.liveview_size : str			# ライブビューサイズ ex. "L", "M", "S"
	.liveview_zoom : str			# ライブビューズーム ex. "x1.0", "x2.5", ...
- options["liveview"] : LiveviewOptions
	.liveview_quality : list[str]	# ライブビュー画質の選択肢 ex. ["High", "Medium"]
	.liveview_size : list[str]		# ライブビューサイズの選択肢 ex. ["L", "M", "S"]
	.liveview_zoom : list[str]		# ライブビューズームの選択肢 ex. ["x1.0", "x2.5", ...]
```
カメラの機種によってサポートされる画質やズームの選択肢が異なる。\
一部の機種ではカメラ本体がより多くの選択肢をもっていても、オプションが3段階に制約されることがある。

### start_liveview()
ライブビューを開始する。
```python
start_liveview()
start_liveview( liveview_quality={liveview_quality}, liveview_size={liveview_size}, liveview_zoom={liveview_zoom} )

result: ResultStatus
	.success
	.error_message
	.camera_status
		.is_ready
		.buffer_count
		.conditions[] 	# 開始すると "liveviewing" が追加される。
```
- liveview_quality, liveview_size, liveview_zoom\
	デフォルトは quality="FINE", size="L", zoom="x1.0" で起動する。\
	必要に応じて任意の項目を指定する。\
	ライブビュー動作中に設定を変更できないため、途中で倍率を変えたい場合は、一度ライブビューを停止してから再度 start_liveview() を呼び出す。

注意点：ライブビューを安定して動作させるためには以下の条件を推奨する。
- focus_mode = "MF"
- focus_mode = "AF-S" or "AF-C",  af_mode = "SINGLE", pre_af = False


### stop_liveview()
ライブビューを停止する。
```python
stop_liveview()

result: ResultConfig
	.success
	.error_message
	.camera_status
		.is_ready
		.buffer_count
		.conditions[] 	# 停止すると "liveviewing" が削除される。
```

### get_liveview_image()
ライブビューの画像を取得する。
```
get_liveview_image()

result: ResultImage
	.success
	.error_message
	.image_data : bytearray # JPEGデータ
	.image_note : dict  	# （通常はNone）
```
ライブビュー画像のJPEGデータをバッファで受け取る。\
bytes型でJPEGデータが返る。\
呼び出し時点での最新のライブビュー画像が取得される。\
カメラの更新より速く呼び出しても、新しい画像が取り込まれるのを待ってから返る。\
カメラの更新より遅れて呼び出しても、古い画像は上書きされて最新の画像が取得される。

## Other operations
	(Not implemented yet)

---
**end of document**