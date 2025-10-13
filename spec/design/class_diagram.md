# クラス図

## 1. 概要

本ドキュメントは、蔵書管理アプリケーションの主要なクラスとその関係性を示します。
クリーンアーキテクチャの思想を参考に、関心の分離と依存関係の制御を目指した設計となっています。

## 2. レイヤー構造

本アプリケーションは、関心の分離と依存関係の制御を目的とした、クリーンアーキテクチャに近いレイヤー構造を採用しています。各レイヤーは以下の責務を持ちます。

- **UI (View) 層:** ユーザーインターフェースの表示とユーザー入力を担当します。`View_Logic`（ウィンドウの振る舞いを定義）と`View_Base`（ウィジェットの配置を定義）に分かれています。この層は、内側のレイヤーについて一切関知しません。
- **Factories 層:** UI コンポーネントの具体的なインスタンスを生成する責務を持ちます。これにより、`Controller`層が具体的な UI クラスに依存することを防ぎます。
- **Interfaces 層:** 各レイヤー間の境界を定義するインターフェース（抽象クラス）群です。依存性の逆転を実現し、内側のレイヤーが外側のレイヤーに依存しないようにするための重要な役割を担います。
- **Controller 層:** アプリケーションのユースケースを実装し、UI からの入力を受け取って`Core`層のビジネスロジックを呼び出し、その結果を UI に反映させるよう指示します。
- **Core 層:** アプリケーションの中核となるビジネスロジックとデータアクセスを担当します。データベース操作、ファイルスキャン、ファイル名解析などが含まれます。この層は UI について一切関知しません。
- **Models 層:** アプリケーション全体で利用されるデータ構造（エンティティ）を定義します。

依存関係は常に外側のレイヤーから内側のレイヤーに向かってのみ発生し、`Interfaces`層を介することで、このルールが徹底されます。

## 3. クラス図

```mermaid
classDiagram
    direction LR

    subgraph Controller
        class ApplicationController {
            +run()
            +toggle_private_mode()
            +open_book_edit_dialog()
            +run_scan_and_refresh()
            +...
        }
    end

    subgraph Factories
        class DialogFactory {
            +create_password_dialog()
            +create_book_edit_dialog()
        }
    end

    subgraph Interfaces
        class IDialogFactory {
            <<interface>>
            +create_password_dialog()
            +create_book_edit_dialog()
        }
        class IMainWindow {
            <<interface>>
            +sync_requested
            +settings_requested
            +show_warning(title, message)
            +...
        }
        class ISettingsWindow {
            <<interface>>
            +save_settings_requested
            +change_password_requested
            +...
        }
        class IPasswordDialog {
            <<interface>>
            +get_password()
            +set_mode(mode)
            +exec()
        }
        class IBookEditDialog {
            <<interface>>
            +display_book_data(book)
            +get_book_data()
            +exec()
        }
        class IApplicationController {
            <<interface>>
            +authenticate_and_open_settings()
            +change_password()
            +...
        }
    end

    subgraph View_Logic
        class MainWindow {
            +display_books(books)
            +get_selected_book()
            +show_warning(title, message)
            +...
        }
        class SettingsWindow {
            +display_settings(...)
            +get_settings()
            +...
        }
        class PasswordDialog {
            +get_password()
            +set_mode(mode)
            +...
        }
        class BookEditDialog {
            +display_book_data(book)
            +get_book_data()
            +...
        }
    end

    subgraph View_Base
        class Ui_MainWindow {
            +setupUi(MainWindow)
        }
        class Ui_SettingsWindow {
            +setupUi(SettingsWindow)
        }
        class Ui_PasswordDialog {
            +setupUi(PasswordDialog, mode)
        }
        class Ui_BookEditDialog {
            +setupUi(BookEditDialog)
        }
    end

    subgraph Core
        class DatabaseManager {
            +save_book(book)
            +get_all_books()
            +get_books_for_display()
            +...
        }
        class FileNameParser {
            +parse_filename(filename)
        }
        class FileScanner {
            +scan_folders()
        }
        class ParsingRuleLoader {
            +load_rules()
        }
        class Security {
            <<module>>
            +hash_password(password)
            +verify_password(stored_hash, password)
        }
    end

    subgraph Models
        class Book {
            +id: int
            +title: str
            +author: str
            +...
        }
    end

    %% --- Relationships ---
    QObject <|-- IMainWindow
    QObject <|-- ISettingsWindow
    QObject <|-- IPasswordDialog
    QObject <|-- IBookEditDialog

    IMainWindow <|.. MainWindow : implements
    ISettingsWindow <|.. SettingsWindow : implements
    IPasswordDialog <|.. PasswordDialog : implements
    IBookEditDialog <|.. BookEditDialog : implements
    IApplicationController <|.. ApplicationController : implements
    IDialogFactory <|.. DialogFactory : implements

    ApplicationController ..> IMainWindow : uses
    ApplicationController ..> ISettingsWindow : uses
    ApplicationController ..> IDialogFactory : uses
    ApplicationController --> FileScanner : uses
    ApplicationController --> DatabaseManager : uses

    DialogFactory ..> IPasswordDialog : creates
    DialogFactory ..> IBookEditDialog : creates

    MainWindow <|-- Ui_MainWindow : inherits
    SettingsWindow <|-- Ui_SettingsWindow : inherits
    PasswordDialog <|-- Ui_PasswordDialog : inherits
    BookEditDialog <|-- Ui_BookEditDialog : inherits

    FileScanner --> DatabaseManager : uses
    FileScanner --> FileNameParser : uses
    FileNameParser ..> Book : creates
    DatabaseManager ..> Book : manages
```

## 4. クラス詳細

### Controller

#### `ApplicationController`

アプリケーション全体の動作を制御する Presenter としての役割を担います。UI（View）からのユーザーイベントを受け取り、それに応じて Core（Model）のビジネスロジックを実行し、最終的な結果を View に表示するよう指示します。View と Model の間の仲介役として、両者が互いに直接関与しないように分離する責務を持ちます。具体的な UI クラス（ダイアログ等）に依存せず、`IDialogFactory` を通じて UI コンポーネントを生成します。

### Factories

#### `DialogFactory`

`IDialogFactory`インターフェースの具体的な実装クラスです。`PasswordDialog`や`BookEditDialog`といった、具体的な UI ダイアログのインスタンスを生成する責務を持ちます。

### Interfaces

#### `IDialogFactory`

ダイアログ生成の責務を抽象化するインターフェースです。`ApplicationController`は、このインターフェースに依存することで、具体的なダイアログクラスを知ることなく、ダイアログの生成を要求できます。

#### `IMainWindow`

メインウィンドウが Presenter に提供すべきインターフェースを定義します。ユーザー操作の通知（`pyqtSignal`）や、メッセージ表示、書籍リストの更新といった、Presenter が View を操作するためのメソッド（`show_warning`など）を抽象化します。

#### `ISettingsWindow`

設定ウィンドウが Presenter に提供すべきインターフェースを定義します。

#### `IPasswordDialog`

パスワードダイアログが Presenter に提供すべきインターフェースを定義します。

#### `IBookEditDialog`

書籍編集ダイアログが Presenter に提供すべきインターフェースを定義します。

#### `IApplicationController`

ApplicationController が View に提供すべきインターフェースを定義します。View が Presenter の具体的な実装に依存せず、抽象的な操作を呼び出せるようにします。

### View_Logic

#### `MainWindow`

アプリケーションのメインウィンドウの振る舞いを定義する View クラスです。UI の構築自体は`Ui_MainWindow`から継承し、自身はユーザー操作（ボタンクリック、検索入力など）のシグナルを`ApplicationController`に接続したり、`ApplicationController`からの指示で書籍リストの表示を更新したりするロジックを担当します。

#### `SettingsWindow`

設定ダイアログの振る舞いを定義する View クラスです。スキャン対象フォルダの追加・削除や、ビューアパスの設定といったユーザー操作をハンドリングし、最終的な設定値を`ApplicationController`に渡す責務を持ちます。

#### `PasswordDialog`

パスワード認証および設定ダイアログの振る舞いを定義する View クラスです。入力されたパスワードの検証や、`ApplicationController`への入力値の受け渡しを担当します。

#### `BookEditDialog`

書籍情報編集ダイアログの振る舞いを定義する View クラスです。既存の書籍情報をフォームに表示し、ユーザーによって編集された新しい書籍情報を`ApplicationController`に渡す責務を持ちます。

### View_Base

#### `Ui_MainWindow`, `Ui_SettingsWindow`, etc.

各 View クラスの見た目（ウィジェットの配置、レイアウト、スタイル）のみを定義するベースクラス群です。これらのクラスはロジックを一切含まず、Qt Designer で自動生成されるファイル、またはそれに準ずる手動での UI 定義ファイルとして扱われます。

### Core

#### `DatabaseManager`

SQLite データベースとのすべてのやり取りをカプセル化するクラスです。接続管理、テーブルの作成、書籍情報や設定の CRUD（作成、読み取り、更新、削除）操作といった、データベースに関するすべての責務を負います。

#### `ParsingRuleLoader`

ファイル名の解析ルールを JSON ファイルから読み込み、優先度順にソートする責務を持つクラスです。

#### `FileNameParser`

`ParsingRuleLoader`によって読み込まれたルールに基づき、ファイル名文字列を解析して`Book`オブジェクトを生成する責務を持ちます。

#### `FileScanner`

指定されたフォルダを再帰的にスキャンし、ファイルシステム上のファイルとデータベース上の書籍情報を同期させる責務を持ちます。ファイルのハッシュ値を計算し、新規、更新、削除されたファイルを検出します。

#### `Security`

パスワードのハッシュ化や検証など、セキュリティ関連のヘルパー関数を提供します。

### Models

#### `Book`

一冊の書籍に関するすべてのメタデータ（タイトル、著者、ファイルパスなど）を保持するデータクラスです。アプリケーション全体で書籍情報をやり取りする際の標準的な形式として利用されます。

### 4.1. 関係性

- `<|--`: 継承 (Inheritance) - View ロジッククラスが View 定義クラスを継承して UI を構築します。
- `-->`: 関連 (Association) - クラス間の持続的な関係（例: `ApplicationController`が`MainWindow`を制御する）。
- `..>`: 依存 (Dependency) - あるクラスが別のクラスの機能を利用する関係（例: `FileNameParser`が`Book`を生成する）。
