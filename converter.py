import os
import subprocess
import shutil 
import zipfile 
import rarfile 
from pathlib import Path
from typing import List
from bs4 import BeautifulSoup 

# --- 設定 ---
INPUT_DIR_NAME = "input"
OUTPUT_DIR_NAME = "output"
TEMP_DIR_NAME = "__temp_archive__" 
# Calibreのebook-convertコマンドの実行ファイル名
EBOOK_CONVERT_COMMAND = "ebook-convert" 


def get_series_info_interactively() -> List[str]:
    """
    ユーザーからシリーズ名と巻数をインタラクティブに取得します。（シリーズ名はバッチ全体に適用）
    """
    print("\n--- シリーズ情報の設定 (バッチ全体に適用) ---")
    series_name = input("📚 シリーズ名を入力してください (スキップする場合はEnter): ").strip()
    
    args: List[str] = []
    
    if series_name:
        args.extend(["--series", series_name])
        print("✅ シリーズ名が設定されました。")
    else:
        print("--- シリーズ名設定をスキップします ---")
        
    return args


def get_series_index_interactively(filename: str) -> List[str]:
    """
    ユーザーから指定されたファイルの巻数をインタラクティブに取得します。（ファイルごとに適用）
    """
    print(f"\n--- ファイル: {filename} の巻数設定 ---")
    args: List[str] = []
    series_index = input("🔢 巻数 (シリーズインデックス) を入力してください (省略する場合はEnter): ").strip()
    if series_index and series_index.isdigit():
        args.extend(["--series-index", series_index])
        print(f"✅ {filename} の巻数が設定されました。")
    elif series_index:
        print(f"⚠️ {filename} の巻数が数字ではないため、巻数の設定はスキップします。")
    else:
        print(f"--- {filename} の巻数設定をスキップします ---")
    return args


def execute_conversion(input_path: Path, output_path: Path, extra_args: List[str] = None) -> bool:
    """
    ebook-convertコマンドを実行し、ファイルを指定されたパスに変換します。
    """
    
    command = [
        EBOOK_CONVERT_COMMAND,
        str(input_path),
        str(output_path),
    ]
    
    if extra_args:
        command.extend(extra_args)

    print(f"▶️ コマンド実行中: {' '.join(command)}")

    try:
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

    extra_args = [
        "--title", base_name, 
        "--language", "ja", 
    ]
    extra_args.extend(global_series_args)

    print(f"\n[MOBI変換開始] ファイル: {mobi_file_path.name}")
    
    file_series_index_args = get_series_index_interactively(mobi_file_path.name)
    extra_args.extend(file_series_index_args)

    execute_conversion(mobi_file_path, output_epub_path, extra_args)


def convert_jpeg_folder(jpeg_dir_path: Path, output_dir: Path, global_series_args: List[str]):
    """JPEG画像を含むディレクトリをEPUB（コミック形式推奨、メタデータ設定を含む）に変換します。"""
    
    base_name = jpeg_dir_path.name 
    output_epub_path = output_dir / f"{base_name}.epub"
    
    extra_args = [
        "--output-profile", "tablet",  
        "--no-default-epub-cover",     
        "--epub-flatten", 
        "--title", base_name, 
        "--language", "ja", 
    ]
    extra_args.extend(global_series_args)

    print(f"\n[JPEGフォルダ変換開始] フォルダ: {jpeg_dir_path.name}")

    folder_series_index_args = get_series_index_interactively(jpeg_dir_path.name)
    extra_args.extend(folder_series_index_args)

    execute_conversion(jpeg_dir_path, output_epub_path, extra_args)


def extract_archive(archive_path: Path, temp_dir: Path) -> Path | None:
    """
    指定されたZIP/RARファイルを一時ディレクトリに解凍し、解凍されたフォルダのPathを返します。
    """
    
    print(f"🔄 アーカイブファイルを解凍中: {archive_path.name}")
    
    extract_target_dir_name = archive_path.stem
    extract_target_path = temp_dir / extract_target_dir_name
    
    try:
        extract_target_path.mkdir(parents=True, exist_ok=True)
        archive_suffix = archive_path.suffix.lower()

        if archive_suffix == '.zip':
            if not zipfile.is_zipfile(archive_path):
                print(f"⚠️ {archive_path.name} は有効なZIPファイルではありません。")
                return None
            with zipfile.ZipFile(archive_path, 'r') as zf:
                zf.extractall(extract_target_path) 
            
        elif archive_suffix == '.rar':
            if not rarfile.is_rarfile(archive_path):
                print(f"⚠️ {archive_path.name} は有効なRARファイルではありません。")
                return None
            with rarfile.RarFile(archive_path, 'r') as rf:
                rf.extractall(extract_target_path)
        
        else:
            print(f"⚠️ {archive_path.name} は対応していないアーカイブ形式です。")
            return None
            
        print(f"✅ 解凍完了: -> {extract_target_path.name}/")
        return extract_target_path
    
    except rarfile.RarExecError:
        print(f"❌ RAR解凍エラー: 'unrar' コマンドが見つからないか、実行できませんでした。")
        print("システムに 'unrar' ユーティリティがインストールされ、パスが通っているか確認してください。")
        return None
    except Exception as e:
        print(f"❌ アーカイブファイルの解凍中にエラーが発生しました: {e}")
        # 解凍に失敗したディレクトリは削除
        if extract_target_path.exists():
            shutil.rmtree(extract_target_path)
        return None


def fix_xhtml_content(xhtml_path: Path) -> bool:
    """
    XHTMLファイルを開き、<body>内にある<img>タグが2つ以上の場合、最初の1つだけを残して他を削除する。
    """
    try:
        with open(xhtml_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        body = soup.find('body')
        if not body:
            return False

        img_tags = body.find_all('img')

        # <img>タグが2つ以上ある場合に修正を実行
        if len(img_tags) < 2:
            return False 

        first_img = img_tags[0]
        
        # 最初のタグ以外のすべてを削除
        for img_tag in img_tags[1:]:
            img_tag.decompose() 

        # 最初の <img> タグから、スライス用のCSSクラスやスタイルを可能な限り除去
        if 'class' in first_img.attrs:
             del first_img.attrs['class']
        if 'style' in first_img.attrs:
             del first_img.attrs['style']

        with open(xhtml_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
            
        print(f"   [HTML修正] ✅ {xhtml_path.name}: {len(img_tags)}個の<img>タグを1つにマージしました。")
        return True

    except Exception as e:
        print(f"   [HTML修正] ❌ {xhtml_path.name} の修正中にエラーが発生しました: {e}")
        return False


def fix_html_and_repack_epub(epub_path: Path, temp_dir: Path):
    """
    EPUBをZIP展開し、HTMLコンテンツを修正した後、EPUBの仕様に従って再ZIP化する。
    元のEPUBファイルの削除は、再パッケージ化が成功した直後に行う。
    """
    temp_extract_dir = temp_dir / epub_path.stem
    
    print(f"\n[EPUB修正開始] 🔄 {epub_path.name} を展開中...")
    
    try:
        # 1. EPUBの展開
        shutil.unpack_archive(epub_path, temp_extract_dir, 'zip')

        # 2. HTMLコンテンツの修正
        html_fixed_count = 0
        for file_path in temp_extract_dir.rglob('*.html'):
            if fix_xhtml_content(file_path):
                html_fixed_count += 1
                
        for file_path in temp_extract_dir.rglob('*.xhtml'):
            if fix_xhtml_content(file_path):
                html_fixed_count += 1
                
        print(f"   [HTML修正] {html_fixed_count} 個のHTML/XHTMLファイルを修正しました。")
        
        # 3. 再ZIP化 (一時ファイル名で保存)
        temp_epub_path = epub_path.with_suffix('.temp.epub')
        print(f"   [再パッケージ] 🔄 EPUB仕様に従って {epub_path.name} を再パッケージ化中...")
        
        with zipfile.ZipFile(temp_epub_path, 'w') as zf: 
            
            # A. mimetype ファイルを無圧縮でZIPの最初に書き込む (EPUB仕様)
            mimetype_path = temp_extract_dir / 'mimetype'
            if mimetype_path.exists():
                zf.write(mimetype_path, 'mimetype', compress_type=zipfile.ZIP_STORED)
            
            # B. 残りのファイルとフォルダを圧縮して書き込む
            for item in temp_extract_dir.rglob('*'):
                if item.is_file() and item.name != 'mimetype':
                    arcname = item.relative_to(temp_extract_dir)
                    zf.write(item, arcname)
                    
        # 4. 成功した場合のみ、元のファイルを削除し、一時ファイルをリネーム
        epub_path.unlink(missing_ok=True) 
        temp_epub_path.rename(epub_path)
                    
        print(f"   [再パッケージ] ✅ 成功しました。")

    except Exception as e:
        print(f"❌ 処理中にエラーが発生しました。元のファイルは保持されます。エラー: {e}")
        # 失敗した場合、一時ファイルが残っていれば削除
        if 'temp_epub_path' in locals() and temp_epub_path.exists():
            temp_epub_path.unlink()
        
    finally:
        # 展開失敗・成功に関わらず、temp_extract_dirが存在すれば削除
        if temp_extract_dir.exists():
            shutil.rmtree(temp_extract_dir)
            print(f"🧹 一時展開フォルダを削除しました: {temp_extract_dir.name}")
        
        print(f"[EPUB修正完了] {epub_path.name}")


def main():
    """
    inputディレクトリ内のMOBIファイル、JPEGフォルダ、およびアーカイブ（ZIP/RAR）ファイルを処理し、outputディレクトリに出力します。
    """
    
    base_dir = Path(os.getcwd())
    input_dir = base_dir / INPUT_DIR_NAME
    output_dir = base_dir / OUTPUT_DIR_NAME
    temp_dir = base_dir / TEMP_DIR_NAME 

    # ディレクトリの存在チェックと作成
    if not input_dir.exists():
        print(f"エラー: 入力ディレクトリ '{input_dir.name}' が見つかりません。")
        return
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
        
    # 一時フォルダの初期化
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)

    # 🌟 バッチ処理開始前にシリーズ情報をインタラクティブに取得
    global_series_args = get_series_info_interactively()

    print(f"\n--- 変換処理開始: '{input_dir.name}' から '{output_dir.name}' へ ---")
    
    # 1. input内のすべての項目をチェック
    for item in input_dir.iterdir():
        item_suffix = item.suffix.lower()
        
        if item.is_file() and item.suffix.lower() == '.mobi':
            # MOBIファイルはそのまま処理
            convert_mobi_file(item, output_dir, global_series_args)
            
        elif item.is_dir():
            # 画像フォルダはそのまま処理
            image_extensions = ('.jpg', '.jpeg', '.png')
            has_image = any(f.suffix.lower() in image_extensions for f in item.iterdir() if f.is_file())
            
            if has_image:
                convert_jpeg_folder(item, output_dir, global_series_args)
            else:
                print(f"スキップ: フォルダ '{item.name}' は対応する画像ファイルを含まないため無視します。")
                
        elif item.is_file() and item_suffix in ('.zip', '.rar'): 
            # ZIP/RARファイルは一時ディレクトリに解凍し、解凍されたフォルダを処理
            unpacked_path = extract_archive(item, temp_dir)
            if unpacked_path:
                # 解凍されたフォルダを画像フォルダとして変換
                convert_jpeg_folder(unpacked_path, output_dir, global_series_args)
                
        else:
            print(f"スキップ: '{item.name}' は対象外のファイル形式です。")

    
    print("\n--- 🔧 EPUBファイルの後処理（HTML修正と再パッケージ化）開始 ---")
    
    # outputディレクトリ内のすべてのEPUBファイルを走査
    for epub_file in output_dir.glob('*.epub'):
        # HTML修正と再パッケージ化を実行
        fix_html_and_repack_epub(epub_file, temp_dir)

    # 3. 処理完了後、一時フォルダをクリーンアップ
    print(f"\n🧹 クリーンアップ中: 一時ディレクトリ '{temp_dir.name}' を削除します。")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
        print("✅ クリーンアップ完了。")

    print("\n--- 全ての変換処理が完了しました ---")


if __name__ == "__main__":
    main()
