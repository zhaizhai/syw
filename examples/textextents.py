#!/usr/bin/env python

import pygtk
pygtk.require('2.0')

import gobject
import pango
import gtk
import math
import time
from gtk import gdk
try:
    import cairo
except ImportError:
    pass

if gtk.pygtk_version < (2,3,93):
    print "PyGtk 2.3.93 or later required"
    raise SystemExit


TEXT = 'cairo'
BORDER_WIDTH = 10

def progress_timeout(object):
    x, y, w, h = object.allocation
    object.window.invalidate_rect((0,0,w,h),False)
    return True

class PyGtkWidget(gtk.Widget):
    __gsignals__ = { 'realize': 'override',
                     'expose-event' : 'override',
                     'size-allocate': 'override',
                     'size-request': 'override',}

    def __init__(self):
        gtk.Widget.__init__(self)
        self.draw_gc = None
        self.layout = self.create_pango_layout(TEXT)
        self.layout.set_font_description(pango.FontDescription("sans serif 8"))
        self.timer = gobject.timeout_add (1000, progress_timeout, self)
                                           
    def do_realize(self):
        self.set_flags(self.flags() | gtk.REALIZED)
        self.window = gdk.Window(self.get_parent_window(),
                                 width=self.allocation.width,
                                 height=self.allocation.height,
                                 window_type=gdk.WINDOW_CHILD,
                                 wclass=gdk.INPUT_OUTPUT,
                                 event_mask=self.get_events() | gdk.EXPOSURE_MASK)
        if not hasattr(self.window, "cairo_create"):
            self.draw_gc = gdk.GC(self.window,
                                  line_width=5,
                                  line_style=gdk.SOLID,
                                  join_style=gdk.JOIN_ROUND)

	self.window.set_user_data(self)
        self.style.attach(self.window)
        self.style.set_background(self.window, gtk.STATE_NORMAL)
        self.window.move_resize(*self.allocation)

    def do_size_request(self, requisition):
	width, height = self.layout.get_size()
	requisition.width = (width // pango.SCALE + BORDER_WIDTH*4)* 1.45
	requisition.height = (3 * height // pango.SCALE + BORDER_WIDTH*4) * 1.2

    def do_size_allocate(self, allocation):
        self.allocation = allocation
        if self.flags() & gtk.REALIZED:
            self.window.move_resize(*allocation)

    def _expose_gdk(self, event):
        x, y, w, h = self.allocation
        self.layout = self.create_pango_layout('no cairo')
        fontw, fonth = self.layout.get_pixel_size()
        self.style.paint_layout(self.window, self.state, False,
                                event.area, self, "label",
                                (w - fontw) / 2, (h - fonth) / 2,
                                self.layout)
        
    def _expose_cairo(self, event, cr):

        text = 'joy'

	# Example is in 26.0 x 1.0 coordinate space 
	cr.scale (240, 240)
	cr.set_font_size (0.5)

        # Drawing

	cr.set_source_rgb (0.0, 0.0, 0.0)
	cr.select_font_face ("Georgia",
                             cairo.FONT_SLANT_NORMAL, 
                             cairo.FONT_WEIGHT_BOLD)
	ux, uy = cr.device_to_user_distance (1, 1)
        px = max((ux, uy))

	ascent, descent, fe_height, \
            max_x_advance, max_y_advance = cr.font_extents ()
	x_bearing, y_bearing, te_width, te_height, \
            x_advance, y_advance = cr.text_extents (text)
	x = 0.5 - x_bearing - te_width / 2
	y = 0.5 - descent + fe_height / 2

        # baseline, descent, ascent, height
	cr.set_line_width (4*px)
	dashlength = 9*px
	cr.set_dash ((1, 0))
	cr.set_source_rgba (0, 0.6, 0, 0.5)
	cr.move_to (x + x_bearing, y)
	cr.rel_line_to (te_width, 0)
	cr.move_to (x + x_bearing, y + descent)
	cr.rel_line_to (te_width, 0)
	cr.move_to (x + x_bearing, y - ascent)
	cr.rel_line_to (te_width, 0)
	cr.move_to (x + x_bearing, y - fe_height)
	cr.rel_line_to (te_width, 0)
	cr.stroke ()

        # extents: width and height
	cr.set_source_rgba (0, 0, 0.75, 0.5)
	cr.set_line_width (px)
	dashlength = 3*px
	cr.set_dash ((1, 0))
	cr.rectangle (x + x_bearing, y + y_bearing, 
                      te_width, te_height)
	cr.stroke ()

        # text
	cr.move_to (x, y)
	cr.set_source_rgb (0, 0, 0)
	cr.show_text (text)

        # bearing
	cr.set_dash ((1, 0))
	cr.set_line_width (2 * px)
	cr.set_source_rgba (0, 0, 0.75, 0.5)
	cr.move_to (x, y)
	cr.rel_line_to (x_bearing, y_bearing)
	cr.stroke ()

        # text's advance
	cr.set_source_rgba (0, 0, 0.75, 0.5)
	cr.arc (x + x_advance, y + y_advance, 
                5 * px, 0, 2 * math.pi)
	cr.fill ()

        # reference point
	cr.arc (x, y, 5 * px, 0, 2 * math.pi)
	cr.set_source_rgba (0.75, 0, 0, 0.5)
	cr.fill ()

        # pango layout 

        x, y, w, h = self.allocation        
        fontw, fonth = self.layout.get_pixel_size()
        cr.move_to((w - fontw - 4), (h - fonth ))
        cr.update_layout(self.layout)
        cr.show_layout(self.layout)
        
    def do_expose_event(self, event):
        self.chain(event)
        try:
            cr = self.window.cairo_create()
        except AttributeError:
            return self._expose_gdk(event)
        return self._expose_cairo(event, cr)

win = gtk.Window()
win.set_title('clock')
win.connect('delete-event', gtk.main_quit)

event_box = gtk.EventBox()
event_box.connect("button_press_event", lambda w,e: win.set_decorated(not win.get_decorated()))

win.add(event_box)

w = PyGtkWidget()
event_box.add(w)

win.move(gtk.gdk.screen_width() - 120, 40)
win.show_all()

gtk.main()

