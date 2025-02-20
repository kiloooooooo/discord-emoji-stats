import collections
import csv


def export_emoji_counts_to_csv(emoji_counts, filename="emoji_counts.csv"):
    """
    emoji_countsをCSVファイルに書き出す関数
    """
    try:
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["絵文字", "カウント"])  # ヘッダーを書き込む
            for emoji, count in emoji_counts.items():
                writer.writerow([emoji, count])
        print(f"絵文字のカウントを {filename} に書き出しました。")
    except Exception as e:
        print(f"エラー: CSVファイルへの書き出しに失敗しました。エラー内容: {e}")


def load_emoji_counts_from_csv(filename):
    """
    CSVファイルからemoji_countsを読み込む関数
    """
    try:
        with open(filename, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.reader(file)
            next(reader)  # ヘッダーをスキップ
            loaded_counts = collections.Counter()
            for row in reader:
                emoji = row[0]
                count = int(row[1])
                loaded_counts[emoji] = count
        print(f"絵文字のカウントを {filename} から読み込みました。")
        return loaded_counts
    except FileNotFoundError:
        print(f"ファイル {filename} が見つかりませんでした。")
        return collections.Counter()  # 空のCounterを返す
    except Exception as e:
        print(f"エラー: CSVファイルからの読み込みに失敗しました。エラー内容: {e}")
        return collections.Counter()
