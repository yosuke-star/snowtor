## アプリ概要　スノトラ 
スキーインストラクターと受講者が予約マッチングできるサービスです
## 利用者向け

<プレゼン資料差し込み>

このWEBアプリは、ユーザーがカフェ情報共有・探索し、作業効率を記録・分析できる便利なプラットフォーム

## サービスのURL

ゲストログインから登録なしで、全ての機能が試せます。お気軽にお試しください。（ユーザーアカウント登録必須）
<url>

## サービス開発の経緯
スキーインストラクターとして働いていた際、紙ベースの受付業務や受講生管理の煩雑さを実感しました。
この実体験から、アプリケーション化によって業務効率化を図れると考え、開発に取り組みました。

## 機能一覧
**新規登録画面とログイン画面の動作**
![sign-to-login](https://github.com/user-attachments/assets/c9784d3a-cccf-43f0-b3b3-1c09357d1a5a)

**受講生のヘッダー機能**
![student-header](https://github.com/user-attachments/assets/3cca8a70-e23a-486c-8900-792ea39f8622)

**インストラクターのヘッダー機能**
![instructor-header](https://github.com/user-attachments/assets/3f945f2c-6a8a-4058-abf1-af8ead168ef9)

**インストラクターのレッスン予約**
![instructor-lesson-detail](https://github.com/user-attachments/assets/b43d48e4-f94b-407f-a220-95ab35aa68cb)




## 使用技術
以下、今回開発に使用した技術になります。
### フロントエンド
- 言語：JavaScript
- スタイル：Tailwind CSS
- 動的操作：Alpine.js

### バックエンド
- 言語：Python
- データベース：PostgreSQL
- 決済機能：Stripe

### インフラ・ホスティング
- AWS : EC2, RDS, ALB
- 環境構築：Docker

### 開発・設計ツール
- IDE：Cursor
- バージョン管理：Git, GitHub
- デザインカンプ：Figma
- ER図：Miro

**システム構成図**

<一枚の絵>

**ER図**

<一枚の絵>

## 今後の展望
1. 機能アップデート ( 評価機能、検索機能の拡張性、本人確認書アップロード機能、管理者機能 )
2. 最新情報を知らせる通知機能
3. 作業ログの記録と分析の共有
