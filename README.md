# SteamLibraryCompare
A small script to compare multiple Steam user libraries. Accepts both Steam IDs and custom vanity URL IDs.

All users will need to have their Steam profiles and game lists be publicly visible. On Steam, set "Edit Profle" -> "Privacy Settings" -> "Game details" to "Public".

# Usage
```
> main.py --help
usage: main.py [-h] user_id [user_id ...]

Compare Steam libraries

positional arguments:
  user_id     list of Steam User IDs

options:
  -h, --help  show this help message and exit
```