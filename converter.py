import os
import subprocess
from pathlib import Path
from typing import List

# --- 設定 ---
INPUT_DIR_NAME = "input"
OUTPUT_DIR_NAME = "output"
# Calibreのebook-convertコマンドの実行ファイル名
EBOOK_CONVERT_COMMAND = "ebook-convert" 


def get_series_info_interactively() -> List[str]:
    """
    ユーザーからシリーズ名と巻数をインタラクティブに取得します。

    Returns:
        ebook-convertに渡すシリーズ関連のオプションリスト。
    """
    print("\n--- シリーズ情報の設定 (バッチ全体に適用) ---")
    # シリーズ名を聞く
    series_name = input("📚 シリーズ名を入力してください (スキップする場合はEnter): ").strip()
    
    args: List[str] = []
    
    if series_name:
        args.extend(["--series", series_name])
        
        # 巻数を聞く
        series_index = input("🔢 巻数 (シリーズインデックス) を入力してください (省略する場合はEnter): ").strip()
        if series_index and series_index.isdigit():
            args.extend(["--series-index", series_index])
        elif series_index:
             print("⚠️ 巻数が数字ではないため、巻数の設定はスキップします。")
             
        print("✅ シリーズ情報が設定されました。")
    else:
        print("--- シリーズ情報の設定をスキップします ---")
        
    return args


def execute_conversion(input_path: Path, output_path: Path, extra_args: List[str] = None) -> bool:
    """
    ebook-convertコマンドを実行し、ファイルを指定されたパスに変換します。
    """
    
    # コマンドの基本部分
    command = [
        EBOOK_CONVERT_COMMAND,
        str(input_path),
        str(output_path),
    ]
    
    # 追加引数があれば結合
    if extra_args:
        command.extend(extra_args)

    print(f"▶️ コマンド実行中: {' '.join(command)}")

    try:
        # コマンドを実行し、エラーが発生したら例外をスロー
        subprocess.run(command, capture_output=True, text=True, check=True)
        print(f"✅ 変換成功: {input_path.name} -> {output_path.name}")
        return True
    
    except subprocess.CalledProcessError as e:
        print(f"❌ 変換失敗: {input_path.name} のコマンド実行エラー")
        print(f"エラーメッセージ:\n{e.stderr}")
        return False
    except FileNotFoundError:
        print(f"❌ 致命的なエラー: '{EBOOK_CONVERT_COMMAND}'コマンドが見つかりません。")
        print("Calibreがインストールされ、パスが設定されているか確認してください。")
        return False
    except Exception as e:
        print(f"❌ 予期せぬエラー: {e}")
        return False


def convert_mobi_file(mobi_file_path: Path, output_dir: Path, global_series_args: List[str]):
    """単一のMOBIファイルをEPUBに変換します。（メタデータ設定を含む）"""
    
    base_name = mobi_file_path.stem 
    output_epub_path = output_dir / f"{base_name}.epub"

    # タイトルはファイル名 (拡張子除く)
    extra_args = [
        "--title", base_name, 
        "--language", "ja", # 言語を日本語に設定
    ]
    # シリーズ情報を追加
    extra_args.extend(global_series_args)

    print(f"\n[MOBI変換開始] ファイル: {mobi_file_path.name}")
    execute_conversion(mobi_file_path, output_epub_path, extra_args)


def convert_jpeg_folder(jpeg_dir_path: Path, output_dir: Path, global_series_args: List[str]):
    """JPEG画像を含むディレクトリをEPUB（コミック形式推奨、メタデータ設定を含む）に変換します。"""
    
    base_name = jpeg_dir_path.name 
    output_epub_path = output_dir / f"{base_name}.epub"
    
    # コミック変換用の推奨オプション + タイトル
    extra_args = [
        "--output-profile", "tablet",  
        "--no-default-epub-cover",     
        "--epub-flatten", 
        "--title", base_name, # タイトルはフォルダ名
        "--language", "ja", # 言語を日本語に設定
    ]
    # シリーズ情報を追加
    extra_args.extend(global_series_args)

    print(f"\n[JPEGフォルダ変換開始] フォルダ: {jpeg_dir_path.name}")
    execute_conversion(jpeg_dir_path, output_epub_path, extra_args)


def main():
    """
    inputディレクトリ内のMOBIファイルとJPEGフォルダを処理し、outputディレクトリに出力します。
    """
    
    base_dir = Path(os.getcwd())
    input_dir = base_dir / INPUT_DIR_NAME
    output_dir = base_dir / OUTPUT_DIR_NAME

    # ディレクトリの存在チェックと作成
    if not input_dir.exists():
        print(f"エラー: 入力ディレクトリ '{input_dir.name}' が見つかりません。")
        return
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    # 🌟 バッチ処理開始前にシリーズ情報をインタラクティブに取得
    global_series_args = get_series_info_interactively()

    print(f"\n--- 変換処理開始: '{input_dir.name}' から '{output_dir.name}' へ ---")
    
    # inputディレクトリ内のアイテムを走査
    for item in input_dir.iterdir():
        
        if item.is_file() and item.suffix.lower() == '.mobi':
            # 1. 単体のMOBIファイルを処理
            convert_mobi_file(item, output_dir, global_series_args)
            
        elif item.is_dir():
            # 2. 画像ファイルを含むディレクトリを処理
            
            image_extensions = ('.jpg', '.jpeg', '.png')
            has_image = any(f.suffix.lower() in image_extensions for f in item.iterdir() if f.is_file())
            
            if has_image:
                convert_jpeg_folder(item, output_dir, global_series_args)
            else:
                print(f"スキップ: フォルダ '{item.name}' は対応する画像ファイルを含まないため無視します。")
                
        else:
            print(f"スキップ: '{item.name}' はMOBIファイルでも画像フォルダでもないため無視します。")

    print("\n--- 全ての変換処理が完了しました ---")


if __name__ == "__main__":
    main()
