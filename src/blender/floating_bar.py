"""
KONGOR TOOL - Floating Navigation Bar (HUD)
Renders a sleek, modern interactive toolbar floating directly above the Timeline in the 3D Viewport.
Built with native GPU 2D shader drawing and non-intrusive event handling.
"""

import bpy
import blf
import gpu
from gpu_extras.batch import batch_for_shader

_instance = None

BUTTONS = [
    {"id": "dialog", "label": "KONGOR Tool", "width": 105, "op": "kongor.dialog"},
    {"id": "imp_model", "label": "Import Model", "width": 105, "op": "kongor.import_model"},
    {"id": "exp_model", "label": "Export Model", "width": 105, "op": "kongor.export_model"},
    {"id": "imp_clip", "label": "Import Clip", "width": 95, "op": "kongor.import_clip"},
    {"id": "exp_clip", "label": "Export Clip", "width": 95, "op": "kongor.export_clip"},
    {"id": "inspect", "label": "Inspect", "width": 70, "op": "kongor.inspect_scene"},
]

def draw_quad_2d(shader, x, y, w, h, color):
    coords = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    indices = [(0, 1, 2), (0, 2, 3)]
    batch = batch_for_shader(shader, "TRIS", {"pos": coords}, indices=indices)
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)

class KONGOR_OT_floating_bar(bpy.types.Operator):
    """Toggle floating navbar above Timeline in 3D Viewport"""
    bl_idname = "kongor.floating_bar"
    bl_label = "KONGOR Floating Navbar"
    bl_options = {"INTERNAL"}

    _handle = None
    hovered_index = -1
    bar_x = 0
    bar_y = 20
    bar_width = 0
    bar_height = 34
    button_rects = []

    def get_button_layout(self, region_width):
        padding = 5
        total_btn_w = sum(b["width"] for b in BUTTONS)
        total_w = total_btn_w + (len(BUTTONS) + 1) * padding
        bar_x = max(10, int((region_width - total_w) / 2))
        bar_y = 22
        bar_h = 34

        rects = []
        cur_x = bar_x + padding
        for b in BUTTONS:
            bw = b["width"]
            bh = bar_h - (padding * 2)
            by = bar_y + padding
            rects.append((cur_x, by, bw, bh))
            cur_x += bw + padding

        return bar_x, bar_y, total_w, bar_h, rects

    def draw_callback_px(self, context):
        if not context.region or context.region.type != "WINDOW":
            return

        region_w = context.region.width
        bar_x, bar_y, bar_w, bar_h, btn_rects = self.get_button_layout(region_w)
        self.bar_x = bar_x
        self.bar_y = bar_y
        self.bar_width = bar_w
        self.bar_height = bar_h
        self.button_rects = btn_rects

        shader = gpu.shader.from_builtin("UNIFORM_COLOR")

        # 1. Bar Shadow / Background
        draw_quad_2d(shader, bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2, (0.05, 0.05, 0.07, 0.95))
        draw_quad_2d(shader, bar_x, bar_y, bar_w, bar_h, (0.13, 0.14, 0.18, 0.92))

        # 2. Bar Border Outline
        border_col = (0.28, 0.32, 0.42, 0.85)
        draw_quad_2d(shader, bar_x, bar_y, bar_w, 1, border_col)
        draw_quad_2d(shader, bar_x, bar_y + bar_h - 1, bar_w, 1, border_col)
        draw_quad_2d(shader, bar_x, bar_y, 1, bar_h, border_col)
        draw_quad_2d(shader, bar_x + bar_w - 1, bar_y, 1, bar_h, border_col)

        # 3. Draw Buttons
        font_id = 0
        blf.size(font_id, 12)

        for idx, (b_info, (bx, by, bw, bh)) in enumerate(zip(BUTTONS, btn_rects)):
            is_hover = (idx == self.hovered_index)
            btn_bg = (0.22, 0.42, 0.85, 0.90) if is_hover else (0.19, 0.21, 0.26, 0.85)
            draw_quad_2d(shader, bx, by, bw, bh, btn_bg)

            # Button border
            b_border = (0.40, 0.60, 1.00, 0.9) if is_hover else (0.26, 0.28, 0.35, 0.7)
            draw_quad_2d(shader, bx, by, bw, 1, b_border)
            draw_quad_2d(shader, bx, by + bh - 1, bw, 1, b_border)
            draw_quad_2d(shader, bx, by, 1, bh, b_border)
            draw_quad_2d(shader, bx + bw - 1, by, 1, bh, b_border)

            # Text
            text = b_info["label"]
            tw, th = blf.dimensions(font_id, text)
            tx = bx + int((bw - tw) / 2)
            ty = by + int((bh - th) / 2) + 2

            if is_hover:
                blf.color(font_id, 1.0, 1.0, 1.0, 1.0)
            else:
                blf.color(font_id, 0.88, 0.90, 0.94, 0.95)

            blf.position(font_id, tx, ty, 0)
            blf.draw(font_id, text)

    def modal(self, context, event):
        global _instance
        if _instance != self:
            self.cancel(context)
            return {"CANCELLED"}

        # Only process in 3D Viewport
        if not context.area or context.area.type != "VIEW_3D":
            return {"PASS_THROUGH"}

        mx = event.mouse_region_x
        my = event.mouse_region_y

        # Check button hover
        new_hover = -1
        for idx, (bx, by, bw, bh) in enumerate(self.button_rects):
            if bx <= mx <= bx + bw and by <= my <= by + bh:
                new_hover = idx
                break

        if event.type == "MOUSEMOVE":
            if new_hover != self.hovered_index:
                self.hovered_index = new_hover
                context.area.tag_redraw()
            return {"PASS_THROUGH"}

        # Left Click on a Button
        if event.type == "LEFTMOUSE" and event.value == "PRESS":
            if new_hover >= 0:
                target_op = BUTTONS[new_hover]["op"]
                try:
                    op_mod, op_name = target_op.split(".")
                    op_func = getattr(getattr(bpy.ops, op_mod), op_name)
                    op_func("INVOKE_DEFAULT")
                except Exception as e:
                    self.report({"ERROR"}, f"Action failed: {e}")
                context.area.tag_redraw()
                return {"RUNNING_MODAL"}

            # Click inside the bar container
            if self.bar_x <= mx <= self.bar_x + self.bar_width and self.bar_y <= my <= self.bar_y + self.bar_height:
                return {"RUNNING_MODAL"}

        return {"PASS_THROUGH"}

    def invoke(self, context, event):
        global _instance
        if _instance is not None:
            # Stop existing instance
            old_inst = _instance
            _instance = None
            old_inst.cancel(context)
            self.report({"INFO"}, "Floating navbar hidden.")
            return {"CANCELLED"}

        self._handle = None
        self.hovered_index = -1
        self.bar_x = 0
        self.bar_y = 20
        self.bar_width = 0
        self.bar_height = 34
        self.button_rects = []

        _instance = self
        self._handle = bpy.types.SpaceView3D.draw_handler_add(
            self.draw_callback_px, (context,), "WINDOW", "POST_PIXEL"
        )
        context.window_manager.modal_handler_add(self)
        if context.area:
            context.area.tag_redraw()
        return {"RUNNING_MODAL"}

    def cancel(self, context):
        if self._handle is not None:
            try:
                bpy.types.SpaceView3D.draw_handler_remove(self._handle, "WINDOW")
            except Exception:
                pass
            self._handle = None
        if context and context.area:
            context.area.tag_redraw()

classes = (
    KONGOR_OT_floating_bar,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    global _instance
    if _instance is not None:
        inst = _instance
        _instance = None
        inst.cancel(bpy.context)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
