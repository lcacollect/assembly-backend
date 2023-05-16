import argparse
import asyncio
import logging.config
import os
import sys
from pathlib import Path

from import_data import ecoplatform, okobau

logging.config.fileConfig(str(Path(__file__).parents[1] / "logging.conf"), disable_existing_loggers=False)

argparser = argparse.ArgumentParser(description="Import EPD data")
argsubparsers = argparser.add_subparsers(title="Commands", dest="command")
argsp = argsubparsers.add_parser("oko", help="Ökobau")
argsp.add_argument("count", metavar="count", default=None, nargs="?")
argsp = argsubparsers.add_parser("eco", help="EcoPlatform")
argsp.add_argument("count", metavar="count", default=None, nargs="?")


async def main(args):
    if args.command == "oko":
        if args.count == -1:
            await okobau.import_data(limit=None)
        elif args.count is None:
            await okobau.import_data()
        else:
            await okobau.import_data(limit=int(args.count))
    elif args.command == "eco":
        if args.count == -1:
            await ecoplatform.import_data(token=os.getenv("ECOPLATFORM_TOKEN"), limit=None)
        elif args.count is None:
            await ecoplatform.import_data(token=os.getenv("ECOPLATFORM_TOKEN"))
        else:
            await ecoplatform.import_data(token=os.getenv("ECOPLATFORM_TOKEN"), limit=int(args.count))
    else:
        print(f"No command with that name: {args.command}")


if __name__ == "__main__":
    argv = sys.argv[1:]
    _args = argparser.parse_args(argv)
    asyncio.run(main(_args))
