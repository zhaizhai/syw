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

from notation import DefaultNotation, OpNotation, ModifierNotation, Notation

SPACING = 0.48

NOTATIONS = {'add': OpNotation('+'),
             'sum': OpNotation('+', if_no_args=['0']),
             'sub': OpNotation('-'),
             'mult': OpNotation('', if_no_args=['1']),
             'div': OpNotation('---', flow=Notation.VERT_FLOW),
             'neg': ModifierNotation('-'),
             'equals': OpNotation('=')}
DEFAULT_NOTATION = DefaultNotation()

def make_notation(node):
    if node.name() in NOTATIONS:
        return NOTATIONS[node.name()].get_notation(node)
    return DEFAULT_NOTATION.get_notation(node)

def get_cairo_dim(cr, text):
    # width, height = cr.text_extents(text)[2:4]
    height, width = cr.text_extents(text)[1:3]
    return (width + 2 * SPACING, abs(height) + 2 * SPACING)

def render_text(cr, text, x, y):
    w, h = get_cairo_dim(cr, text)
    cr.move_to(x + SPACING, y - SPACING + h)
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
        self.width, self.height = None, None

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
            orient, notation = make_notation(self.node)

            for elt in notation:
                w, h = (get_cairo_dim(cr, elt) 
                        if isinstance(elt, str) else 
                        self.display.display_nodes[self.node.children[elt]].get_node_box(cr))

                if orient == Notation.HORIZ_FLOW:
                    height = max((h, height))
                    width += w
                elif orient == Notation.VERT_FLOW:
                    width = max((w, width))
                    height += h
                else:
                    raise Exception("Invalid orientation %r" % orient)

            return width, height

    def render_vert(self, cr, x, y, notation_elts):
        # TODO: actually make vert
        for elt in notation_elts:
            w, h = None, None

            if isinstance(elt, str):
                w, h = get_cairo_dim(cr, elt)
                render_text(cr, elt, x + (self.width - w) / 2, y)
            else:
                # TODO: this is rather clunky
                child_display = self.display.display_nodes[self.node.children[elt]]
                w, h = child_display.get_node_box(cr)
                child_display.render_node_box(cr, x + (self.width - w) / 2, y)

            y += h

    def render_horiz(self, cr, x, y, notation_elts):
        for elt in notation_elts:
            w, h = None, None

            if isinstance(elt, str):
                w, h = get_cairo_dim(cr, elt)
                render_text(cr, elt, x, y + (self.height - h) / 2)
            else:
                # TODO: this is rather clunky
                child_display = self.display.display_nodes[self.node.children[elt]]
                w, h = child_display.get_node_box(cr)
                child_display.render_node_box(cr, x, y + (self.height - h) / 2)

            x += w + (0.005 if elt == ',' else 0.0)


    def render_node_box(self, cr, x, y):
        self.width, self.height = self.get_node_box(cr)
        self.bbox = (x, y, x + self.width, y + self.height)

        if isinstance(self.node, ValueNode):
            render_text(cr, self.node.name(), x, y)
        else:
            orient, notation_elts = make_notation(self.node)
            
            assert orient in (Notation.HORIZ_FLOW, Notation.VERT_FLOW)
            if orient == Notation.HORIZ_FLOW:
                self.render_horiz(cr, x, y, notation_elts)
            else:
                self.render_vert(cr, x, y, notation_elts)


class App:
    def __init__(self, root, rules, auto_rules):
        self.win = gtk.Window()
        self.win.set_default_size(500, 300)
        self.win.set_title('eqns')
        self.win.connect('delete-event', gtk.main_quit)

        self.root = root
        self.rules = rules
        self.auto_rules = auto_rules

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

        to_reach = self.disp.get_node(e.x, e.y)
        print_node(self.root)

        if None not in (self.to_move, to_reach):
            manip = Manipulator(self.root, self.rules)
            manip.move_towards(self.to_move, to_reach, desired_parent=None) # TODO
            self.root = manip.root
            self.root = apply_auto(self.root, self.auto_rules)
            self.disp.reinit(self.root)
            # new_root = move_towards(self.root, self.to_move, to_reach, self.rules)
            # if new_root is not None:
            #     self.root = new_root
            #     # print_node(self.root)
            #     # self.root.validate()
            #     self.root = apply_auto(self.root, self.auto_rules)
            #     self.disp.reinit(self.root)

        self.to_move = None
        self.hover = None
        self.redraw()

    def expose(self, widget, event):
        cr = widget.window.cairo_create()

        cr.set_font_size (40)

        # Drawing

        cr.set_source_rgb (1, 1, 1)
        cr.rectangle(0, 0, 500, 300)
        cr.fill()

        cr.set_source_rgb (0.0, 0.0, 0.0)
        cr.select_font_face ("Times",
                             cairo.FONT_SLANT_NORMAL, 
                             cairo.FONT_WEIGHT_BOLD)

        self.disp.display_nodes[self.root].render_node_box(cr, 120, 120)

        if self.hover is not None:
            cr.set_source_rgba (0, 0, 1, 0.2)
            x1, y1, x2, y2 = self.disp.display_nodes[self.hover].bbox
            cr.rectangle(x1, y1, x2 - x1, y2 - y1)
            cr.fill()



        



if __name__ == '__main__':

    def sub(a, b):
        return a - b

    def add(a, b):
        return a + b

    def div(a, b):
        return a / b

    def mult(a, b):
        return a * b

    def _sum(*n):
        return sum(*n)

    def neg(x):
        return -x

    def equals(x, y):
        return x == y

    ft = RefTable()
#    ft.add_variable('add', Function('add', add, 2))
#    ft.add_variable('sub', Function('sub', sub, 2))
    ft.add_variable('div', Function('div', sub, 2,
                                    precedence=300))
    ft.add_variable('mult', Function('mult', sub, None,
                                     precedence=300))

    ft.add_variable('sum', Function('sum', _sum, None,
                                    precedence=200))
    ft.add_variable('neg', Function('neg', neg, 1))

    ft.add_variable('equals', 
                    Function('equals', equals, 2, precedence=100))

    pivot_rules, auto_rules = load_from_file('rules-new.txt', ft)

#    root = parse('equals(sum(x,y,z),w)', ft)
#    root = parse('equals(sum(div(x,y),z),w)', ft)
    root = parse('equals(div(x, sum(y, div(x, z))), w)', ft)
    print_node(root)

    App(root, pivot_rules, auto_rules)
