import collections
import csv
import glob


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


def load_emoji_counts_from_csv():
    emoji_counts = {}
    for filename in glob.glob("*.csv"):
        server_id = filename.split(".")[1]
        emoji_counts[int(server_id)] = _load_emoji_counts_from_csv(filename)
    return emoji_counts


def _load_emoji_counts_from_csv(filename):
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


def get_top_n_range(counter, start_rank, end_rank):
    """
    collections.Counterオブジェクトから指定した順位範囲の要素を抽出する関数

    Args:
        counter (collections.Counter): 集計結果のCounterオブジェクト
        start_rank (int): 抽出を開始する順位（1始まり）
        end_rank (int): 抽出を終了する順位（含む）

    Returns:
        list: 指定した順位範囲の(要素, カウント)のタプルのリスト
    """
    if start_rank is None:
        start_rank = 1

    if end_rank is None:
        end_rank = len(counter) + 1

    if start_rank <= 0 or end_rank <= 0 or start_rank > end_rank:
        return []  # 無効な順位範囲の場合は空のリストを返す

    sorted_items = counter.most_common()
    if not sorted_items:
        return []  # Counterが空の場合も空のリストを返す。

    # 順位をリストのインデックスに変換（0始まり）
    start_index = start_rank - 1
    end_index = end_rank

    # リストの範囲を超えないように調整
    start_index = max(0, start_index)
    end_index = min(len(sorted_items), end_index)

    return sorted_items[start_index:end_index]
