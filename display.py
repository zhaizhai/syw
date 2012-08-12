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

from core import *
from rules import *
from simplify import *

SPACING = 0.48



def sub(a, b):
    return a - b

def add(a, b):
    return a + b

def equals(a, b):
    return a == b



def get_cairo_dim(cr, text):
    width, height = cr.text_extents(text)[2:4]
    return (width + 2 * SPACING, height + 2 * SPACING)

def render_text(cr, text, x, y):
    w, h = get_cairo_dim(cr, text)
    cr.move_to(x + SPACING, y + SPACING + h)
    cr.show_text(text)

class Display(object):
    def __init__(self, root):
        self.reinit(root)

    def reinit(self, root):
        self.root = root
        self.display_nodes = {}
        
        def make_display_node(node, depth=None):
            self.display_nodes[node] = DisplayNode(node, self)
        self.root.recurse(make_display_node)

    def get_node(self, x, y):
        
        def find_node(node):
            if not self.display_nodes[node].contains(x, y):
                return None
            for child in node.children:
                ret = find_node(child)
                if ret is not None:
                    return ret
            return node
                
        return find_node(self.root)
        


class DisplayNode(object):
    def __init__(self, node, display):
        self.node = node
        self.display = display
        self.bbox = None

    def contains(self, x, y):
        if self.bbox is None:
            return False
        x1, y1, x2, y2 = self.bbox
        return (x1 <= x and x <= x2 and y1 <= y and y <= y2)

    def get_node_box(self, cr):        
        if isinstance(self.node, ValueNode):
            return get_cairo_dim(cr, self.node.name())
        else:
            width, height = 0, 0
            notation = self.node.fn.notation
            for elt in notation:
                w, h = (get_cairo_dim(cr, elt) 
                        if isinstance(elt, str) else 
                        self.display.display_nodes[self.node.children[elt]].get_node_box(cr))
                if h > height:
                    height = h
                width += w
            return width, height

    def render_node_box(self, cr, x, y):
        width, height = self.get_node_box(cr)
        self.bbox = (x, y, x + width, y + height)

        if isinstance(self.node, ValueNode):
            render_text(cr, self.node.name(), x, y)
        else:
            notation = self.node.fn.notation

            for elt in notation:
                w, h = None, None

                if isinstance(elt, str):
                    w, h = get_cairo_dim(cr, elt)
                    render_text(cr, elt, x, y + (height - h) / 2)
                else:
                    child_display = self.display.display_nodes[self.node.children[elt]]
                    w, h = child_display.get_node_box(cr)
                    child_display.render_node_box(cr, x, y + (height - h) / 2)

                x += w + (0.005 if elt == ',' else 0.0)




class App:
    def __init__(self, root, rules):
        self.win = gtk.Window()
        self.win.set_default_size(500, 300)
        self.win.set_title('eqns')
        self.win.connect('delete-event', gtk.main_quit)

        self.root = root
        self.rules = rules
        self.disp = Display(self.root)
        self.to_move = None
        self.hover = None

        event_box = gtk.EventBox()
        event_box.connect("button_press_event", self.on_click)
        event_box.connect("button_release_event", self.on_release)
        event_box.connect("motion_notify_event", self.on_move)

        self.da = gtk.DrawingArea()
        self.da.connect("expose_event", self.expose)
        event_box.add(self.da)
        self.win.add(event_box)

        self.win.move(0, 0)
        self.win.show_all()
        gtk.main()

    def redraw(self):
        self.expose(self.da, None)

    def on_move(self, w, e):
        if e.is_hint:
            x, y, state = e.window.get_pointer()
        else:
            x = e.x
            y = e.y
            state = e.state
    
        if state & gtk.gdk.BUTTON1_MASK != 0:
            self.hover = self.disp.get_node(x, y)
            self.redraw()

    
    def on_click(self, w, e):
        assert e.button == 1
        print e.x, e.y
        self.to_move = self.disp.get_node(e.x, e.y)

    def on_release(self, w, e):
        print e.x, e.y
        # TODO: this is horrible... think of how to actually organize the class

        to_reach = self.disp.get_node(e.x, e.y)

        print 'moving', self.to_move, 'to', to_reach

        self.root = move_towards(self.root, self.to_move, to_reach, self.rules)
#        print_node(self.root)
#        self.root.validate()

        self.disp.reinit(self.root)
        self.to_move = None
        self.hover = None
        self.redraw()

    def expose(self, widget, event):
        cr = widget.window.cairo_create()

        cr.set_font_size (24)

        # Drawing

        cr.set_source_rgb (1, 1, 1)
        cr.rectangle(0, 0, 500, 300)
        cr.fill()

        cr.set_source_rgb (0.0, 0.0, 0.0)
        cr.select_font_face ("Georgia",
                             cairo.FONT_SLANT_NORMAL, 
                             cairo.FONT_WEIGHT_BOLD)

        self.disp.display_nodes[self.root].render_node_box(cr, 120, 120)

        if self.hover is not None:
            cr.set_source_rgba (0, 0, 1, 0.2)
            x1, y1, x2, y2 = self.disp.display_nodes[self.hover].bbox
            cr.rectangle(x1, y1, x2 - x1, y2 - y1)
            cr.fill()



        





ft = RefTable()
ft.add_variable('add', Function('add', add, 2, notation=['(', 0, '+', 1, ')']))
ft.add_variable('sub', Function('sub', sub, 2, notation=['(', 0, '-', 1, ')']))
ft.add_variable('equals', Function('equals', equals, 2, notation=[0, '=', 1]))

all_rules = []
with open('rules.txt') as f:
    for line in f:
        line = line.strip().replace(' ', '')
        if not line:
            continue

        first, second = line.split('=')
        all_rules.append(Rule(parse(first, ft), parse(second, ft)))

root = parse('equals(add(x,add(y,z)),w)', ft)
print_node(root)

App(root, all_rules)
