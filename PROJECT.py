import math
import time
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

# ============================================================
#  PRISON BREAK - 3D first-person stealth escape game
#  Built on the provided PyOpenGL / GLUT template.
#  Keeps the same function names/hooks as the template:
#  draw_text, draw_shapes, keyboardListener, specialKeyListener,
#  mouseListener, setupCamera, idle, showScreen, main
# ============================================================

# ---------------- Camera-related variables (from template) ----------------
camera_pos = (0, 500, 500)   # kept for compatibility; recomputed each frame
fovY = 120                   # Field of view (kept as in template)
GRID_LENGTH = 2500           # now used as the overall floor extent
rand_var = 423                # unused leftover from template, kept for reference

# ---------------- World scale ----------------
# Every world coordinate below is on the XY ground plane, Z is "up"
# (matches the template's up-vector (0,0,1) and floor drawn on z=0).
WALL_H = 160.0
WALL_T = 40.0
PLAYER_H = 70.0
PLAYER_R = 18.0
MOVE_STEP = 26.0
GUARD_DETECT_R = 210.0
GUARD_CATCH_R = 55.0
GUARD_LOSE_R = 380.0
GUARD_PATROL_SPEED = 95.0     # units / second
GUARD_CHASE_SPEED = 165.0     # units / second
EXIT_TRIGGER_X = 2240.0

# ---------------- Mutable game state ----------------
player_x, player_y, player_angle = -240.0, 0.0, 0.0
walls = []   # list of dict(minx,maxx,miny,maxy)
doors = []   # list of dict(x, reqItem, isFinal, locked, offset)
items = []   # list of dict(id, x, y, collected)

guard = {}
guard_desk = (660.0, -280.0)
guard_state = 'patrol'
guard_lose_timer = 0.0

inventory = {'key': False, 'card': False, 'tools': False}
timer_active = False
time_remaining = 60.0

game_over = False
game_won = False
game_over_reason = ""

cheat_mode = False     # 'c' -> invulnerable + faster
cheat_vision = False   # 'v' -> radar readout of guard/items
camera_mode = 'first'  # 'first' or 'third' (right click toggles)

cam_orbit_angle = 200.0
cam_orbit_dist = 420.0
cam_height = 260.0

last_time = time.time()
toast_msg = ""
toast_until = 0.0


# ============================================================
#  Level construction helpers
# ============================================================

def wall_segments(start, end, gaps):
    """Split [start,end] into segments, skipping the given gap ranges."""
    segs = []
    cursor = start
    for g0, g1 in sorted(gaps):
        if g0 > cursor:
            segs.append((cursor, g0))
        cursor = max(cursor, g1)
    if cursor < end:
        segs.append((cursor, end))
    return segs


def add_wall_box(cx, cy, sx, sy):
    walls.append({
        'minx': cx - sx / 2.0, 'maxx': cx + sx / 2.0,
        'miny': cy - sy / 2.0, 'maxy': cy + sy / 2.0
    })


def add_wall_run_x(fixed_y, start, end, gaps):
    """Wall that runs along X, thin in Y, at a fixed Y coordinate."""
    for s0, s1 in wall_segments(start, end, gaps):
        add_wall_box((s0 + s1) / 2.0, fixed_y, s1 - s0, WALL_T)


def add_room(xmin, xmax, ymin, ymax, skip_wall):
    """A rectangular room with one wall fully open (shared with corridor)."""
    t = WALL_T
    if skip_wall != 'west':
        add_wall_box(xmin - t / 2.0, (ymin + ymax) / 2.0, t, (ymax - ymin) + t)
    if skip_wall != 'east':
        add_wall_box(xmax + t / 2.0, (ymin + ymax) / 2.0, t, (ymax - ymin) + t)
    if skip_wall != 'north':
        add_wall_box((xmin + xmax) / 2.0, ymax + t / 2.0, (xmax - xmin) + t, t)
    if skip_wall != 'south':
        add_wall_box((xmin + xmax) / 2.0, ymin - t / 2.0, (xmax - xmin) + t, t)


def build_level():
    """(Re)builds all static + dynamic level data. Called at startup and on reset."""
    global walls, doors, items
    walls = []
    doors = []
    items = []

    # ---- Starting cell: x -400..-80, y -160..160, opening east y -120..120 ----
    add_wall_box(-240, 160, 320, WALL_T)     # north
    add_wall_box(-240, -160, 320, WALL_T)    # south
    add_wall_box(-400, 0, WALL_T, 320)       # west
    add_wall_box(-80, 140, WALL_T, WALL_T)   # east stub (upper)
    add_wall_box(-80, -140, WALL_T, WALL_T)  # east stub (lower)

    # ---- Main corridor: x -80..2360, y -120..120 ----
    add_wall_run_x(140, -80, 2360, [(160, 400), (1560, 1840)])          # north wall, 2 gaps
    add_wall_run_x(-140, -80, 2360, [(600, 720), (840, 1160)])          # south wall, 2 gaps
    add_wall_box(2360, 0, WALL_T, 320)                                   # end cap wall

    # ---- Side room 1: KEY room (north, x 120..440, y 120..440) ----
    add_room(120, 440, 120, 440, 'south')

    # ---- Security / Guard room (south, x 600..720, y -440..-120) ----
    # A dedicated space for the patrolling guard, as called for in the
    # environment spec (prison cells / corridors / security rooms / doors).
    add_room(600, 720, -440, -120, 'north')

    # ---- Side room 2: ACCESS CARD room (south, x 840..1160, y -440..-120) ----
    add_room(840, 1160, -440, -120, 'north')

    # ---- Side room 3: TOOLS room (north, x 1560..1880, y 120..440) ----
    add_room(1560, 1880, 120, 440, 'south')

    # ---- Doors (gates across the corridor) ----
    doors.append({'x': 640.0, 'reqItem': 'key', 'isFinal': False,
                  'locked': True, 'offset': 0.0, 'color': (0.85, 0.65, 0.25)})
    doors.append({'x': 1360.0, 'reqItem': 'card', 'isFinal': False,
                  'locked': True, 'offset': 0.0, 'color': (0.35, 0.65, 0.85)})
    doors.append({'x': 2000.0, 'reqItem': 'tools', 'isFinal': True,
                  'locked': True, 'offset': 0.0, 'color': (0.85, 0.3, 0.3)})

    # ---- Items ----
    items.append({'id': 'key', 'x': 280.0, 'y': 280.0, 'collected': False,
                  'color': (0.85, 0.65, 0.25)})
    items.append({'id': 'card', 'x': 1000.0, 'y': -280.0, 'collected': False,
                  'color': (0.35, 0.65, 0.85)})
    items.append({'id': 'tools', 'x': 1720.0, 'y': 280.0, 'collected': False,
                  'color': (0.85, 0.3, 0.3)})

    # A cosmetic desk marking the guard room as the guard's post
    global guard_desk
    guard_desk = (660.0, -280.0)


def build_guard():
    global guard
    guard = {
        'x': 80.0, 'y': 0.0,
        'a': (80.0, 0.0), 'b': (560.0, 0.0),
        'target': 'b'
    }


# ============================================================
#  Collision
# ============================================================

def active_colliders():
    colliders = list(walls)
    for d in doors:
        if d['locked']:
            colliders.append({
                'minx': d['x'] - WALL_T / 2.0, 'maxx': d['x'] + WALL_T / 2.0,
                'miny': -120.0, 'maxy': 120.0
            })
    return colliders


def can_stand(x, y):
    r = PLAYER_R
    for c in active_colliders():
        if x + r > c['minx'] and x - r < c['maxx'] and y + r > c['miny'] and y - r < c['maxy']:
            return False
    return True


# ============================================================
#  Text / HUD drawing  (template's draw_text, reused as-is)
# ============================================================

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()

    # Set up an orthographic projection that matches window coordinates
    gluOrtho2D(0, 1000, 0, 800)  # left, right, bottom, top

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # Draw text at (x, y) in screen coordinates
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))

    # Restore original projection and modelview matrices
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def draw_hud():
    # Inventory
    draw_text(10, 770, "INVENTORY:")
    draw_text(10, 748, ("[X] Key" if inventory['key'] else "[ ] Key"))
    draw_text(10, 726, ("[X] Access Card" if inventory['card'] else "[ ] Access Card"))
    draw_text(10, 704, ("[X] Tools" if inventory['tools'] else "[ ] Tools"))

    # Guard status
    status = "GUARD: ALERTED!" if guard_state == 'alert' else "GUARD: patrolling"
    draw_text(800, 770, status)

    # Timer
    if timer_active:
        draw_text(430, 770, f"TIME REMAINING: {int(math.ceil(time_remaining))}s")

    # Cheat indicators
    if cheat_mode:
        draw_text(800, 748, "CHEAT MODE: ON")
    if cheat_vision:
        gdx = guard['x'] - player_x
        gdy = guard['y'] - player_y
        gdist = math.hypot(gdx, gdy)
        draw_text(800, 726, f"[RADAR] Guard dist: {int(gdist)}")

    # Interact prompt
    d = nearest_locked_door()
    if d is not None:
        label = {'key': 'Key', 'card': 'Access Card', 'tools': 'Tools'}[d['reqItem']]
        if inventory[d['reqItem']]:
            draw_text(360, 40, f"Press E (or left click) to unlock door [{label}]")
        else:
            draw_text(360, 40, f"Locked -- requires {label}")

    # Toast
    if toast_msg and time.time() < toast_until:
        draw_text(360, 70, toast_msg)

    # Controls reminder
    draw_text(10, 20, "W/S/A/D move   Mouse look   E/LClick interact   C cheat   V radar   RClick camera   R reset")

    # Game over / win banners
    if game_over:
        draw_text(380, 420, "GAME OVER", GLUT_BITMAP_TIMES_ROMAN_24)
        draw_text(360, 390, game_over_reason)
        draw_text(300, 360, "Press R to try again")
    elif game_won:
        draw_text(330, 420, "ESCAPE SUCCESSFUL!", GLUT_BITMAP_TIMES_ROMAN_24)
        draw_text(300, 360, "Press R to play again")

    draw_minimap()


def draw_minimap():
    """Small top-down radar drawn in screen space, bottom-right corner."""
    ox, oy, scale = 800, 40, 0.045
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # background box
    glColor3f(0.05, 0.08, 0.08)
    glBegin(GL_QUADS)
    glVertex2f(ox - 4, oy - 4)
    glVertex2f(ox + 186, oy - 4)
    glVertex2f(ox + 186, oy + 146)
    glVertex2f(ox - 4, oy + 146)
    glEnd()

    def to_screen(wx, wy):
        return ox + (wx + 400) * scale, oy + (wy + 400) * scale

    glColor3f(0.35, 0.45, 0.45)
    for w in walls:
        x0, y0 = to_screen(w['minx'], w['miny'])
        x1, y1 = to_screen(w['maxx'], w['maxy'])
        glBegin(GL_QUADS)
        glVertex2f(x0, y0)
        glVertex2f(x1, y0)
        glVertex2f(x1, y1)
        glVertex2f(x0, y1)
        glEnd()

    for d in doors:
        x, y = to_screen(d['x'], 0)
        glColor3f(0.9, 0.25, 0.25) if d['locked'] else glColor3f(0.25, 0.85, 0.4)
        glBegin(GL_QUADS)
        glVertex2f(x - 2, y - 6)
        glVertex2f(x + 2, y - 6)
        glVertex2f(x + 2, y + 6)
        glVertex2f(x - 2, y + 6)
        glEnd()

    for it in items:
        if it['collected']:
            continue
        x, y = to_screen(it['x'], it['y'])
        glColor3f(1.0, 0.83, 0.36)
        glBegin(GL_QUADS)
        glVertex2f(x - 2, y - 2)
        glVertex2f(x + 2, y - 2)
        glVertex2f(x + 2, y + 2)
        glVertex2f(x - 2, y + 2)
        glEnd()

    gx, gy = to_screen(guard['x'], guard['y'])
    glColor3f(1.0, 0.15, 0.15) if guard_state == 'alert' else glColor3f(0.3, 0.55, 0.85)
    glBegin(GL_QUADS)
    glVertex2f(gx - 3, gy - 3)
    glVertex2f(gx + 3, gy - 3)
    glVertex2f(gx + 3, gy + 3)
    glVertex2f(gx - 3, gy + 3)
    glEnd()

    px, py = to_screen(player_x, player_y)
    glColor3f(1, 1, 1)
    glBegin(GL_QUADS)
    glVertex2f(px - 3, py - 3)
    glVertex2f(px + 3, py - 3)
    glVertex2f(px + 3, py + 3)
    glVertex2f(px - 3, py + 3)
    glEnd()

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


# ============================================================
#  3D drawing (template's draw_shapes, repurposed for the level)
# ============================================================

def draw_box(cx, cy, cz, sx, sy, sz, color):
    glPushMatrix()
    glColor3f(*color)
    glTranslatef(cx, cy, cz)
    glScalef(sx, sy, sz)
    glutSolidCube(1.0)
    glPopMatrix()


def draw_floor():
    glColor3f(0.16, 0.18, 0.18)
    glBegin(GL_QUADS)
    glVertex3f(-500, -500, 0)
    glVertex3f(GRID_LENGTH, -500, 0)
    glVertex3f(GRID_LENGTH, 500, 0)
    glVertex3f(-500, 500, 0)
    glEnd()

    # exit floor patch (bright, marks the escape point)
    glColor3f(0.22, 0.85, 0.42)
    glBegin(GL_QUADS)
    glVertex3f(2200, -140, 1)
    glVertex3f(2340, -140, 1)
    glVertex3f(2340, 140, 1)
    glVertex3f(2200, 140, 1)
    glEnd()


def draw_walls():
    for w in walls:
        cx = (w['minx'] + w['maxx']) / 2.0
        cy = (w['miny'] + w['maxy']) / 2.0
        sx = w['maxx'] - w['minx']
        sy = w['maxy'] - w['miny']
        draw_box(cx, cy, WALL_H / 2.0, sx, sy, WALL_H, (0.42, 0.42, 0.40))


def draw_doors():
    for d in doors:
        z = WALL_H / 2.0 + d['offset']
        draw_box(d['x'], 0, z, WALL_T, 240.0, WALL_H, d['color'])


def draw_items():
    for it in items:
        if it['collected']:
            continue
        draw_box(it['x'], it['y'], 40.0, 26.0, 26.0, 34.0, it['color'])

    # Guard room desk (cosmetic, marks the security/guard room)
    dx, dy = guard_desk
    draw_box(dx, dy, 35.0, 90.0, 40.0, 70.0, (0.30, 0.24, 0.20))


def draw_guard():
    glPushMatrix()
    glTranslatef(guard['x'], guard['y'], 0)
    dx = player_x - guard['x']
    dy = player_y - guard['y']
    ang = math.degrees(math.atan2(dy, dx))
    glRotatef(ang, 0, 0, 1)

    color = (0.9, 0.25, 0.22) if guard_state == 'alert' else (0.28, 0.38, 0.55)
    quad = gluNewQuadric()
    glColor3f(*color)
    glPushMatrix()
    glRotatef(-90, 1, 0, 0)   # cylinder default axis is Z -> stand it upright
    gluCylinder(quad, 22, 22, 95, 10, 4)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(0, 0, 110)
    gluSphere(quad, 20, 10, 10)
    glPopMatrix()

    glPopMatrix()


def draw_shapes():
    """Draws every dynamic/static 3D object in the level (template hook)."""
    draw_walls()
    draw_doors()
    draw_items()
    draw_guard()

    if cheat_vision:
        draw_detection_ring()


def draw_detection_ring():
    """Cheat-vision aid: outlines the guard's detection radius on the floor."""
    glColor3f(1.0, 0.3, 0.3)
    glLineWidth(2.0)
    glBegin(GL_LINE_LOOP)
    for i in range(48):
        a = 2 * math.pi * i / 48
        glVertex3f(guard['x'] + math.cos(a) * GUARD_DETECT_R,
                   guard['y'] + math.sin(a) * GUARD_DETECT_R, 2)
    glEnd()


# ============================================================
#  Gameplay logic
# ============================================================

def nearest_locked_door():
    best, best_d = None, 1e9
    for d in doors:
        if not d['locked']:
            continue
        dd = math.hypot(player_x - d['x'], player_y)
        if dd < 130 and dd < best_d:
            best, best_d = d, dd
    return best


def show_toast(msg, seconds=2.2):
    global toast_msg, toast_until
    toast_msg = msg
    toast_until = time.time() + seconds


def try_interact():
    if game_over or game_won:
        return
    d = nearest_locked_door()
    if d is None or not inventory[d['reqItem']]:
        return
    d['locked'] = False
    label = {'key': 'Key', 'card': 'Access card', 'tools': 'Tools'}[d['reqItem']]
    show_toast(f"{label} used -- door unlocked!")
    if d['isFinal']:
        global timer_active, time_remaining
        timer_active = True
        time_remaining = 60.0
        show_toast("Alarm triggered! 60 seconds to escape!", 3.0)


def update_items_pickup():
    for it in items:
        if it['collected']:
            continue
        if math.hypot(player_x - it['x'], player_y - it['y']) < 60:
            it['collected'] = True
            inventory[it['id']] = True
            label = {'key': 'Key', 'card': 'Access Card', 'tools': 'Tools'}[it['id']]
            show_toast(f"Picked up: {label}")


def update_doors(dt):
    for d in doors:
        if not d['locked'] and d['offset'] < WALL_H + 40:
            d['offset'] += dt * (WALL_H + 40)


def update_guard(dt):
    global guard_state, guard_lose_timer

    dx = player_x - guard['x']
    dy = player_y - guard['y']
    dist = math.hypot(dx, dy)

    if guard_state == 'patrol':
        tgt = guard['b'] if guard['target'] == 'b' else guard['a']
        tx, ty = tgt[0] - guard['x'], tgt[1] - guard['y']
        d = math.hypot(tx, ty)
        if d < 4:
            guard['target'] = 'a' if guard['target'] == 'b' else 'b'
        else:
            guard['x'] += tx / d * GUARD_PATROL_SPEED * dt
            guard['y'] += ty / d * GUARD_PATROL_SPEED * dt

        if dist < GUARD_DETECT_R and not cheat_mode:
            guard_state = 'alert'
            guard_lose_timer = 0.0
    else:
        if dist > 1:
            guard['x'] += dx / dist * GUARD_CHASE_SPEED * dt
            guard['y'] += dy / dist * GUARD_CHASE_SPEED * dt

        if dist < GUARD_CATCH_R and not cheat_mode:
            trigger_game_over("You were caught!")

        if dist > GUARD_LOSE_R:
            guard_lose_timer += dt
            if guard_lose_timer > 3.0:
                guard_state = 'patrol'
        else:
            guard_lose_timer = 0.0


def update_timer(dt):
    global timer_active, time_remaining
    if not timer_active or game_over or game_won:
        return
    time_remaining -= dt
    if time_remaining <= 0:
        time_remaining = 0
        timer_active = False
        trigger_game_over("Time's up!")


def check_exit():
    if player_x > EXIT_TRIGGER_X and abs(player_y) < 150:
        trigger_win()


def trigger_game_over(reason):
    global game_over, game_over_reason
    if game_over or game_won:
        return
    game_over = True
    game_over_reason = reason


def trigger_win():
    global game_won
    if game_over or game_won:
        return
    game_won = True


def reset_game():
    global player_x, player_y, player_angle
    global guard_state, guard_lose_timer
    global timer_active, time_remaining, game_over, game_won, game_over_reason
    global cheat_mode, cheat_vision, camera_mode

    build_level()
    build_guard()

    player_x, player_y, player_angle = -240.0, 0.0, 0.0
    guard_state = 'patrol'
    guard_lose_timer = 0.0

    for k in inventory:
        inventory[k] = False

    timer_active = False
    time_remaining = 60.0
    game_over = False
    game_won = False
    game_over_reason = ""
    cheat_mode = False
    cheat_vision = False
    camera_mode = 'first'
    show_toast("Escape the prison!", 2.5)


# ============================================================
#  Input callbacks (template hooks)
# ============================================================

def keyboardListener(key, x, y):
    """
    Handles keyboard inputs for player movement, turning, interaction
    and cheat mode toggles.
    """
    global player_x, player_y, player_angle, cheat_mode, cheat_vision

    if key in (b'r', b'R'):
        reset_game()
        glutPostRedisplay()
        return

    if game_over or game_won:
        return

    step = MOVE_STEP * (1.8 if cheat_mode else 1.0)
    rad = math.radians(player_angle)

    # Move forward (W key)
    if key in (b'w', b'W'):
        nx = player_x + math.cos(rad) * step
        ny = player_y + math.sin(rad) * step
        if can_stand(nx, player_y):
            player_x = nx
        if can_stand(player_x, ny):
            player_y = ny

    # Move backward (S key)
    if key in (b's', b'S'):
        nx = player_x - math.cos(rad) * step
        ny = player_y - math.sin(rad) * step
        if can_stand(nx, player_y):
            player_x = nx
        if can_stand(player_x, ny):
            player_y = ny

    # Move left / strafe (A key)
    if key in (b'a', b'A'):
        srad = rad + math.pi / 2
        nx = player_x + math.cos(srad) * step
        ny = player_y + math.sin(srad) * step
        if can_stand(nx, player_y):
            player_x = nx
        if can_stand(player_x, ny):
            player_y = ny

    # Move right / strafe (D key)
    if key in (b'd', b'D'):
        srad = rad - math.pi / 2
        nx = player_x + math.cos(srad) * step
        ny = player_y + math.sin(srad) * step
        if can_stand(nx, player_y):
            player_x = nx
        if can_stand(player_x, ny):
            player_y = ny

    # Interact with nearby locked door
    if key in (b'e', b'E'):
        try_interact()

    # Toggle cheat mode (C key) -- invulnerable + faster movement
    if key in (b'c', b'C'):
        cheat_mode = not cheat_mode
        show_toast("Cheat mode " + ("ON" if cheat_mode else "OFF"))

    # Toggle cheat vision (V key) -- radar readout + detection ring
    if key in (b'v', b'V'):
        cheat_vision = not cheat_vision
        show_toast("Cheat vision " + ("ON" if cheat_vision else "OFF"))

    glutPostRedisplay()


def specialKeyListener(key, x, y):
    """
    Handles special key inputs (arrow keys) for adjusting the
    third-person orbit camera's angle and height.
    """
    global cam_orbit_angle, cam_height

    # Move camera up (UP arrow key)
    if key == GLUT_KEY_UP:
        cam_height = min(cam_height + 15, 700)

    # Move camera down (DOWN arrow key)
    if key == GLUT_KEY_DOWN:
        cam_height = max(cam_height - 15, 60)

    # Orbit camera left (LEFT arrow key)
    if key == GLUT_KEY_LEFT:
        cam_orbit_angle = (cam_orbit_angle + 5) % 360

    # Orbit camera right (RIGHT arrow key)
    if key == GLUT_KEY_RIGHT:
        cam_orbit_angle = (cam_orbit_angle - 5) % 360

    glutPostRedisplay()


_win_cx, _win_cy = 500, 400
_ignore_next_motion = False
LOOK_SENSITIVITY = 0.13


def mouseMoveListener(x, y):
    """
    First-person mouse-look: compares the cursor to the window centre,
    turns the player by the horizontal delta, then re-centres the cursor.
    Registered for both passive motion (no button held) and motion
    (button held), so looking around always works.
    """
    global player_angle, _ignore_next_motion

    if game_over or game_won:
        return

    if _ignore_next_motion:
        # this event was caused by our own glutWarpPointer call below
        _ignore_next_motion = False
        return

    dx = x - _win_cx
    if dx != 0:
        player_angle = (player_angle - dx * LOOK_SENSITIVITY) % 360

    _ignore_next_motion = True
    glutWarpPointer(_win_cx, _win_cy)
    glutPostRedisplay()


def mouseListener(button, state, x, y):
    """
    Handles mouse inputs:
    left click  -> interact with a nearby locked door
    right click -> toggle first-person / third-person camera
    """
    global camera_mode

    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        try_interact()

    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        camera_mode = 'third' if camera_mode == 'first' else 'first'
        show_toast("Camera: " + ("Third-person" if camera_mode == 'third' else "First-person"))

    glutPostRedisplay()


# ============================================================
#  Camera / render pipeline (template hooks)
# ============================================================

def setupCamera():
    """
    Configures the camera's projection and view settings.
    Uses a perspective projection; first-person mode places the
    camera at the player's eyes, third-person orbits around them.
    """
    global camera_pos

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, 1.25, 1.0, 6000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    if camera_mode == 'first':
        eye_x, eye_y, eye_z = player_x, player_y, PLAYER_H
        rad = math.radians(player_angle)
        look_x = eye_x + math.cos(rad) * 200
        look_y = eye_y + math.sin(rad) * 200
        look_z = eye_z
    else:
        rad = math.radians(cam_orbit_angle)
        eye_x = player_x + math.cos(rad) * cam_orbit_dist
        eye_y = player_y + math.sin(rad) * cam_orbit_dist
        eye_z = cam_height
        look_x, look_y, look_z = player_x, player_y, 60

    camera_pos = (eye_x, eye_y, eye_z)

    gluLookAt(eye_x, eye_y, eye_z,
              look_x, look_y, look_z,
              0, 0, 1)


def idle():
    """
    Idle function that runs continuously:
    - advances guard AI / timer using real elapsed time
    - triggers a screen redraw for real-time updates
    """
    global last_time
    now = time.time()
    dt = min(now - last_time, 0.05)
    last_time = now

    if not game_over and not game_won:
        update_guard(dt)
        update_doors(dt)
        update_items_pickup()
        update_timer(dt)
        check_exit()

    glutPostRedisplay()


def showScreen():
    """
    Display function to render the game scene:
    - Clears the screen and sets up the camera.
    - Draws the floor, level geometry, guard, items and HUD.
    """
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)

    setupCamera()

    draw_floor()
    draw_shapes()
    draw_hud()

    glutSwapBuffers()


# ============================================================
#  Main
# ============================================================

def main():
    global last_time
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(0, 0)
    wind = glutCreateWindow(b"Prison Break :: Stealth Escape")

    glEnable(GL_DEPTH_TEST)
    glClearColor(0.03, 0.04, 0.05, 1.0)

    build_level()
    build_guard()
    show_toast("Escape the prison! Find the Key, Access Card and Tools.", 3.0)
    last_time = time.time()

    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutPassiveMotionFunc(mouseMoveListener)
    glutMotionFunc(mouseMoveListener)
    glutIdleFunc(idle)
    glutWarpPointer(_win_cx, _win_cy)
    glutSetCursor(GLUT_CURSOR_NONE)

    glutMainLoop()


if __name__ == "__main__":
    main()