from PIL import Image, ImageDraw, ImageFont
import os
import pathlib

PATH = pathlib.Path.cwd()


def text_on_img(trade, color_choice):
    #wrapped_text = textwrap.wrap(text, width=800)
    (in_or_out, ticker, datetime, strike_price, call_or_put, buy_price,
     user_name, expiration) = trade
    expiration = expiration.replace(r'/', '.')
    text = f'We are going\n {in_or_out.upper()} on {ticker.upper()}\n Strike price: {strike_price.upper()}\n {call_or_put.upper()} Price: {buy_price}\n Expiration: {expiration}'
    filename = f'{in_or_out}.{ticker}.{strike_price}.{call_or_put}.{expiration}.png'
    my_font = ImageFont.truetype('micross.ttf', 180)
    # create image
    max_w, max_h = (1080, 1080)
    image = Image.new("RGBA", (max_w, max_h), color_choice)
    draw = ImageDraw.Draw(image)
    w, h = draw.multiline_textsize(text, font=my_font)
    # draw text
    draw.multiline_text((0, 0),
                        text,
                        fill='black',
                        font=my_font,
                        spacing=4,
                        align='center')
    # save file
    image.save(filename)
    return filename
    # show file
    #os.system(filename)
