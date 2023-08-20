from random import randint, uniform
import numpy as np


def get_color(annotation):
    # rectangle, circle
    return annotation.get_edgecolor()


def set_edge_color(annotation, color):
    # rectangle, circle
    annotation.set_edgecolor(color)


def set_edge_thick(annotation, line_width=1):
    annotation.set_linewidth(line_width)


def random_bright_color() -> str:
    # 랜덤한 RGB 값을 생성합니다.
    red = randint(0, 255)
    green = randint(0, 255)
    blue = randint(0, 255)

    # 밝기 조정을 위한 랜덤한 계수를 생성합니다.
    brightness_factor = uniform(0.5, 1.0)  # 0.5부터 1.0 사이의 값을 가집니다.

    # RGB 값에 밝기 조정을 적용합니다.
    red = int(red * brightness_factor)
    green = int(green * brightness_factor)
    blue = int(blue * brightness_factor)

    # RGB 값을 16진수 색상 코드로 변환합니다.
    return "#{:02x}{:02x}{:02x}".format(red, green, blue)


def get_rectangle_coords(start, end):
    width = abs(start[0] - end[0])
    height = abs(start[1] - end[1])
    x = min(start[0], end[0])
    y = min(start[1], end[1])
    return (x, y), width, height


def get_circle_coords(start, end):
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    center = start
    radius = np.sqrt(dx ** 2 + dy ** 2)
    return center, radius


def get_line_coords(start, end):
    x = [start[0], end[0]]
    y = [start[1], end[1]]
    return x, y


def get_freehand_coords(points):
    return zip(*points)


def get_ractangle_annotation_info(an):
    """
    Retruns:
        (라벨명, (x, y), w, h, 컬러값)
    """
    return an.get_label(), (an.xy, an.get_width(), an.get_height()), get_color(an)


def get_line_annotation_info(an):
    """
    Retruns:
        (라벨명, (x, y), 컬러값)
    """
    data = an.get_data()
    ret_points = [(data[0][i], data[1][i]) for i in range(len(data[0]))]
    return an.get_label(), ret_points, get_color(an)


def get_circle_annotation_info(an):
    """
    Retruns:
        (라벨명, (center, radius), 컬러값)
    """
    return an.get_label(), (an.get_center(), an.get_radius()), get_color(an)
