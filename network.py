#!/usr/bin/env python
import tkinter as tk
import networkx as nx
import numpy as np

import subprocess


from LatexZettel import analysis


class Node:
    def __init__(self, x = 0, y = 0):
       self.x = x
       self.y = y



class App(tk.Tk):
    radius = 2
    circle_color='red'

    def __init__(self, network):
        super().__init__()
        self.title('LaTeX Zettel Network')
        self.canvas = tk.Canvas(self, width=1000, height=700, bg='white', bd=0, highlightthickness=0)
        self.canvas.pack(expand=True)
        self.update()
        
        self.width = self.canvas.winfo_width()
        self.height = self.canvas.winfo_height()

        self.canvas.bind('<1>', self.select_circle)
        self.canvas.bind('<Double-1>', self.open_pdf)

        self.canvas.bind('<MouseWheel>', self.rescale)
        self.canvas.bind('<Button-4>', lambda event: self.rescale(event, 0.1))
        self.canvas.bind('<Button-5>', lambda event: self.rescale(event, -0.1))

        self.bind("<Configure>", self.resize)

        self.selected = None

        self.network = network
        self.positions = nx.nx_agraph.graphviz_layout(self.network)



        #calculate positions
       
        self.nodes = {}
        self.node_ids = {}
        self.text_ids = {}

        self.edges = {}
        self.node_edges = {}

        self.selected_node = None
        self.dragging_canvas = None
        self.drag_start_position = None
        

        self.scale = 1 

        for name in self.network.nodes:
            self.nodes[name] = Node(self.positions[name][0], self.positions[name][1])

        for node in self.nodes:
            node_id, text_id = self._add_node_circle(node)
            self.node_ids[node_id] = node 
            self.text_ids[node_id] = text_id 

            self.node_edges[node_id] = []

            self.canvas.addtag_withtag('node', node_id)

        for source, dest in self.network.edges:
            edge_id = self._add_edge_line(source, dest)
            source_id = [node_id for node_id, node in self.node_ids.items() if node == source][0]
            dest_id = [node_id for node_id, node in self.node_ids.items() if node == dest][0]
            self.edges[edge_id] = (source_id, dest_id)
            
            self.canvas.addtag_withtag('edge', edge_id)

            self.node_edges[source_id].append(edge_id)
            self.node_edges[dest_id].append(edge_id)

        for node in self.node_ids:
            self.canvas.tag_raise('node')
        
    def resize(self, event):
        self.canvas.config(width=event.width, height=event.height)


    def rescale(self, event, delta=None):
        scale = np.exp(event.delta)

        if delta is not None:
            scale = np.exp(delta)

        self.scale *= scale



        self.canvas.scale('all', event.x, event.y, scale, scale)


    def convert_coordinates(self, x, y):
        xs = [n.x for n in self.nodes.values()]
        ys = [n.y for n in self.nodes.values()]

        max_x = np.max(xs)
        max_y = np.max(ys)
        min_x = np.min(xs)
        min_y = np.min(ys)

        range_x = max_x - min_x
        range_y = max_y - min_y

        padding = 0.05

        max_x = max_x + 0.05 * range_x
        min_x = min_x - 0.05 * range_x
        max_y = max_y + 0.05 * range_y
        min_y = min_y - 0.05 * range_y
        range_x = max_x - min_x
        range_y = max_y - min_y

        return (x - min_x) / (range_x) * self.width, (y - min_y) / (range_y) * self.height



    def _add_node_circle(self, node):
        x, y = self.convert_coordinates(self.nodes[node].x, self.nodes[node].y)
        node_id = self.canvas.create_oval(x-self.radius, y-self.radius, x+self.radius, y+self.radius, outline='black', fill=self.circle_color)
        text_id = self.canvas.create_text(x, y + self.radius * 2.5, text=' '.join([s.capitalize() for s in node.split('_')]))
        return node_id, text_id

    def _calculate_end_offset(self, x0, y0, x1, y1):
        dx = x1 - x0
        dy = y1 - y0
        dy1 = np.sign(dy) * np.sqrt(self.radius ** 2 / (1 +  dx ** 2 / dy ** 2))
        dx1 = dx / dy * dy1
        x1 -= dx1 * self.scale
        y1 -= dy1 * self.scale

        return x1, y1



    def _add_edge_line(self, source, dest):
        x0, y0 = self.convert_coordinates(self.nodes[source].x, self.nodes[source].y)
        x1, y1 = self.convert_coordinates(self.nodes[dest].x, self.nodes[dest].y)
        dx = x1 - x0
        dy = y1 - y0
        if dx == 0 or dy == 0:
            return self.canvas.create_line(x0, y0, x1, y1, arrow=tk.LAST)

        x1, y1 = self._calculate_end_offset(x0, y0, x1, y1)

        return self.canvas.create_line(x0, y0, x1, y1, arrow=tk.LAST)


    def select_circle(self, event):

        nodes = [node for node in self.canvas.find_withtag(tk.CURRENT) if node in self.node_ids]
        
        self.canvas.bind('<Motion>', self.move_circle)
        self.canvas.bind('<ButtonRelease-1>', self.deselect)
        
        if len(nodes) == 0:
            self.dragging_canvas = True
            self.drag_start_position = np.array([event.x, event.y])
            return

        node = nodes[0]



        self.canvas.addtag_withtag('selected', node) 
        nodes = self.canvas.find_withtag(tk.CURRENT)
        try:
            self.selected_node = nodes[0]
        except KeyError:
            pass

    def open_pdf(self, event):
        clicked = self.canvas.find_withtag(tk.CURRENT)
        try:
            node_id = clicked[0]
            filename = self.node_ids[node_id]
            subprocess.call(['xdg-open', f'pdf/{filename}.pdf'])
        except KeyError:
            pass



    def move_circle(self, event):
        if self.dragging_canvas:
            position = np.array([event.x, event.y])
            delta = position - self.drag_start_position
            self.drag_start_position = position

            elements = self.canvas.find_all()
            for element in elements:
                coords = np.array(self.canvas.coords(element))
                for i in range(coords.size):
                    coords[i] += delta[i % 2]

                self.canvas.coords(element, *coords)

            return 


        x, y, r = event.x, event.y, self.radius * self.scale
        self.canvas.coords('selected', x-r, y-r, x+r, y+r)
        self.canvas.coords(self.text_ids[self.selected_node], x, y + r * 2.5)

        edges = self.node_edges[self.selected_node]
        for edge in edges:
            edge_coords = self.canvas.coords(edge)
            if self.selected_node == self.edges[edge][0]:
                self.canvas.coords(edge, x, y, edge_coords[2], edge_coords[3])
            elif self.selected_node == self.edges[edge][1]:
                dy = edge_coords[3] - edge_coords[1]
                dx = edge_coords[2] - edge_coords[0]
                if dx == 0 or dy == 0:
                    self.canvas.coords(edge, edge_coords[0], edge_coords[1], x, y)
                x1, y1 = self._calculate_end_offset(*edge_coords[:2], x, y)
                self.canvas.coords(edge, edge_coords[0], edge_coords[1], x1, y1)

    def deselect(self, event):
        self.canvas.dtag('selected')    # removes the 'selected' tag
        self.canvas.unbind('<Motion>')
        self.selected_node = None
        self.dragging_canvas = False


if __name__ == '__main__':
    notes, matrix = analysis.calculate_adjacency_matrix()
    network = nx.DiGraph(matrix)
    network = nx.relabel_nodes(network, {i: note.filename for i, note in enumerate(notes)})
    App(network).mainloop()

