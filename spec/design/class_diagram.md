# クラス図

## 1. 概要

本ドキュメントは、蔵書管理アプリケーションの主要なクラスとその関係性を示します。Mermaid 記法を用いて記述されています。

## 2. クラス図

```mermaid
classDiagram
    class Book {
        +INTEGER id
        +TEXT title
        +TEXT subtitle
        +INTEGER volume
        +TEXT author
        +TEXT original_author
        +TEXT series
        +TEXT category
        +INTEGER rating
        +INTEGER is_magazine_collection
        +TEXT file_path
        +TEXT file_hash
        +TEXT created_at
    }

    class ScanFolder {
        +INTEGER id
        +TEXT path
        +INTEGER is_private
    }

    class ExcludeFolder {
        +INTEGER id
        +TEXT path
    }

    class AppSettings {
        +TEXT key
        +TEXT value
    }

    class DatabaseManager {
        +connect()
        +disconnect()
        +create_tables()
        +save_book(book)
        +get_books()
        +update_book(book)
        +delete_book(id)
        +save_scan_folder(folder)
        +get_scan_folders()
        +delete_scan_folder(id)
        +save_exclude_folder(folder)
        +get_exclude_folders()
        +delete_exclude_folder(id)
        +get_setting(key)
        +set_setting(key, value)
    }

    class FileNameParser {
        +parse_filename(filename)
    }

    class FileScanner {
        +scan_folders()
    }

    class MainWindow {
        +show()
        +toggle_mode()
        +open_settings()
        +sync_data()
        +open_viewer()
    }

    class SettingsWindow {
        +show()
        +save_settings()
        +cancel_settings()
    }

    class PasswordInputWindow {
        +show()
        +authenticate(password)
    }

    DatabaseManager "1" --o "*" Book : manages
    DatabaseManager "1" --o "*" ScanFolder : manages
    DatabaseManager "1" --o "*" ExcludeFolder : manages
    DatabaseManager "1" --o "*" AppSettings : manages

    FileNameParser ..> Book : creates

    FileScanner ..> DatabaseManager : uses
    FileScanner ..> FileNameParser : uses

    MainWindow "1" --o "1" DatabaseManager : uses
    MainWindow "1" --o "1" FileScanner : uses
    MainWindow ..> SettingsWindow : opens
    MainWindow ..> PasswordInputWindow : opens

    SettingsWindow "1" --o "1" DatabaseManager : uses
    SettingsWindow ..> PasswordInputWindow : opens

    PasswordInputWindow ..> MainWindow : returns_to
    PasswordInputWindow ..> SettingsWindow : returns_to

```

### 2.1. 説明

- **Book, ScanFolder, ExcludeFolder, AppSettings**: データモデルを表すクラスです。
- **DatabaseManager**: データベースとのやり取りを管理し、各データモデルの CRUD 操作を提供します。
- **FileNameParser**: ファイル名から書籍情報を解析する機能を提供します。
- **FileScanner**: 指定されたフォルダをスキャンし、ファイルシステムとデータベースの同期を行います。
- **MainWindow**: アプリケーションのメインウィンドウを管理し、主要な機能へのアクセスを提供します。
- **SettingsWindow**: アプリケーションの設定を行うウィンドウを管理します。
- **PasswordInputWindow**: パスワード入力を処理するウィンドウを管理します。

各矢印はクラス間の関係性を示します。

- `--o`: 集約 (Aggregation) - 全体と部分が独立して存在できる関係。
- `..>`: 依存 (Dependency) - あるクラスが別のクラスの機能を利用する関係。
