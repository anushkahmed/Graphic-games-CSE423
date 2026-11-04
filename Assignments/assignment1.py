from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import math
import time


# TASK 1: Building a House in Rainfall

width= 650
height =650

raindrops_number =115
angle= 0.0
max_angle= 7.5
raindrops= []

def init_raindrops():
    for i in range(raindrops_number):
        raindrops.append([random.uniform(-250, 250), random.uniform(250,260),
                          random.uniform(9,25), 
                          #length 
                          random.uniform(3,6),
                            #speed
                          ])
        
bright= 0.0
#dark = 0.0 but light is 1.0 ;>
bright_transition= 0.05

def rgbofsky():
    night= [0.06,0.06,0.15]
    day= [0.6,0.9,1.0]
    a= bright
    return (
        night[0] + (day[0]-night [0]) *a,
        night[1] + (day[1]-night[1]) *a,
        night [2] + (day[2]-night[2]) *a,
        )

def colour(nightcolor, daycolor):
    a= bright
    return tuple(nightcolor[i] + (daycolor[i] - nightcolor[i]) * a for i in range(3))

def point(x,y,size):
    glPointSize(size)
    glBegin(GL_POINTS)
    glVertex2f(x,y)
    glEnd()
    
def lines(x1, y1, x2, y2):
    glBegin(GL_LINES)
    glVertex2f(x1, y1)
    glVertex2f(x2, y2)
    glEnd()
 
def triangles(x1, y1, x2, y2, x3, y3):
    glBegin(GL_TRIANGLES)
    glVertex2f(x1, y1)
    glVertex2f(x2, y2)
    glVertex2f(x3, y3)
    glEnd()
 
def rectangles_2tri(l, b, r, t):    
    triangles(l, b, r, b, r, t)
    triangles(l, b, l, t, r, t)
 
def circle_tri(c_x, c_y, r, steps=24):
    for i in range(steps):
        a = math.radians(i       * 360 / steps)
        b = math.radians((i + 1) * 360 / steps)
        triangles(c_x, c_y,
            c_x + r * math.cos(a), c_y + r * math.sin(a),
            c_x + r * math.cos(b), c_y + r * math.sin(b))
 
def circlepoints(c_x, c_y, r, steps=36, sz=3):
    glPointSize(sz)
    glBegin(GL_POINTS)
    for i in range(steps):
        c = math.radians(i * 360 / steps)
        glVertex2f(c_x + r * math.cos(c), c_y + r * math.sin(c))
    glEnd()   

def house():
    wall= colour((0.8,0.6, 0.5), (0.62,0.45,0.34))
    roof= colour((0.88,0.3,0.3), (0.59, 0.14,0.10))
    door= colour((0.38, 0.22, 0.08), (0.24, 0.12, 0.04))
    window=colour((1.00, 0.95, 0.55), (0.55, 0.82, 0.97))  
    border= colour((0.18, 0.12, 0.08), (0.10, 0.07, 0.04))
    chimney= colour((0.58, 0.48, 0.38), (0.40, 0.30, 0.20))
    ground = colour((0.18, 0.42, 0.12), (0.14, 0.55, 0.14))

    glColor3f(*wall)
    rectangles_2tri(-82, -165, 82, -65)
 
    glColor3f(*roof)
    triangles(-98, -65, 97, -65, 0, 33)  
 
    glColor3f(*chimney)
    rectangles_2tri(30, -30, 50, 10)
 
    glColor3f(*door)
    rectangles_2tri(-23, -162, 23, -107)
 
    glColor3f(*window)
    rectangles_2tri(-67, -106, -37, -73)
    rectangles_2tri( 39, -107,  69, -73)
 
    # Window with bars
    glColor3f(*door)
    glLineWidth(1.5)
    lines(-67, -89, -35, -89);  lines(-52, -106, -52, -73)
    lines( 39, -89,  69, -89);  lines( 54, -107,  54, -73) 
    glLineWidth(1)

    glColor3f(*border)
    glLineWidth(1.5)
    lines(-82,-165, 82,-165); lines(-82,-165,-82,-65)
    lines( 82,-165, 82, -65); lines(-82,  -65, 82,-65)
    lines(-98,-65, 0, 33); lines(97,-65, 0, 33); lines(-98,-65, 97,-65)
    lines(30,-30,30,10); lines(50,-30,50,10); lines(30,10,50,10); lines(30,-30,50,-30)
    lines(-23,-165,-23,-107); lines(23,-165,23,-107); lines(-23,-107,23,-107)
    glLineWidth(1)
    

    #ground lines 

    glColor3f(*ground)
    glLineWidth(2)
    lines(-250, -167, 250, -167)
    glLineWidth(1)
 
    # Moon or Sun transition 

    if bright < 0.5:
        # Moon is filled like crecent shaped

        glColor3f(1.0, 1.0, 0.85)
        circle_tri(-183, 183, 23)
        r, g, b = rgbofsky()
        glColor3f(r, g, b)
        circle_tri(-176, 188, 16)

        # Stars drawing

        glColor3f(1.0, 1.0, 0.9)
        glPointSize(2)
        glBegin(GL_POINTS)
        for i, j in [(100,210),(-50,230),(150,190),(50,220),(-120,200),(180,215),(-10,240),(70,200),(-80,185)]:
            glVertex2f(i, j)
        glEnd()
    else:
        # drawing sun when we press d

        glColor3f(1.0, 0.9, 0.0)
        circle_tri(-185, 185, 26)
        # rays from the sun

        glColor3f(1.0, 0.75, 0.0)
        glLineWidth(2)
        for i in range(8):
            a = math.radians(i * 45)
            lines(-185 + 28*math.cos(a), 185 + 28*math.sin(a),
               -185 + 40*math.cos(a), 185 + 40*math.sin(a))
        glLineWidth(1)

#Now we draw the rains yaay

def rains():
    rain= colour((0.55, 0.78, 1.0), (0.10, 0.28, 0.72))
    glColor3f(*rain)
    glLineWidth(1.5)
    for x, y, length, _ in raindrops:
        slopex = x + angle * (length / 12.0)
        slopey = y - length
        lines(x, y, slopex, slopey)
    glLineWidth(1)

#rain changing 

last_time = time.time()

def rainupdating():
    global last_time
    current = time.time()
    dt = (current - last_time) * 60   # scaling it so motion matches old 16ms tick feel
    last_time = current
    for drop in raindrops:
        drop[1] -= drop[3] * dt
        drop[0] += angle * 0.12 * dt
        if drop[1] < -260:
            drop[1] = 265
            drop[0] = random.uniform(-250, 250)
    glutPostRedisplay()

#keyboards func left and right to bend

def keys(key, x, y):
    global angle
    if key == GLUT_KEY_LEFT:
        angle = max(-max_angle, angle - 0.4)
        print(f"Rain angle: {angle:+.1f}  (left)")
    elif key == GLUT_KEY_RIGHT:
        angle = min(max_angle, angle + 0.4)
        print(f"Rain angle: {angle:+.1f}  (right)")
    glutPostRedisplay()

def keyboard(key, x, y):
    global bright
    if key == b'd':                            
        bright = min(1.0, bright + bright_transition * 8)
        print(f"Brightness: {bright:.2f}  (-> day)")
    elif key == b'n':                         
        bright = max(0.0, bright - bright_transition * 8)
        print(f"Brightness: {bright:.2f}  (-> night)")
    elif key == b'\x1b':                       
        import sys; sys.exit(0)
    glutPostRedisplay()

def setup_projection():
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(-250, 250, -250, 250, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

def display():
    glClear(GL_COLOR_BUFFER_BIT)
    setup_projection()
    r, g, b = rgbofsky()
    glColor3f(r, g, b)
    rectangles_2tri(-250, -250, 250, 250)
    house()
    rains()
    glutSwapBuffers()

def main_task1():
    init_raindrops()
    glutInit()
    glutInitDisplayMode(GLUT_RGBA)
    glutInitWindowSize(width, height)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Task 1 is House during rain")
    glutDisplayFunc(display)
    glutSpecialFunc(keys)
    glutKeyboardFunc(keyboard)
    glutIdleFunc(rainupdating)
    print("=" * 42)
    print(" Task 1 is House during rain")
    print("=" * 42)
    print(" using left arrow we bend rain left")
    print(" using right arrow we bend rain right")
    print("  D : brighten (Night -> Day)")
    print("  N : dark   (Day  -> Night)")
    print("  ESC : quit")
    print("=" * 42)
    glutMainLoop()






# TASK 2: The Amazing Box


width2 = 500
height2 = 500

left   = 100
right  = 400
bottom = 100
top    = 400

dotlist   = []       
speed_point = 1.0
freeze = False
blink = False
blink_visibility = True
blinking_time  = 0

def diagonal():
    x = 1 if random.randint(0, 1) == 0 else -1
    y = 1 if random.randint(0, 1) == 0 else -1
    return x, y

def dot_colour():
    while True:
        r = random.randint(0, 10) / 10
        g = random.randint(0, 10) / 10    # if I divide this by 10 then I get a no betn 0 and 1
        b = random.randint(0, 10) / 10
        if r + g + b > 0.8:
            return r, g, b

def point_appears(x_axis, y_axis):
    gx = x_axis
    gy = height2 - y_axis              # we need to flip the y coordinate cuz origin is in bottom left in opengl
    gx = max(left,   min(right,  gx))
    gy = max(bottom, min(top,    gy))
    diag_x, diag_y = diagonal()
    r, g, b = dot_colour()
    dotlist.append([float(gx), float(gy), float(diag_x), float(diag_y), r, g, b])

def drawing_the_dot(x, y, size=7):
    glPointSize(size)
    glBegin(GL_POINTS)
    glVertex2f(x, y)
    glEnd()

def box():
    glColor3f(1.0, 1.0, 1.0)
    glLineWidth(2)
    lines(left, bottom, right, bottom)  
    lines(left, top, right, top)      
    lines(left, bottom, left, top)      
    lines(right, bottom, right, top)     
    glLineWidth(1)

last_time2= time.time()

def updating():
    global blinking_time, blink_visibility, last_time2
    current = time.time()
    t = (current - last_time2) * 1000
    last_time2 = current
    if not freeze:
        for i in dotlist:                 
            i[0] += i[2] * speed_point
            i[1] += i[3] * speed_point
            if i[0] <= left or i[0] >= right:
                i[2] *= -1
                i[0] = max(left, min(right, i[0]))
            if i[1] <= bottom or i[1] >= top:
                i[3] *= -1
                i[1] = max(bottom, min(top, i[1]))
        if blink:
            blinking_time += t
            if blinking_time >= 500:
                blink_visibility = not blink_visibility
                blinking_time   = 0
    glutPostRedisplay()

def keyboard0(button, x0, y0):
    global speed_point
    if freeze:
        return
    if button == GLUT_KEY_UP:
        speed_point = min(speed_point * 1.5, 20.0)
        print(f"Speed: {speed_point:.2f}")
    elif button == GLUT_KEY_DOWN:
        speed_point = max(speed_point / 1.5, 0.1)
        print(f"Speed: {speed_point:.2f}")
    glutPostRedisplay()

def keyboard1(button, x1, y1):
    global freeze, blink, blink_visibility, blinking_time   
    if button == b' ':  #byte
        freeze = not freeze
        print("Freeze" if freeze else "Unfreeze")
    elif button == b'\x1b':
        import sys; sys.exit(0)
    glutPostRedisplay()

def mouse(button, pos, x2, y2):
    global blink, blink_visibility, blinking_time           
    if freeze:
        return
    if button == GLUT_RIGHT_BUTTON and pos == GLUT_DOWN:
        point_appears(x2, y2)
        print(f"Point appears at ({x2},{y2})")
    elif button == GLUT_LEFT_BUTTON and pos == GLUT_DOWN:
        blink          = not blink
        blinking_time  = 0                                 
        blink_visibility = True
        print("Blinking ON" if blink else "Blinking OFF") 
    glutPostRedisplay()

def setup_projection2():
    glViewport(0, 0, width2, height2)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0.0, width2, 0.0, height2, 0.0, 1.0)
    glMatrixMode(GL_MODELVIEW)

def display2():                                             
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    setup_projection2()
    box()
    if not blink or blink_visibility:
        for j in dotlist:                                   
            glColor3f(j[4], j[5], j[6])
            drawing_the_dot(j[0], j[1])                    
    if freeze:
        glColor3f(1.0, 0.0, 0.0)
        glPointSize(10)
        glBegin(GL_POINTS)
        glVertex2f(15, height2 - 15)
        glEnd()
    glutSwapBuffers()

    #main tasks


def main_task2():
    glutInit()
    glutInitDisplayMode(GLUT_RGBA)
    glutInitWindowSize(width2, height2)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Task 2 - The Amazing Box")
    glutDisplayFunc(display2)                               
    glutSpecialFunc(keyboard0)
    glutKeyboardFunc(keyboard1)
    glutMouseFunc(mouse)
    glutIdleFunc(updating)
    print("=" * 42)
    print(" Task 2 is the The Amazing Box")
    print("=" * 42)
    print("  RIGHT click   ->  appears point")
    print("  LEFT  click   ->   blink")
    print("  UP    arrow   ->  speed up")
    print("  DOWN  arrow   ->  slows down")
    print("  SPACE         ->  freeze / unfreeze")
    print("  ESC           ->  quit")
    print("=" * 42)
    glutMainLoop()


# Since in one file task=1 or task=2 to run either

if __name__ == "__main__":
    task = 1    
    if task == 1:
        main_task1()
    else:
        main_task2()