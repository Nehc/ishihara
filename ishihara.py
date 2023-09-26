import os, math, random, sys, colorsys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

TOTAL_CIRCLES = 1500
MIN_D, MAX_D = 1/200, 1/75
BACKGROUND = (254, 250, 235)

color = lambda c: ((c >> 16) & 255, (c >> 8) & 255, c & 255)

COLORS_OFF = [color(0x958038), color(0xB39D4F), color(0xCEB567)]
COLORS_ON_D = [color(0x88855E), color(0xD3C18A)]
COLORS_ON_N =  [color(0xC66535), color(0xE79569)]
COLORS_ON_A =  [color(0xCD7706D), color(0xD79780)]

def change_saturation(r, g, b, factor):
    h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    s = max(0.0, min(1.0, s * factor)) # Изменяем насыщенность
    new_rgb_color = tuple( # Преобразуем HSV обратно в RGB
                          map(lambda c:int(c * 255),
                              colorsys.hsv_to_rgb(h, s, v)
                             )
                          )
    return new_rgb_color


def tti(text, size=None):
    if size: 
      image = Image.new('RGB', size, 'white')
    else:  
      image = Image.new('RGB', (200,200), 'white')

    draw = ImageDraw.Draw(image)
    #font = ImageFont.load_default()
    font = ImageFont.truetype('tahoma.ttf', 200)
    text_width, text_height = draw.textsize(text, font=font)

    if size:
      if text_width>text_height:
        font = ImageFont.truetype('tahoma.ttf', int(size[0]*200/(text_width*1.1)))
      else:
        font = ImageFont.truetype('tahoma.ttf', int(size[1]*200/(text_height)))

      text_width, text_height = draw.textsize(text, font=font)
    else:
      size = (text_width, text_height)
      image = Image.new('RGB', size, 'white')
      draw = ImageDraw.Draw(image)

    # Вычисляем позицию для центрирования текста
    x = (size[0] - text_width) // 2
    y = (size[1] - int(text_height*1.1)) // 2

    # Рисуем текст на изображении
    draw.text((x, y), text, font=font, fill='black',align='center')

    return image


def generate_circle(image_width, image_height, 
                    min_diameter, max_diameter,
                    round = False):
    radius = random.triangular(min_diameter, max_diameter,
                               max_diameter * 0.8 + min_diameter * 0.2) / 2
    angle = random.uniform(0, math.pi * 2)

    if round:
      distance_from_center = random.uniform(0, image_width * 0.48 - radius)
      x = image_width  * 0.5 + math.cos(angle) * distance_from_center
      y = image_height * 0.5 + math.sin(angle) * distance_from_center
    else:
      x = random.uniform(radius, image_width - radius)  
      y = random.uniform(radius, image_height - radius)  

    return x, y, radius


def overlaps_motive(image, circle):
    x, y, r = circle
    points_x = [x, x, x, x-r, x+r, x-r*0.93, x-r*0.93, x+r*0.93, x+r*0.93]
    points_y = [y, y-r, y+r, y, y, y+r*0.93, y-r*0.93, y+r*0.93, y-r*0.93]

    for xy in zip(points_x, points_y):
        if image.getpixel(xy)[:3] != (255, 255, 255):
            return True

    return False


def circle_intersection(circle1, circle2):
    x1, y1, r1 = circle1
    x2, y2, r2 = circle2
    return (x2 - x1)**2 + (y2 - y1)**2 < (r2 + r1)**2


def circle_draw(draw_image, imageN, imageS, circle, saturation=1):
    if overlaps_motive(imageN, circle) and overlaps_motive(imageS, circle):
        fill_colors = COLORS_ON_A
    elif overlaps_motive(imageN, circle):
        fill_colors = COLORS_ON_N
    elif overlaps_motive(imageS, circle):
        fill_colors = COLORS_ON_D
    else:
        fill_colors = COLORS_OFF
    fill_color = random.choice(fill_colors)
    fill_color = change_saturation(*fill_color, saturation)
    x, y, r = circle
    draw_image.ellipse((x - r, y - r, x + r, y + r),
                       fill=fill_color,
                       outline=fill_color)

def Generator(normalImage, secretImage, saturation=1, size=None):
    if os.path.isfile(normalImage): 
        image_n = Image.open(normalImage).convert('RGB')
        if not size: size = image_n.size
    else: 
        image_n = tti(normalImage, size)
    if os.path.isfile(secretImage):  
        image_s = Image.open(secretImage).convert('RGB')
    else: 
        image_s = tti(secretImage, size)
    image_r = Image.new('RGB', image_n.size, BACKGROUND)
    d = ImageDraw.Draw(image_r)
    width, height = image_n.size
    min_diameter = (width + height) * MIN_D
    max_diameter = (width + height) * MAX_D
    circle = generate_circle(width, height, min_diameter, max_diameter)
    circles = [circle]
    circle_draw(d, image_n, image_s, circle, saturation)
    try:
        for i in range(TOTAL_CIRCLES):
            tries = 0
            while any(circle_intersection(circle, circle2) for circle2 in circles):
                tries += 1
                circle = generate_circle(width, height, min_diameter, max_diameter)
            circles.append(circle)
            circle_draw(d, image_n, image_s, circle, saturation)
    except (KeyboardInterrupt, SystemExit): pass

    return image_r.filter(ImageFilter.GaussianBlur(radius=1))
