## アプリ概要　スノトラ 

<img alt="スノトラ" width="512" height="512" alt="Copilot_20250712_145904" src="https://github.com/user-attachments/assets/a88c08d1-2152-4761-ab26-597ce1c1e8c1" />


このWebアプリケーションは、スキーインストラクターと受講者が予約マッチングできるサービスです。

## サービスのURL
このサービスの運用は、10時 ~ 18時の時間帯を目安に起動しています。(それ以降の時間帯はアクセスできません)<br>
アカウントを作成する必要がありますが、どんな機能を実装しているのかを把握したい場合は下の方にある「機能一覧」からGIFで確認が可能です💁‍♀️<br>

またこちらはデモ版を想定しており、2025年12月ごろにサービスとして本格的にリリース予定しています。

- 受講者側の新規画面︎：<https://snowtor.click/signup/student><br>
- インストラクター側の新規画面︎：<https://snowtor.click/signup/instructor>

## サービス開発の経緯
スキーインストラクターとして働いていた際、紙ベースの受付業務や受講生管理の煩雑さを実感しました。
この実体験から、アプリケーション化によって業務効率化を図れると考え、開発に取り組みました。

## 機能一覧
### 新規登録画面とログイン画面の動作
![sign-to-login](https://github.com/user-attachments/assets/c9784d3a-cccf-43f0-b3b3-1c09357d1a5a)
- [x] インストラクター、受講者とともにアカウントの新規作成、ログイン機能があります。

### 受講者のヘッダー機能
![student-header](https://github.com/user-attachments/assets/3cca8a70-e23a-486c-8900-792ea39f8622)
- [x] 「探す」では、レッスンの検索が可能です。
- [x] 「履歴」では、レッスンの履歴を閲覧できます。 

### インストラクターのヘッダー機能
![instructor-header](https://github.com/user-attachments/assets/3f945f2c-6a8a-4058-abf1-af8ead168ef9)
- [x] 「日程調整」では、レッスンの場所や、料金などの詳細情報を設定できます。
- [x] 「履歴」では、各レッスンの履歴を確認することが可能です。 

### インストラクターのレッスン予約
![instructor-lesson-detail](https://github.com/user-attachments/assets/b43d48e4-f94b-407f-a220-95ab35aa68cb)
インストラクターがレッスンの予約をする工程です。
- [x] レッスン日 (自由に設定可能)
- [x] レッスン場所 (あらかじめ用意したエリアのみ対応)
- [x] アクティビティタイプ (スキー、スノーボード)
- [x] レベルの設定 (初心者、中級者、上級者の３択)
- [x] レッスン形態 (プライベートのみ)
- [x] 最大受講人数 (自由に設定可能) 
- [x] 時間帯 (午前、午後、1日の３択)
- [x] 料金 (自由に設定可能)

### 受講生のレッスン検索
![student-resarch](https://github.com/user-attachments/assets/e73aac26-4373-457e-a5ad-ac66e0ee3d03)
- [x] レッスン日
- [x] レッスン場所
- [x] アクティビティタイプ
- [x] レッスン形態
- [x] 時間帯    

### Stripe決済(テスト用)
![stripe-fuction](https://github.com/user-attachments/assets/7e25c795-d85b-4080-b21b-dcf3905204e5)
- [x] テスト用の決済が可能

### インストラクター側のレッスンキャンセル
![cancel-lesson](https://github.com/user-attachments/assets/75426143-7d00-4288-8f47-e97874314155)
- [x] 受講者が 1人もいない場合は、すぐ「削除」可能
- [x] 受講者が 1人でもいる場合は、確認アラート表示してから「削除」または「キャンセル」可能

### 受講者側のレッスンキャンセル
![cancel-student](https://github.com/user-attachments/assets/bc10691f-e056-4816-8c92-c896a207f6ad)
- [x] すぐにキャンセルすることが可能です

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

## ER図
![snowtor_ER (1)](https://github.com/user-attachments/assets/4d077139-d937-4485-a5d0-fb97f81ecd45)


## 今後の展望
1. 機能アップデート ( 評価機能、検索機能の拡張性、本人確認書アップロード機能、管理者機能 )
2. 最新情報を知らせる通知機能
3. 作業ログの記録と分析の共有
