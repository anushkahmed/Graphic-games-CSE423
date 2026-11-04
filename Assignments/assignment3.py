from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
import time


grid = 600          
cell = 80             
wall = 100          
view = 120                 


camera_angle = -90.0      
camera_height = 450.0    
camera_radius = 750.0      
first_person = False      

player_x = 0.0
player_y = 0.0
player_angle = 0.0         
PLAYER_SPEED = 10.0
TURN_SPEED = 5.0
GUN_HEIGHT = 100.0         
GUN_LENGTH = 80.0

life = 5
score = 0
missed = 0
game_over = False

cheat_mode = False
cheat_vision = False
cheat_cooldown = 0        

enemies = []
ENEMY_COUNT = 5
ENEMY_SPEED = 1.2
enemy_scale = 1.0          
enemy_growing = True



bullets = []
BULLET_SPEED = 18.0
last_time = time.time()


def direction_vector(angle_deg):
    rad = math.radians(angle_deg)
    return -math.sin(rad), math.cos(rad)


def angle_to_point(x, y):
    return math.degrees(math.atan2(-(x - player_x), y - player_y))


def angle_difference(a, b):
    
    d = b - a
    while d > 180:
        d -= 360
    while d < -180:
        d += 360
    return d


def random_enemy_position():

    while True:
        x = random.randint(-grid + 60, grid - 60)
        y = random.randint(-grid + 60, grid - 60)
        distance = math.sqrt((x - player_x) ** 2 + (y - player_y) ** 2)
        if distance > 300:
            return float(x), float(y)


def nearest_enemy():
    best = None
    best_distance = 999999
    for e in enemies:
        d = math.sqrt((e['x'] - player_x) ** 2 + (e['y'] - player_y) ** 2)
        if d < best_distance:
            best_distance = d
            best = e
    return best


def reset_game():
    global player_x, player_y, player_angle
    global life, score, missed, game_over
    global cheat_mode, cheat_vision, cheat_cooldown
    global enemy_scale, enemy_growing

    player_x = 0.0
    player_y = 0.0
    player_angle = 0.0

    life = 5
    score = 0
    missed = 0
    game_over = False

    cheat_mode = False
    cheat_vision = False
    cheat_cooldown = 0

    enemy_scale = 1.0
    enemy_growing = True

    bullets.clear()
    enemies.clear()
    for i in range(ENEMY_COUNT):
        x, y = random_enemy_position()
        enemies.append({'x': x, 'y': y})


def fire_bullet():
    dx, dy = direction_vector(player_angle)
    bullets.append({
        'x': player_x + dx * GUN_LENGTH,
        'y': player_y + dy * GUN_LENGTH,
        'z': GUN_HEIGHT,
        'dx': dx,
        'dy': dy
    })


def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()

    gluOrtho2D(0, 1000, 0, 800)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def draw_floor():
    
    number_of_cells = (2 * grid) // cell

    glBegin(GL_QUADS)
    for i in range(number_of_cells):
        for j in range(number_of_cells):
            x = -grid + i * cell
            y = -grid + j * cell

            if (i + j) % 2 == 0:
                glColor3f(1, 1, 1)             
            else:
                glColor3f(0.7, 0.5, 0.95)       

            glVertex3f(x, y, 0)
            glVertex3f(x + cell, y, 0)
            glVertex3f(x + cell, y + cell, 0)
            glVertex3f(x, y + cell, 0)
    glEnd()


def draw_walls():
   
    g = grid
    h = wall

    glBegin(GL_QUADS)

  
    glColor3f(0, 0, 1)
    glVertex3f(-g, -g, 0)
    glVertex3f(-g, g, 0)
    glVertex3f(-g, g, h)
    glVertex3f(-g, -g, h)

    glColor3f(0, 1, 0)
    glVertex3f(g, -g, 0)
    glVertex3f(g, g, 0)
    glVertex3f(g, g, h)
    glVertex3f(g, -g, h)

    glColor3f(0, 1, 1)
    glVertex3f(-g, g, 0)
    glVertex3f(g, g, 0)
    glVertex3f(g, g, h)
    glVertex3f(-g, g, h)

   
    glColor3f(1, 1, 1)
    glVertex3f(-g, -g, 0)
    glVertex3f(g, -g, 0)
    glVertex3f(g, -g, h)
    glVertex3f(-g, -g, h)

    glEnd()


def draw_player():
   
    glPushMatrix()

    glTranslatef(player_x, player_y, 0)
    glRotatef(player_angle, 0, 0, 1)

    # when the game is over the player lies down
    if game_over:
        glTranslatef(0, 0, 30)
        glRotatef(90, 1, 0, 0)

    # ---------- legs (two cylinders) ----------
    glColor3f(0, 0, 1)
    glPushMatrix()
    glTranslatef(-14, 0, 0)
    gluCylinder(gluNewQuadric(), 13, 8, 60, 10, 10)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(14, 0, 0)
    gluCylinder(gluNewQuadric(), 13, 8, 60, 10, 10)
    glPopMatrix()

    # ---------- body (cuboid) ----------
    glColor3f(0.3, 0.4, 0.2)
    glPushMatrix()
    glTranslatef(0, 0, 90)
    glScalef(1.3, 0.7, 1.2)
    glutSolidCube(50)
    glPopMatrix()

    # ---------- head (sphere) ----------
    glColor3f(0, 0, 0)
    glPushMatrix()
    glTranslatef(0, 0, 138)
    gluSphere(gluNewQuadric(), 20, 12, 12)
    glPopMatrix()

    # ---------- arms (two cylinders pointing forward) ----------
    glColor3f(1, 0.85, 0.7)
    glPushMatrix()
    glTranslatef(-32, 0, 105)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 9, 9, 55, 10, 10)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(32, 0, 105)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 9, 9, 55, 10, 10)
    glPopMatrix()

    
    glPushMatrix()
    glTranslatef(0, 0, GUN_HEIGHT)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 12, 4, GUN_LENGTH, 10, 10)
    glPopMatrix()

    glPopMatrix()


def draw_enemies():
   
    for e in enemies:
        glPushMatrix()
        glTranslatef(e['x'], e['y'], 0)
        glScalef(enemy_scale, enemy_scale, enemy_scale)

        glColor3f(1, 0, 0)
        glTranslatef(0, 0, 30)
        gluSphere(gluNewQuadric(), 30, 12, 12)

        glColor3f(0, 0, 0)
        glTranslatef(0, 0, 36)
        gluSphere(gluNewQuadric(), 13, 12, 12)

        glPopMatrix()


def draw_bullets():
  
    glColor3f(1, 1, 0)
    for b in bullets:
        glPushMatrix()
        glTranslatef(b['x'], b['y'], b['z'])
        glutSolidCube(15)
        glPopMatrix()



def update_game():
    global missed, score, life, game_over
    global enemy_scale, enemy_growing
    global player_angle, cheat_cooldown

    if game_over:
        return

   
    i = len(bullets) - 1
    while i >= 0:
        b = bullets[i]
        b['x'] += b['dx'] * BULLET_SPEED
        b['y'] += b['dy'] * BULLET_SPEED

        # bullet left the grid = missed bullet
        if abs(b['x']) > grid or abs(b['y']) > grid:
            bullets.pop(i)
            missed += 1
        i -= 1


    if enemy_growing:
        enemy_scale += 0.006
        if enemy_scale > 1.2:
            enemy_growing = False
    else:
        enemy_scale -= 0.006
        if enemy_scale < 0.8:
            enemy_growing = True

   
    for e in enemies:
        vx = player_x - e['x']
        vy = player_y - e['y']
        d = math.sqrt(vx * vx + vy * vy)

        if d > 1:
            e['x'] += (vx / d) * ENEMY_SPEED
            e['y'] += (vy / d) * ENEMY_SPEED

        if d < 50:
            life -= 1
            e['x'], e['y'] = random_enemy_position()

  
    i = len(bullets) - 1
    while i >= 0:
        b = bullets[i]
        hit = False
        for e in enemies:
            d = math.sqrt((b['x'] - e['x']) ** 2 + (b['y'] - e['y']) ** 2)
            if d < 38 * enemy_scale:
                hit = True
                score += 1
                e['x'], e['y'] = random_enemy_position()
                break
        if hit:
            bullets.pop(i)
        i -= 1

   
    if cheat_mode:
        player_angle += 2.0
        if player_angle >= 360:
            player_angle -= 360

        if cheat_cooldown > 0:
            cheat_cooldown -= 1
        else:
            for e in enemies:
                target_angle = angle_to_point(e['x'], e['y'])
                if abs(angle_difference(player_angle, target_angle)) < 5:
                    fire_bullet()
                    cheat_cooldown = 8
                    break

    
    if life <= 0 or missed >= 10:
        game_over = True


def keyboardListener(key, x, y):
    """
    W / S  -> move forward and backward
    A / D  -> rotate the gun left and right
    C      -> cheat mode on / off
    V      -> cheat vision on / off
    R      -> restart the game
    """
    global player_x, player_y, player_angle
    global cheat_mode, cheat_vision

    
    key = key.lower()

   
    if key == b'r':
        reset_game()
        return

    if game_over:
        return

    dx, dy = direction_vector(player_angle)

    # move forward
    if key == b'w':
        new_x = player_x + dx * PLAYER_SPEED
        new_y = player_y + dy * PLAYER_SPEED
        if abs(new_x) < grid - 40 and abs(new_y) < grid - 40:
            player_x = new_x
            player_y = new_y

    # move backward
    if key == b's':
        new_x = player_x - dx * PLAYER_SPEED
        new_y = player_y - dy * PLAYER_SPEED
        if abs(new_x) < grid - 40 and abs(new_y) < grid - 40:
            player_x = new_x
            player_y = new_y

    if key == b'a' and not cheat_mode:
        player_angle += TURN_SPEED
        if player_angle >= 360:
            player_angle -= 360

    if key == b'd' and not cheat_mode:
        player_angle -= TURN_SPEED
        if player_angle < 0:
            player_angle += 360

    # cheat mode
    if key == b'c':
        cheat_mode = not cheat_mode

    # cheat vision
    if key == b'v':
        cheat_vision = not cheat_vision


def specialKeyListener(key, x, y):
   
    global camera_height, camera_angle

    if key == GLUT_KEY_UP:
        camera_height += 15
        if camera_height > 1000:
            camera_height = 1000

    if key == GLUT_KEY_DOWN:
        camera_height -= 15
        if camera_height < 100:
            camera_height = 100

    if key == GLUT_KEY_LEFT:
        camera_angle -= 3

    if key == GLUT_KEY_RIGHT:
        camera_angle += 3


def mouseListener(button, state, x, y):
    global first_person

    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        if not game_over:
            fire_bullet()

    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        first_person = not first_person


def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(view, 1.25, 0.1, 2500)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    if first_person:
        dx, dy = direction_vector(player_angle)
        eye_x = player_x + dx * 30
        eye_y = player_y + dy * 30
        eye_z = GUN_HEIGHT + 30

        look_x = eye_x + dx * 100
        look_y = eye_y + dy * 100
        look_z = eye_z

        if cheat_mode and cheat_vision:
            target = nearest_enemy()
            if target is not None:
                look_x = target['x']
                look_y = target['y']
                look_z = 50

        gluLookAt(eye_x, eye_y, eye_z,
                  look_x, look_y, look_z,
                  0, 0, 1)
    else:
        rad = math.radians(camera_angle)
        cam_x = camera_radius * math.cos(rad)
        cam_y = camera_radius * math.sin(rad)

        gluLookAt(cam_x, cam_y, camera_height,
                  0, 0, 0,
                  0, 0, 1)



def idle():
   
    global last_time

    now = time.time()
    if now - last_time > 0.016:      # about 60 updates per second
        last_time = now
        update_game()

    glutPostRedisplay()


def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
 

    setupCamera()

    draw_floor()
    draw_walls()
    draw_player()

   
    if not game_over:
        draw_enemies()
        draw_bullets()

    
    if game_over:
        draw_text(10, 770, f"Game is Over. Your Score is {score}.")
        draw_text(10, 740, 'Press "R" to RESTART the Game.')
    else:
        draw_text(10, 770, f"Player Life Remaining: {life}")
        draw_text(10, 740, f"Game Score: {score}")
        draw_text(10, 710, f"Player Bullet Missed: {missed}")

    glutSwapBuffers()


def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(0, 0)
    wind = glutCreateWindow(b"3D OpenGL Bullet Frenzy")

    reset_game()

    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)

    glutMainLoop()


if __name__ == "__main__":
    main()