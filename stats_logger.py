import csv
import os
import pandas as pd

# Filenames for the raw game results and the aggregated statistics.
CSV_FILE = "game_results.csv"
AGGREGATED_CSV_FILE = "aggregated_game_results.csv"

# Define the CSV header for individual game results.
HEADERS = [
    "ai_model",
    "games_played",
    "games_won",
    "games_losed",
    "win_rate",             # win_rate in percentage (0-100)
    "average_round_score",  # average point differential per round (could be negative)
    "tricks_played",
    "tricks_won",
    "tricks_losed",
    "trick_success_rate",   # percentage of tricks won (0-100)
    "tricks_per_game"
    # Add more columns here if needed.
]

def append_game_result(game_result: dict):
    """
    Appends a finished game result (provided as a dictionary) to the CSV file.
    After appending, automatically updates aggregated statistics.
    
    Parameters:
        game_result (dict): A dictionary containing game result fields,
                            which should adhere to the HEADERS.
    """
    file_exists = os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=HEADERS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(game_result)
    
    # Update aggregated statistics automatically after appending the new game result.
    update_aggregated_stats()

def update_aggregated_stats():
    """
    Reads the raw game results from CSV_FILE, aggregates the statistics
    by ai_model, and writes the aggregated data to AGGREGATED_CSV_FILE.
    
    For each ai_model, the following is computed:
        - Sum of games_played, games_won, games_losed, tricks_played, tricks_won, tricks_losed.
        - win_rate = (total games won / total games played) * 100.
        - average_round_score = mean(average_round_score) from each game.
        - trick_success_rate = (total tricks won / total tricks played) * 100.
        - tricks_per_game = total tricks played / games played.
    """
    if not os.path.exists(CSV_FILE):
        return  # Nothing to aggregate if the file doesn't exist.

    df = pd.read_csv(CSV_FILE)
    if df.empty:
        return  # No data to aggregate.

    # Aggregate basic counts and averages by ai_model.
    aggregated = df.groupby("ai_model").agg(
        games_played=("games_played", "sum"),
        games_won=("games_won", "sum"),
        games_losed=("games_losed", "sum"),
        average_round_score=("average_round_score", "mean"),
        tricks_played=("tricks_played", "sum"),
        tricks_won=("tricks_won", "sum"),
        tricks_losed=("tricks_losed", "sum")
    ).reset_index()

    # Recalculate derived metrics:
    aggregated["win_rate"] = aggregated["games_won"] / aggregated["games_played"] * 100
    aggregated["trick_success_rate"] = (
        aggregated["tricks_won"] / aggregated["tricks_played"] * 100
    ).fillna(0)  # Avoid division by zero.
    aggregated["tricks_per_game"] = aggregated["tricks_played"] / aggregated["games_played"]

    # Rearranging columns in a desired order.
    aggregated = aggregated[[
        "ai_model", "games_played", "games_won", "games_losed", "win_rate",
        "average_round_score", "tricks_played", "tricks_won", "tricks_losed",
        "trick_success_rate", "tricks_per_game"
    ]]

    # Write the aggregated statistics to a new CSV file.
    aggregated.to_csv(AGGREGATED_CSV_FILE, index=False)