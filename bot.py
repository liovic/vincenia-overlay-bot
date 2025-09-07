import discord
from discord.ext import commands
from PIL import Image
import io
import aiohttp
import os
from dotenv import load_dotenv


load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

OVERLAY_DIR = 'overlays'


def get_available_overlays():
    return [f for f in os.listdir(OVERLAY_DIR) if f.endswith('.png')]

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command(name='overlay')
async def overlay_image(ctx, overlay_name: str = None):
    if not overlay_name:
        available_overlays = get_available_overlays()
        if not available_overlays:
            await ctx.send("No overlays available! Add PNG files to the overlays directory.")
            return
        overlay_list = '\n'.join([f.replace('.png', '') for f in sorted(available_overlays)])
        await ctx.send(f"Please specify an overlay. Available overlays:\n{overlay_list}")
        return

    overlay_path = os.path.join(OVERLAY_DIR, f"{overlay_name}.png")
    if not os.path.exists(overlay_path):
        available_overlays = get_available_overlays()
        overlay_list = '\n'.join([f.replace('.png', '') for f in sorted(available_overlays)])
        await ctx.send(f"Overlay '{overlay_name}' not found. Available overlays:\n{overlay_list}")
        return

    if not ctx.message.attachments:
        await ctx.send("Please upload an image to overlay!")
        return

    attachment = ctx.message.attachments[0]
    if not attachment.filename.endswith(('.png', '.jpg', '.jpeg')):
        await ctx.send("Please upload a valid image (PNG, JPG, JPEG)!")
        return

    async with aiohttp.ClientSession() as session:
        async with session.get(attachment.url) as resp:
            if resp.status != 200:
                await ctx.send("Failed to download the image!")
                return
            image_data = await resp.read()

    try:
        user_image = Image.open(io.BytesIO(image_data)).convert('RGBA')
        overlay = Image.open(overlay_path).convert('RGBA')

        overlay = overlay.resize(user_image.size, Image.LANCZOS)
        result = Image.alpha_composite(user_image, overlay)

        output = io.BytesIO()
        result.save(output, format='PNG')
        output.seek(0)

        await ctx.send(file=discord.File(output, f'overlayed_{overlay_name}.png'))
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")

bot.run(os.getenv('TOKEN'))