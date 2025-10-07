# シーケンス図

## 1. 概要

本ドキュメントは、蔵書管理アプリケーションの主要な機能におけるオブジェクト間のメッセージのやり取りと時間的な順序を示します。

## 2. 蔵書データの登録と同期処理

```mermaid
sequenceDiagram
    participant User
    participant MainWindow
    participant FileScanner
    participant FileNameParser
    participant DatabaseManager

    User->>MainWindow: 同期ボタンをクリック
    activate MainWindow
    MainWindow->>FileScanner: scan_folders()
    activate FileScanner

    loop 各スキャン対象フォルダ
        FileScanner->>FileScanner: フォルダ内のファイルを走査
        FileScanner->>DatabaseManager: get_book_by_hash(file_hash)
        activate DatabaseManager
        DatabaseManager-->>FileScanner: 既存の書籍情報 or None
        deactivate DatabaseManager

        alt 既存の書籍情報が見つからない場合 (新規ファイル)
            FileScanner->>FileNameParser: parse_filename(filename)
            activate FileNameParser
            FileNameParser-->>FileScanner: 書籍情報 (Bookオブジェクト)
            deactivate FileNameParser
            FileScanner->>DatabaseManager: save_book(book)
            activate DatabaseManager
            DatabaseManager-->>FileScanner: 成功/失敗
            deactivate DatabaseManager
        else 既存の書籍情報が見つかる場合
            alt パスが異なる場合 (ファイル移動)
                FileScanner->>DatabaseManager: update_book_path(book_id, new_path)
                activate DatabaseManager
                DatabaseManager-->>FileScanner: 成功/失敗
                deactivate DatabaseManager
            else ハッシュ値が異なる場合 (ファイル更新)
                FileScanner->>DatabaseManager: update_book_hash(book_id, new_hash)
                activate DatabaseManager
                DatabaseManager-->>FileScanner: 成功/失敗
                deactivate DatabaseManager
            end
        end
    end

    FileScanner->>DatabaseManager: get_all_recorded_books()
    activate DatabaseManager
    DatabaseManager-->>FileScanner: 全ての記録済み書籍情報
    deactivate DatabaseManager

    loop 記録済み書籍と実ファイルの比較
        alt 実ファイルが見つからない場合 (ファイル削除)
            FileScanner->>DatabaseManager: mark_book_as_deleted(book_id)
            activate DatabaseManager
            DatabaseManager-->>FileScanner: 成功/失敗
            deactivate DatabaseManager
        end
    end

    FileScanner-->>MainWindow: 同期完了通知
    deactivate FileScanner
    MainWindow-->>User: 同期完了メッセージ表示
    deactivate MainWindow
```

### 2.1. 説明

- **User**: アプリケーションの利用者です。
- **MainWindow**: アプリケーションのメインウィンドウです。同期処理のトリガーとなります。
- **FileScanner**: ファイルシステムを走査し、ファイルとデータベースの同期ロジックを管理します。
- **FileNameParser**: ファイル名から書籍情報を抽出する役割を担います。
- **DatabaseManager**: データベースへのアクセスと操作を管理します。

このシーケンス図は、ユーザーが同期ボタンをクリックしてから、ファイルのスキャン、解析、データベースの更新、そして結果の通知までの一連の流れを示しています。
