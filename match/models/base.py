from datetime import datetime
from uuid import uuid4

import pytz
from neomodel import AsyncStructuredNode, DateTimeProperty, StringProperty


class Node(AsyncStructuredNode):
    """
    An abstract base class for Neo4j nodes using neomodel's AsyncStructuredNode.

    Attributes:
        uuid (str): A unique identifier for the node, automatically generated using UUID4.
        created_at (datetime): The UTC timestamp indicating when the node was created.
    """

    __abstract_node__ = True

    uuid = StringProperty(unique_index=True, default=uuid4)
    created_at = DateTimeProperty(default=lambda: datetime.now(pytz.utc))
