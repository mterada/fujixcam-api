# -----------------------------------------------------
# clickwrap.py :
#  Clickwrap diaglog for terms of use of SDK.
#
# Clickwrap performs following at first usge of the package.
# 1. Ask the user for the folder where the SDK installed, records it for future use.
# 2. Show dialog before the SDK using to confirm the user's acceptance.
# 3. The result is stored in "_clickwrap.ini" in the same directory as this.
#
# Copyright 2026 Masahiro Terada (@mterada.com)
# This software is released under the MIT License.
# http://opensource.org/licenses/mit-license.php
# -----------------------------------------------------
import os
import tkinter as tk
import configparser
import webbrowser
from datetime import datetime

CLICKWRAP_INI = "_clickwrap.ini"
LICENSER_NAME = "Default_Licenser"

# _clickwrap.ini format:
# [{licenser_name}]
# license_name = {License_Key_Name}
# {License_Key_Name} = accepted     # (after user accepts)
# {License_Key_Name}_accepted_at =  2024-01-01 12:00:00 
# install_path = C:\Path\To\SDK     # (optional, can be set by user)
#
# [License_Key_Name.en]
# title = Clickwrap Agreement
# intro = Please read and accept the following agreement before using the application:
# term1 = 1. You agree to use this application at your own risk.
# term2 = 2. The developers are not responsible for any damage caused by using this application.
# term3 = 3. You agree to comply with all applicable laws while using this application.
# term4 = 4. Additional term (optional, can add more terms)
# more_info = For more information, please visit: 
# url = https://example.com/terms
# accept = Accept
# cancel = Cancel
# lang_button = 日本語
#
# [License_Key_Name.ja]
# title = 利用規約
# intro = アプリケーションを使用する前に、以下の規約をお読みになり、同意してください:
# term1 = 1. 本アプリケーションの使用は、お客様自身の責任において行うものとします。
# term2 = 2. 開発者は、本アプリケーションの使用により生じたいかなる損害についても責任を負いません。
# term3 = 3. お客様は、本アプリケーションの使用中、適用されるすべての法律を遵守することに同意します。
# term4 = 4. 追加の条項（オプション、さらに追加可能）
# more_info = 詳細については、こちらをご覧ください: 
# url = https://example.com/terms-ja
# accept = 同意する
# cancel = キャンセル
# lang_button = English

# デフォルト言語辞書（iniファイルに言語セクションがない場合のフォールバック）
DEFAULT_LANGUAGES = {
    "en": {
        "title": "User License Agreement",
        "intro": "Please read and accept the following agreement before using the application:\n\n",
        "terms": [
            "1. You agree to use this application at your own risk.\n",
            "2. The developers are not responsible for any damage caused by using this application.\n",
            "3. You agree to comply with all applicable laws while using this application.\n"
        ],
        "more_info": "For more information, please visit: ",
        "url": "https://example.com/terms",
        "accept": "Accept",
        "cancel": "Cancel",
        "lang_button": "日本語で表示"
    },
    "ja": {
        "title": "利用規約",
        "intro": "アプリケーションを使用する前に、以下の規約をお読みになり、同意してください:\n\n",
        "terms": [
            "1. 本アプリケーションの使用は、お客様自身の責任において行うものとします。\n",
            "2. 開発者は、本アプリケーションの使用により生じたいかなる損害についても責任を負いません。\n",
            "3. お客様は、本アプリケーションの使用中、適用されるすべての法律を遵守することに同意します。\n"
        ],
        "more_info": "詳細については、こちらをご覧ください: ",
        "url": "https://example.com/terms-ja",
        "accept": "同意する",
        "cancel": "キャンセル",
        "lang_button": "Show in English"
    }
}

def _load_languages_from_config(config, license_name):
    """iniファイルからLANGUAGES辞書を読み込む
    
    セクション名は {license_name}.en, {license_name}.ja の形式
    """
    languages = {}
    for lang in ["en", "ja"]:
        section_name = f"{license_name}.{lang}"
        if config.has_section(section_name):
            # term* キーを動的に読み込む
            terms = []
            term_num = 1
            while True:
                term_key = f"term{term_num}"
                if config.has_option(section_name, term_key):
                    term_text = config.get(section_name, term_key).replace("\\n", "\n")
                    terms.append(term_text + "\n")
                    term_num += 1
                else:
                    break
            
            # termsが空の場合はデフォルトを使用
            if not terms:
                terms = DEFAULT_LANGUAGES[lang]["terms"]
            
            languages[lang] = {
                "title": config.get(section_name, "title", fallback=DEFAULT_LANGUAGES[lang]["title"]),
                "intro": config.get(section_name, "intro", fallback=DEFAULT_LANGUAGES[lang]["intro"]).replace("\\n", "\n") + "\n\n",
                "terms": terms,
                "more_info": config.get(section_name, "more_info", fallback=DEFAULT_LANGUAGES[lang]["more_info"]),
                "url": config.get(section_name, "url", fallback=DEFAULT_LANGUAGES[lang]["url"]),
                "accept": config.get(section_name, "accept", fallback=DEFAULT_LANGUAGES[lang]["accept"]),
                "cancel": config.get(section_name, "cancel", fallback=DEFAULT_LANGUAGES[lang]["cancel"]),
                "lang_button": config.get(section_name, "lang_button", fallback=DEFAULT_LANGUAGES[lang]["lang_button"])
            }
        else:
            languages[lang] = DEFAULT_LANGUAGES[lang]
    return languages

def _setup_text_with_link(text_widget, texts ):
    """テキストウィジェットにリンク付きテキストを設定"""
    text_widget.config(state=tk.NORMAL)
    text_widget.delete(1.0, tk.END)
    text_widget.insert(tk.END, texts["intro"])

    # 可変個数のtermsを表示
    for term in texts["terms"]:
        text_widget.insert(tk.END, term)
    text_widget.insert(tk.END, "\n")
    text_widget.insert(tk.END, texts["more_info"])
    text_widget.insert(tk.END, "\n")
    # URLリンクの追加
    text_widget.insert(tk.END, texts["url"], "hyperlink")
    text_widget.insert(tk.END, "\n") 

    # リンクの装飾
    text_widget.tag_config("hyperlink", foreground="blue", underline=True)
    
    # リンクのクリックイベント
    def open_link(event):
        webbrowser.open(texts["url"])
    
    # マウスカーソルの変更
    def on_enter(event):
        text_widget.config(cursor="hand2")
    
    def on_leave(event):
        text_widget.config(cursor="arrow")
    
    text_widget.tag_bind("hyperlink", "<Button-1>", open_link)
    text_widget.tag_bind("hyperlink", "<Enter>", on_enter)
    text_widget.tag_bind("hyperlink", "<Leave>", on_leave)
    
    text_widget.config(state=tk.DISABLED)

def confirm_clickwrap(filename=CLICKWRAP_INI, licenser=LICENSER_NAME, language="ja"):
    # _clickwrap.ini is expected to be in the same directory as this script
    config = configparser.ConfigParser()
    filepath = os.path.join( os.path.dirname(os.path.abspath(__file__)), filename )
    config.read(filepath, encoding="utf-8")
    
    # license_nameをlicenserセクションから取得
    license_name = config.get(licenser, "license_name", fallback="license_sample")
    
    # Check if the clickwrap agreement has already been accepted
    if config.has_section(licenser) and config.get(licenser, license_name, fallback="no") == "accepted":
        return True
    
    # LANGUAGESをiniファイルから読み込む
    LANGUAGES = _load_languages_from_config(config, license_name)

    # If not accepted, show the clickwrap agreement
    root = tk.Tk()
    
    # 現在の言語を管理
    current_lang = tk.StringVar(value=language)
    texts = LANGUAGES.get(language, LANGUAGES["ja"])
    root.title(texts["title"])

    # 言語切替ボタン
    def switch_language():
        new_lang = "ja" if current_lang.get() == "en" else "en"
        current_lang.set(new_lang)
        update_ui()
    
    def update_ui():
        texts = LANGUAGES[current_lang.get()]
        root.title(texts["title"])
        _setup_text_with_link(agreement_text, texts)
        cancel_button.config(text=texts["cancel"])
        accept_button.config(text=texts["accept"])
        lang_button.config(text=texts["lang_button"])
    
    lang_button = tk.Button(root, text=texts["lang_button"], command=switch_language)
    lang_button.pack(pady=5)

    # 規約テキスト表示
    agreement_text = tk.Text(root, wrap=tk.WORD, cursor="arrow", height=22, width=80)
    _setup_text_with_link(agreement_text, texts)
    agreement_text.pack(padx=12, pady=8)

    # 同意ボタン
    def accept():
        if not config.has_section(licenser):
            config.add_section(licenser)
        config.set(licenser, license_name, "accepted")
        config.set(licenser, f"{license_name}_accepted_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        with open(filepath, "w", encoding="utf-8") as configfile:
            config.write(configfile)
        root.destroy()
    
    # キャンセルボタン
    def cancel():
        root.destroy()

    # ボタンフレーム（CancelとAcceptを横並びに）
    button_frame = tk.Frame(root)
    button_frame.pack(pady=10)
    
    cancel_button = tk.Button(button_frame, text=texts["cancel"], command=cancel, width=10)
    cancel_button.pack(side=tk.LEFT, padx=5)
    
    accept_button = tk.Button(button_frame, text=texts["accept"], command=accept, width=10)
    accept_button.pack(side=tk.LEFT, padx=5)

    root.mainloop()
    return config.has_section(licenser) and config.get(licenser, license_name, fallback="no") == "accepted"

#
# 以下はSDKのインストールガイドの例。必要に応じて、clickwrapでユーザーにSDKのインストールを促す際に使用する。
# 
def guide_installation( licenser="Default_Licenser", url="https://example.com/download", default_path="" ):
    # SDKのインストールガイドを表示して、ユーザーにインストール先を入力させる
    print( f"{licenser} not found. / {licenser} が見つかりませんでした。" )
    print( f"install_path: {default_path}\n" )
    # 英語、日本語の両方で表示する
    print( f"You can download the SDK from {url} and install it on your system." )
    print( "If you have already installed the SDK, please enter the installation path to load the library." )
    print( "Path is expected to be the directory containing the library files XSDK.DAT, *.dll, *.dylib,..." )
    print( "---" )
    print( f"カメラSDKをメーカーのページ {url} からダウンロードして任意のフォルダに解凍してください。" )
    print( "入手済みであれば保存先のSDKモジュールのフォルダ名（フルパス）を教えてください。" )
    print( "対象のフォルダは、XSDK.DAT や *.dll, *.dylib,...が入っているフォルダです。" )

    install_path = input( f"\nPlease enter the path to {licenser} (or press Enter to retry): " ).strip() or default_path
    print( f"Checking {licenser} module in: {install_path}  ...\n" )
    return install_path

def get_install_path(filename=CLICKWRAP_INI, licenser=LICENSER_NAME):
    config = configparser.ConfigParser()
    filepath = os.path.join( os.path.dirname(os.path.abspath(__file__)), filename )
    config.read(filepath, encoding="utf-8")
    
    # licenser_name SDKのインストール先を _clickwrap.ini から取得する
    if config.has_section(licenser) and config.has_option(licenser, "install_path"):
        return config.get(licenser, "install_path")
    return ""

def set_install_path(install_path, filename=CLICKWRAP_INI, licenser=LICENSER_NAME):
    config = configparser.ConfigParser()
    filepath = os.path.join( os.path.dirname(os.path.abspath(__file__)), filename )
    config.read(filepath, encoding="utf-8")
    
    # licenser_name SDKのインストール先を _clickwrap.ini に保存する
    if not config.has_section(licenser):
        config.add_section(licenser)
    config.set(licenser, "install_path", install_path)
    
    with open(filepath, "w", encoding="utf-8") as configfile:
        config.write(configfile)

def is_license_accepted(filename=CLICKWRAP_INI, licenser=LICENSER_NAME):
    config = configparser.ConfigParser()
    filepath = os.path.join( os.path.dirname(os.path.abspath(__file__)), filename )
    config.read(filepath, encoding="utf-8")

    # license_name を licenserセクションから取得
    license_name = config.get(licenser, "license_name", fallback="license_sample")
    return config.has_section(licenser) and config.get(licenser, license_name, fallback="no") == "accepted"
    