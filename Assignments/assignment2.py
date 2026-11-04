import random
import time

from OpenGL.GL import *
from OpenGL.GLUT import *

#midpoint algo

def get_zone(dx, dy):
    if dx == 0 and dy == 0:
        # Both points are the same which means no direction or zones needed
        return None

    if abs(dx) >= abs(dy):
        # horizontal-ish line
        if dx >= 0 and dy >= 0:
            return 0
        elif dx < 0 and dy >= 0:
            return 3
        elif dx < 0 and dy < 0:
            return 4
        else:
            return 7
    else:
        # vertical-ish line
        if dx >= 0 and dy > 0:
            return 1
        elif dx < 0 and dy > 0:
            return 2
        elif dx < 0 and dy <= 0:
            return 5
        else:
            return 6


def zone0(x, y, zone):
    if zone == 0:
        return (x, y)
    if zone == 1:
        return (y, x)
    if zone == 2:
        return (y, -x)
    if zone == 3:
        return (-x, y)
    if zone == 4:
        return (-x, -y)
    if zone == 5:
        return (-y, -x)
    if zone == 6:
        return (-y, x)
    if zone == 7:
        return (x, -y)
    raise ValueError("Invalid zone: " + str(zone))


def original_zone(x, y, zone):
    if zone == 0:
        return (x, y)
    if zone == 1:
        return (y, x)
    if zone == 2:
        return (-y, x)
    if zone == 3:
        return (-x, y)
    if zone == 4:
        return (-x, -y)
    if zone == 5:
        return (-y, -x)
    if zone == 6:
        return (y, -x)
    if zone == 7:
        return (x, -y)
    raise ValueError("Invalid zone: " + str(zone))


def midpoint(x1, y1, x2, y2):
    point = []

    dx = x2 - x1
    dy = y2 - y1

    d = 2 * dy - dx
    east = 2 * dy
    northeast = 2 * (dy - dx)

    xaxis = x1
    yaxis = y1

    while xaxis <= x2:
        point.append((xaxis, yaxis))
        if d > 0:
            d = d + northeast
            yaxis = yaxis + 1
        else:
            d = d + east
        xaxis = xaxis + 1

    return point


def midpoint_line(x1, y1, x2, y2):
    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
    if (x1 > x2) or (x1 == x2 and y1 > y2):
        x1, y1, x2, y2 = x2, y2, x1, y1

    dx = x2 - x1
    dy = y2 - y1

    if dx == 0 and dy == 0:
        return [(x1, y1)]

    zone = get_zone(dx, dy)
    end_x, end_y = zone0(dx, dy, zone)
    raw = midpoint(0, 0, end_x, end_y)

    points = []
    for (px, py) in raw:
        ox, oy = original_zone(px, py, zone)
        points.append((x1 + ox, y1 + oy))

    return points


# GAME 

width = 500
height = 700

catchercolor = (1.0, 1.0, 1.0)    # white
gameovercolour = (1.0, 0.0, 0.0)  # red

diamondcolour = [
    (1.0, 1.0, 0.0),   # yellow
    (0.0, 1.0, 1.0),   # cyan
    (1.0, 0.2, 0.8),   # pink
    (0.4, 1.0, 0.4),   # light green
    (1.0, 0.6, 0.0),   # orange
    (0.6, 0.6, 1.0),   # light purple
]

catchertop = 55       
catcherbottom = 30    
catcherheight = 25  
catcheredge = 60      
speed = 260           

# diamond shape 

diaheight = 18
diawidth = 12
diaspeed = 90         # starting falling speed
acceleration = 6      # speeds the game up gradually over time
hit = 20              # if the diamond falls below this y, it's a miss


button_min = height - 70
button_max = height - 20
left = (20, button_min, 90, button_max)
pausebtn = (width // 2 - 35, button_min, width // 2 + 35, button_max)
esc = (width - 90, button_min, width - 20, button_max)

teal = (0.0, 0.8, 0.8)
amber = (1.0, 0.75, 0.0)
red = (1.0, 0.0, 0.0)


catcher_x = width / 2.0
catcher_color = catchercolor

diamond_x = width / 2.0
diamond_y = height - 60
diamond_color = random.choice(diamondcolour)
diamond_speed = diaspeed
diamond_visible = True

score = 0
gameover = False
paused = False
cheat = False

left_pressed = False
right_pressed = False
left_last = 0.0
right_last = 0.0
KEY_TIMEOUT = 0.15   # seconds - if no new key-down event arrives within
                     # this long, we treat the key as released. Works
                     # because the OS keeps re-firing glutSpecialFunc
                     # while a key is held down (key auto-repeat).

latesttime = None


def plot_points(points, color):
    glColor3f(color[0], color[1], color[2])
    glBegin(GL_POINTS)
    for (x, y) in points:
        glVertex2f(x, y)
    glEnd()


def line(x1, y1, x2, y2, color):
    points = midpoint_line(x1, y1, x2, y2)
    plot_points(points, color)


def diamond(cx, cy, color):
    # Diamond using 4 midpoint lines.
    top = (cx, cy + diaheight)
    right = (cx + diawidth, cy)
    bottom = (cx, cy - diaheight)
    left_pt = (cx - diawidth, cy)

    line(top[0], top[1], right[0], right[1], color)
    line(right[0], right[1], bottom[0], bottom[1], color)
    line(bottom[0], bottom[1], left_pt[0], left_pt[1], color)
    line(left_pt[0], left_pt[1], top[0], top[1], color)


def catcher(cx, color):
    # We draw the catcher using 4 midpoint lines.
  
    top_left = (cx - catchertop, catcheredge + catcherheight)
    top_right = (cx + catchertop, catcheredge + catcherheight)
    bottom_right = (cx + catcherbottom, catcheredge)
    bottom_left = (cx - catcherbottom, catcheredge)

    line(top_left[0], top_left[1], top_right[0], top_right[1], color)             # top edge
    line(top_right[0], top_right[1], bottom_right[0], bottom_right[1], color)     # right slant
    line(bottom_right[0], bottom_right[1], bottom_left[0], bottom_left[1], color) # bottom edge
    line(bottom_left[0], bottom_left[1], top_left[0], top_left[1], color)         # left slant


def leftarrow():
    x1, y1, x2, y2 = left
    mid_y = (y1 + y2) / 2
    # shaft of the arrow
    line(x2 - 15, mid_y, x1 + 20, mid_y, teal)
    # arrow head (two diagonal lines)
    line(x1 + 20, mid_y, x1 + 35, y2 - 8, teal)
    line(x1 + 20, mid_y, x1 + 35, y1 + 8, teal)


def pause():
    x1, y1, x2, y2 = pausebtn
    mid_x = (x1 + x2) / 2
    # pause icon: two vertical bars
    line(mid_x - 10, y1 + 8, mid_x - 10, y2 - 8, amber)
    line(mid_x + 10, y1 + 8, mid_x + 10, y2 - 8, amber)


def play():
    x1, y1, x2, y2 = pausebtn
    mid_y = (y1 + y2) / 2
    # play icon: a triangle pointing right
    line(x1 + 15, y1 + 8, x1 + 15, y2 - 8, amber)
    line(x1 + 15, y2 - 8, x2 - 12, mid_y, amber)
    line(x2 - 12, mid_y, x1 + 15, y1 + 8, amber)


def quit():
    x1, y1, x2, y2 = esc
    line(x1 + 8, y1 + 8, x2 - 8, y2 - 8, red)
    line(x1 + 8, y2 - 8, x2 - 8, y1 + 8, red)


def buttons():
    leftarrow()
    if paused:
        play()
    else:
        pause()
    quit()


def catcherbox():
    return (
        catcher_x - catchertop,
        catcheredge,
        catcher_x + catchertop,
        catcheredge + catcherheight,
    )


def diabox():
    return (
        diamond_x - diawidth,
        diamond_y - diaheight,
        diamond_x + diawidth,
        diamond_y + diaheight,
    )


def box(box1, box2):
    x1_min, y1_min, x1_max, y1_max = box1
    x2_min, y2_min, x2_max, y2_max = box2
    return (x1_min < x2_max and x1_max > x2_min and
            y1_min < y2_max and y1_max > y2_min)


def newdiamond():
    global diamond_x, diamond_y, diamond_color, diamond_visible
    margin = diawidth + 10
    diamond_x = random.randint(margin, width - margin)
    diamond_y = height - 40
    diamond_color = random.choice(diamondcolour)
    diamond_visible = True


def restart():
    global score, diamond_speed, gameover, catcher_x, catcher_color, paused
    score = 0
    diamond_speed = diaspeed
    gameover = False
    paused = False
    catcher_x = width / 2.0
    catcher_color = catchercolor
    newdiamond()
    print("Starting Over")


def boxpoint(px, py, box_coords):
    x_min, y_min, x_max, y_max = box_coords
    return x_min <= px <= x_max and y_min <= py <= y_max


def display():
    glClear(GL_COLOR_BUFFER_BIT)

    buttons()
    catcher(catcher_x, catcher_color)
    if diamond_visible:
        diamond(diamond_x, diamond_y, diamond_color)

    glutSwapBuffers()


def idle():
    global latesttime, catcher_x, diamond_y, diamond_speed
    global diamond_visible, gameover, catcher_color, score
    global left_pressed, right_pressed

    now = time.time()
    if latesttime is None:
        latesttime = now
    dt = now - latesttime
    latesttime = now

   
    if now - left_last > KEY_TIMEOUT:
        left_pressed = False
    if now - right_last > KEY_TIMEOUT:
        right_pressed = False

    if not paused and not gameover:

        # moving the catcher
        if cheat:
           
            catch_line = catcheredge + catcherheight + diaheight
            remaining_distance = diamond_y - catch_line
            if remaining_distance > 0 and diamond_speed > 0:
                time_remaining = remaining_distance / diamond_speed
                required_speed = (diamond_x - catcher_x) / time_remaining
                catcher_x += required_speed * dt
            else:
                catcher_x = diamond_x
        else:
            if left_pressed:
                catcher_x -= speed * dt
            if right_pressed:
                catcher_x += speed * dt

        # keeping the catcher fully inside the screen 
        min_x = catchertop
        max_x = width - catchertop
        if catcher_x < min_x:
            catcher_x = min_x
        if catcher_x > max_x:
            catcher_x = max_x

       # speed the diamond + speed up the diamond
        diamond_speed += acceleration * dt
        diamond_y -= diamond_speed * dt

       
        if box(catcherbox(), diabox()):
            score += 1
            print("Score:", score)
            newdiamond()

        
        elif diamond_y - diaheight <= hit:
            diamond_visible = False
            gameover = True
            catcher_color = gameovercolour
            print("Game Over! Final Score:", score)

    glutPostRedisplay()


def keyboard(key, x, y):
    global cheat
    if key in (b'c', b'C'):
        cheat = not cheat
        print("Cheat Mode:", "on" if cheat else "off")


def down(key, x, y):
    global left_pressed, right_pressed, left_last, right_last
    if key == GLUT_KEY_LEFT:
        left_pressed = True
        left_last = time.time()
    elif key == GLUT_KEY_RIGHT:
        right_pressed = True
        right_last = time.time()


def mouse(button, state, x, y):
    global paused

    if button != GLUT_LEFT_BUTTON or state != GLUT_DOWN:
        return
    gl_y = height - y

    if boxpoint(x, gl_y, left):
        restart()
    elif boxpoint(x, gl_y, pausebtn):
        paused = not paused
    elif boxpoint(x, gl_y, esc):
        print("Goodbye! Final Score:", score).
        glutLeaveMainLoop()


def init_gl():
    glViewport(0, 0, width, height)
    glPointSize(2)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, width, 0, height, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def main():
    newdiamond()

    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
    glutInitWindowSize(width, height)
    glutCreateWindow(b"Catch the Diamonds!")

    init_gl()

    glutDisplayFunc(display)
    glutIdleFunc(idle)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(down)
    glutMouseFunc(mouse)

    glutMainLoop()


if __name__ == "__main__":
    main()