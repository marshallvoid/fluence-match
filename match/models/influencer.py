from neomodel import IntegerProperty, StringProperty

from match.models.base import Node


class Influencer(Node):
    """Represents an influencer in the system."""

    __label__ = "Influencer"

    uid = StringProperty(max_length=255, unique_index=True, help_text="Unique user identifier")
    sec_uid = StringProperty(max_length=255, unique_index=True, help_text="Secondary unique identifier")
    unique_id = StringProperty(max_length=255, unique_index=True, help_text="Public-facing username or handle")
    nickname = StringProperty(max_length=255, help_text="Display name or nickname")

    region = StringProperty(max_length=255, help_text="Geographic region or location")
    signature = StringProperty(max_length=255, help_text="Bio or personal description")

    total_videos = IntegerProperty(default=0, help_text="Total number of videos published")
    total_followings = IntegerProperty(default=0, help_text="Total number of accounts followed")
    total_followers = IntegerProperty(default=0, help_text="Total number of followers")
    total_favorites = IntegerProperty(default=0, help_text="Total number of likes/favorites received")
