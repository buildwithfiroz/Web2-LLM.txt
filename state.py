import sys
import os
import asyncio


engine_path = os.path.abspath(os.path.join("engine", "xengine"))
sys.path.insert(0, engine_path)


from Cengine import xengine

async def main():
    await xengine("https://example.com")

if __name__ == "__main__":
    asyncio.run(main())
