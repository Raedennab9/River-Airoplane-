"""Compatibility entry point for older shortcuts.

The asset and audio fixes now live in the complete game.
"""

import asyncio

from airplane_shooter_advanced import main


if __name__ == "__main__":
    asyncio.run(main())
