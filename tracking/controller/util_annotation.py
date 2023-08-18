from random import randint, uniform


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


def get_ractangle_annotation_info(an):
    """
    Retruns:
        (라벨명, (x, y), w, h, 컬러값)
    """
    return (an.get_label(), an.xy, an.get_width(), an.get_height(), get_color(an))
