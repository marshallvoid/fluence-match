def get_price(followers: int) -> float:
    """
    Calculate the price based on followers and engagement rate.
    """
    price_ranges = [
        (1000, 5000, 500_000),
        (5000, 10_000, 1_000_000),
        (10_000, 50_000, 1_900_000),
        (50_000, 100_000, 2_600_000),
        (100_000, 150_000, 3_000_000),
        (150_000, 200_000, 3_200_000),
        (200_000, 300_000, 5_500_000),
        (300_000, 500_000, 5_800_000),
        (500_000, 1_000_000, 9_000_000),
        (1_000_000, 2_000_000, 11_000_000),
    ]

    for lower, upper, price in price_ranges:
        if lower <= followers <= upper:
            return price

    return 0  # Default case for followers below 1k or above 2M
