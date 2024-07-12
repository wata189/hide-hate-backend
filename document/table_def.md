# user
|論理名         |物理名         |型       |PK |null可 |UK   |備考   |
|ユーザID       |id             |string   |◯ |×     |◯   |       |
|名前           |name           |string   |× |×     |×   |       |
|アイコンパス   |icon_path      |string   |× |◯     |◯   |       |
|メールアドレス |email          |string   |× |×     |◯   |       |
|パスワード     |hashed_password|string   |× |×     |×   |       |
|作成日時       |create_at      |timestamp|× |×     |×   |       |
|作成ユーザID   |create_user_id |string   |× |×     |×   |batchとかsystemとかいれる想定？なのでFKはなし|
|更新日時       |update_at      |timestamp|× |×     |×   |       |
|更新ユーザID   |update_user_id |string   |× |×     |×   |batchとかsystemとかいれる想定？なのでFKはなし|

# post
|論理名         |物理名         |型       |PK |null可 |UK   |備考   |
|ユーザID       |user_id        |string   |× |×     |×   |userテーブルにFK|
|内容           |content        |string   |× |×     |×   |       |
|ヘイトフラグ   |may_hate       |boolean  |× |×     |×   |       |
|作成日時       |create_at      |timestamp|× |×     |×   |       |
|作成ユーザID   |create_user_id |string   |× |×     |×   |batchとかsystemとかいれる想定？なのでFKはなし|
|更新日時       |update_at      |timestamp|× |×     |×   |       |
|更新ユーザID   |update_user_id |string   |× |×     |×   |batchとかsystemとかいれる想定？なのでFKはなし|
