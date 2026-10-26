"""
Indian Bus Simulator: GameHub-friendly prototype.
Designed for low-resolution Windows emulation on Android.
Keyboard: W/S accelerate/brake, A/D steer, C camera, 1/2 bus, Esc quit.
Touch: tap large on-screen controls. Accelerator/brake are toggle controls.
This is an arcade prototype; no full multiplayer or realistic physics yet.
"""
import math
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.gui.DirectGui import DirectButton, DirectLabel
from direct.gui import DirectGuiGlobals as DGG
from panda3d.core import (
    AmbientLight, DirectionalLight, Vec3, Vec4, TextNode,
    WindowProperties, CardMaker, LineSegs
)

BUS_STYLES = {
    "government": {"label": "GOVERNMENT BUS", "body": (0.72, 0.08, 0.08, 1), "roof": (0.92, 0.88, 0.72, 1)},
    "private": {"label": "PRIVATE COACH", "body": (0.05, 0.20, 0.62, 1), "roof": (0.96, 0.76, 0.06, 1)},
}


def cube(parent, name, pos, scale, color):
    """Create a cube from built-in Panda3D geometry without external model files."""
    fmt = __import__("panda3d.core", fromlist=["GeomVertexFormat"]).GeomVertexFormat.getV3n3()
    vdata = __import__("panda3d.core", fromlist=["GeomVertexData"]).GeomVertexData(
        name, fmt, __import__("panda3d.core", fromlist=["Geom"]).Geom.UHStatic
    )
    vw = __import__("panda3d.core", fromlist=["GeomVertexWriter"]).GeomVertexWriter(vdata, "vertex")
    nw = __import__("panda3d.core", fromlist=["GeomVertexWriter"]).GeomVertexWriter(vdata, "normal")
    # six cube faces, each face has its own normals
    faces = [
        ((0,0,1), [(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]),
        ((0,0,-1), [(-1,1,-1),(1,1,-1),(1,-1,-1),(-1,-1,-1)]),
        ((0,-1,0), [(-1,-1,-1),(1,-1,-1),(1,-1,1),(-1,-1,1)]),
        ((0,1,0), [(-1,1,1),(1,1,1),(1,1,-1),(-1,1,-1)]),
        ((-1,0,0), [(-1,-1,1),(-1,1,1),(-1,1,-1),(-1,-1,-1)]),
        ((1,0,0), [(1,-1,-1),(1,1,-1),(1,1,1),(1,-1,1)]),
    ]
    from panda3d.core import Geom, GeomTriangles, GeomNode
    tris = GeomTriangles(Geom.UHStatic)
    for normal, verts in faces:
        start = vw.getWriteRow()
        for x,y,z in verts:
            vw.addData3(x,y,z)
            nw.addData3(*normal)
        tris.addVertices(start, start+1, start+2)
        tris.addVertices(start, start+2, start+3)
    geom = Geom(vdata)
    geom.addPrimitive(tris)
    node = GeomNode(name)
    node.addGeom(geom)
    np = parent.attachNewNode(node)
    np.setName(name)
    np.setPos(*pos)
    np.setScale(*scale)
    np.setColor(*color)
    return np


class BusGame(ShowBase):
    def __init__(self):
        super().__init__()
        self.disableMouse()
        self.setBackgroundColor(0.50, 0.72, 0.88, 1)
        props = WindowProperties()
        props.setTitle("Indian Bus Simulator - GameHub Edition")
        props.setSize(960, 540)
        self.win.requestProperties(props)
        self.setFrameRateMeter(False)

        self.speed = 0.0
        self.heading = 0.0
        self.camera_mode = 0
        self.bus_type = "government"
        self.throttle = False
        self.brake = False
        self.steer_left = False
        self.steer_right = False
        self.keys = {k: False for k in ("w", "s", "a", "d")}
        for k in self.keys:
            self.accept(k, self.set_key, [k, True])
            self.accept(k + "-up", self.set_key, [k, False])
        self.accept("escape", self.userExit)
        self.accept("c", self.toggle_camera)
        self.accept("1", self.set_bus, ["government"])
        self.accept("2", self.set_bus, ["private"])

        self.world = self.render.attachNewNode("world")
        self._lighting()
        self._build_world()
        self.bus = self.world.attachNewNode("player_bus")
        self._build_bus()
        self._apply_bus_style()
        self._build_ui()
        self.taskMgr.add(self.update, "update")

    def _lighting(self):
        ambient = AmbientLight("ambient")
        ambient.setColor(Vec4(0.68, 0.68, 0.72, 1))
        self.render.setLight(self.render.attachNewNode(ambient))
        sun = DirectionalLight("sun")
        sun.setColor(Vec4(0.85, 0.84, 0.78, 1))
        sun_np = self.render.attachNewNode(sun)
        sun_np.setHpr(-30, -50, 0)
        self.render.setLight(sun_np)

    def _build_world(self):
        # Flat ground
        cm = CardMaker("ground")
        cm.setFrame(-180, 180, -220, 220)
        ground = self.world.attachNewNode(cm.generate())
        ground.setP(-90)
        ground.setZ(-0.12)
        ground.setColor(0.20, 0.42, 0.20, 1)
        ground.setTwoSided(True)

        road = CardMaker("road")
        road.setFrame(-6, 6, -210, 210)
        road_np = self.world.attachNewNode(road.generate())
        road_np.setP(-90)
        road_np.setZ(0.01)
        road_np.setColor(0.16, 0.17, 0.18, 1)
        road_np.setTwoSided(True)

        for y in range(-200, 205, 12):
            dash = CardMaker("center_line")
            dash.setFrame(-0.10, 0.10, -2.6, 2.6)
            n = self.world.attachNewNode(dash.generate())
            n.setP(-90)
            n.setPos(0, y, 0.03)
            n.setColor(0.95, 0.86, 0.52, 1)
            n.setTwoSided(True)
        for x in (-6.25, 6.25):
            edge = CardMaker("road_edge")
            edge.setFrame(-0.07, 0.07, -210, 210)
            n = self.world.attachNewNode(edge.generate())
            n.setP(-90)
            n.setX(x)
            n.setZ(0.035)
            n.setColor(0.9, 0.9, 0.8, 1)
            n.setTwoSided(True)

        # Sparse scenery: fewer objects for low-end GPU.
        for y in range(-180, 190, 36):
            for x in (-12, 12):
                cube(self.world, "tree_trunk", (x, y, 0.65), (0.18, 0.18, 0.65), (0.30, 0.16, 0.07, 1))
                cube(self.world, "tree_top", (x, y, 1.65), (0.72, 0.72, 0.95), (0.10, 0.34, 0.10, 1))
            if y % 72 == 0:
                cube(self.world, "roadside_shop", (-20, y, 1.0), (1.8, 2.2, 1.0), (0.68, 0.52, 0.32, 1))
                cube(self.world, "roadside_shop", (20, y, 1.0), (1.8, 2.2, 1.0), (0.68, 0.60, 0.48, 1))

    def _build_bus(self):
        self.body = cube(self.bus, "bus_body", (0, 0, 1.20), (1.15, 2.8, 0.90), (1, 1, 1, 1))
        self.windows = cube(self.bus, "bus_windows", (0, 0.0, 1.85), (1.17, 2.15, 0.30), (0.12, 0.42, 0.58, 1))
        self.roof = cube(self.bus, "bus_roof", (0, 0.0, 2.17), (1.10, 2.25, 0.12), (1, 1, 1, 1))
        self.front = cube(self.bus, "bus_front", (0, -2.78, 1.08), (1.10, 0.07, 0.42), (0.85, 0.85, 0.78, 1))
        for x in (-1.08, 1.08):
            for y in (-1.85, 1.85):
                cube(self.bus, "wheel", (x, y, 0.48), (0.18, 0.42, 0.42), (0.04, 0.04, 0.04, 1))

    def _build_ui(self):
        self.hud = DirectLabel(
            text="Loading...", scale=0.052, pos=(-1.28, 0, 0.91),
            text_align=TextNode.ALeft, text_fg=(1,1,1,1),
            frameColor=(0.02,0.02,0.02,0.55), frameSize=(-0.04, 0.68, -0.20, 0.08),
            relief=DGG.FLAT
        )
        self.help = DirectLabel(
            text="TAP ACCEL TOGGLE  |  BRAKE  |  STEER  |  CAMERA",
            scale=0.034, pos=(0,0,-0.95), text_fg=(1,1,1,1),
            frameColor=(0.02,0.02,0.02,0.5), frameSize=(-0.75,0.75,-0.10,0.10),
            relief=DGG.FLAT
        )
        # Big touch targets. Taps toggle accelerator/brake and briefly steer.
        self.throttle_btn = DirectButton(
            text="ACCEL\nON/OFF", scale=0.09, pos=(0.98,0,-0.69),
            command=self.toggle_throttle, frameColor=(0.05,0.45,0.10,0.90),
            text_fg=(1,1,1,1), text_scale=0.55, relief=DGG.FLAT
        )
        self.brake_btn = DirectButton(
            text="BRAKE", scale=0.085, pos=(0.73,0,-0.79),
            command=self.toggle_brake, frameColor=(0.65,0.05,0.05,0.90),
            text_fg=(1,1,1,1), text_scale=0.60, relief=DGG.FLAT
        )
        self.left_btn = DirectButton(
            text="◀ LEFT", scale=0.078, pos=(-0.95,0,-0.76),
            command=self.steer_once, extraArgs=[-1],
            frameColor=(0.08,0.18,0.45,0.90), text_fg=(1,1,1,1), text_scale=0.62, relief=DGG.FLAT
        )
        self.right_btn = DirectButton(
            text="RIGHT ▶", scale=0.078, pos=(-0.67,0,-0.76),
            command=self.steer_once, extraArgs=[1],
            frameColor=(0.08,0.18,0.45,0.90), text_fg=(1,1,1,1), text_scale=0.62, relief=DGG.FLAT
        )
        self.camera_btn = DirectButton(
            text="CAM", scale=0.065, pos=(0.45,0,0.82),
            command=self.toggle_camera, frameColor=(0.1,0.1,0.1,0.75),
            text_fg=(1,1,1,1), text_scale=0.65, relief=DGG.FLAT
        )
        self.bus_btn = DirectButton(
            text="BUS: GOV/PRIVATE", scale=0.058, pos=(0.82,0,0.86),
            command=self.toggle_bus, frameColor=(0.1,0.1,0.1,0.75),
            text_fg=(1,1,1,1), text_scale=0.58, relief=DGG.FLAT
        )

    def _apply_bus_style(self):
        style = BUS_STYLES[self.bus_type]
        self.body.setColor(*style["body"])
        self.roof.setColor(*style["roof"])

    def set_key(self, key, value):
        self.keys[key] = value

    def toggle_throttle(self):
        self.throttle = not self.throttle
        self.throttle_btn["text"] = "ACCEL\nON" if self.throttle else "ACCEL\nOFF"

    def toggle_brake(self):
        self.brake = not self.brake
        self.brake_btn["text"] = "BRAKE\nON" if self.brake else "BRAKE\nOFF"

    def steer_once(self, direction):
        self.heading += direction * 8.0

    def toggle_camera(self):
        self.camera_mode = 1 - self.camera_mode

    def toggle_bus(self):
        self.bus_type = "private" if self.bus_type == "government" else "government"
        self._apply_bus_style()

    def set_bus(self, bus_type):
        self.bus_type = bus_type
        self._apply_bus_style()

    def update(self, task):
        dt = min(globalClock.getDt(), 0.05)
        accel = self.keys["w"] or self.throttle
        brake = self.keys["s"] or self.brake
        if accel and not brake:
            self.speed = min(self.speed + 5.5 * dt, 17.0)
        elif brake:
            if self.speed > 0:
                self.speed = max(0, self.speed - 11.0 * dt)
            else:
                self.speed = max(-3.0, self.speed - 2.0 * dt)
        else:
            self.speed *= max(0, 1.0 - 0.45 * dt)

        steer = (1 if self.keys["a"] else 0) - (1 if self.keys["d"] else 0)
        self.heading += steer * self.speed * 1.3 * dt
        angle = math.radians(self.heading)
        self.bus.setX(self.bus, math.sin(angle) * self.speed * dt)
        self.bus.setY(self.bus, math.cos(angle) * self.speed * dt)
        self.bus.setH(self.heading)

        if self.camera_mode == 0:
            self.camera.setPos(self.bus.getPos() + Vec3(0, -10, 4.8))
            self.camera.lookAt(self.bus.getPos() + Vec3(0, 1.5, 1.1))
        else:
            self.camera.setPos(self.bus.getPos() + Vec3(0, -0.1, 2.65))
            self.camera.setHpr(self.bus.getH(), 0, 0)

        style = BUS_STYLES[self.bus_type]
        self.hud["text"] = (
            f"{style['label']}\\n"
            f"SPEED: {abs(self.speed)*3.6:4.0f} km/h\\n"
            f"CAMERA: {'CHASE' if self.camera_mode == 0 else 'CABIN'}"
        )
        return Task.cont


if __name__ == "__main__":
    BusGame().run()
