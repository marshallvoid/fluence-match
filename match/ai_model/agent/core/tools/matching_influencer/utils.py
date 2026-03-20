import pandas as pd


def bucketize_followers(num_followers: int) -> str:
    """
    Assigns a follower-count bucket label based on predefined ranges.
    """
    # each tuple: (inclusive_lower_bound, exclusive_upper_bound, label)
    buckets = [
        (1_000, 5_000, "1k - 5k followers"),
        (5_000, 10_000, "5k - 10k followers"),
        (10_000, 50_000, "10k - 50k followers"),
        (50_000, 100_000, "50k - 100k followers"),
        (100_000, 150_000, "100k - 150k followers"),
        (150_000, 200_000, "150k - 200k followers"),
        (200_000, 300_000, "200k - 300k followers"),
        (300_000, 500_000, "300k - 500k followers"),
        (500_000, 1_000_000, "500k - 1M followers"),
        (1_000_000, 2_000_000, "1M - 2M followers"),
        (2_000_000, 3_000_000, "2M - 3M followers"),
        (3_000_000, 5_000_000, "3M - 5M followers"),
    ]

    for lower, upper, label in buckets:
        if lower <= num_followers < upper:
            return label

    return "5M+ followers"


def calc_followers_bucket(row: pd.Series) -> str:
    num_followers = row["total_followers"]
    output = bucketize_followers(num_followers)
    return output
