# coding=utf-8
"""
Geojson layer
=============

.. note::

    Currently experimental and a work in progress, not fully optimized.


Supports:

- html color in properties
- polygon geometry are cached and not redrawed when the parent mapview changes
- linestring are redrawed everymove, it's ugly and slow.
- marker are NOT supported

"""

__all__ = ["GeoJsonMapLayer"]

import json
from kivy.properties import StringProperty, ObjectProperty
from kivy.graphics import (Canvas, PushMatrix, PopMatrix, MatrixInstruction,
                           Translate, Scale)
from kivy.utils import get_color_from_hex
from mapview.view import MapLayer
from mapview.downloader import Downloader

COLORS = {
    'aqua': '#00ffff',
    'black': '#000000',
    'blue': '#0000ff',
    'fuchsia': '#ff00ff',
    'green': '#008000',
    'grey': '#808080',
    'lime': '#00ff00',
    'maroon': '#800000',
    'navy': '#000080',
    'olive': '#808000',
    'purple': '#800080',
    'red': '#ff0000',
    'silver': '#c0c0c0',
    'teal': '#008080',
    'white': '#ffffff',
    'yellow': '#ffff00',
    'aliceblue': '#f0f8ff',
    'antiquewhite': '#faebd7',
    'aqua': '#00ffff',
    'aquamarine': '#7fffd4',
    'azure': '#f0ffff',
    'beige': '#f5f5dc',
    'bisque': '#ffe4c4',
    'black': '#000000',
    'blanchedalmond': '#ffebcd',
    'blue': '#0000ff',
    'blueviolet': '#8a2be2',
    'brown': '#a52a2a',
    'burlywood': '#deb887',
    'cadetblue': '#5f9ea0',
    'chartreuse': '#7fff00',
    'chocolate': '#d2691e',
    'coral': '#ff7f50',
    'cornflowerblue': '#6495ed',
    'cornsilk': '#fff8dc',
    'crimson': '#dc143c',
    'cyan': '#00ffff',
    'darkblue': '#00008b',
    'darkcyan': '#008b8b',
    'darkgoldenrod': '#b8860b',
    'darkgray': '#a9a9a9',
    'darkgrey': '#a9a9a9',
    'darkgreen': '#006400',
    'darkkhaki': '#bdb76b',
    'darkmagenta': '#8b008b',
    'darkolivegreen': '#556b2f',
    'darkorange': '#ff8c00',
    'darkorchid': '#9932cc',
    'darkred': '#8b0000',
    'darksalmon': '#e9967a',
    'darkseagreen': '#8fbc8f',
    'darkslateblue': '#483d8b',
    'darkslategray': '#2f4f4f',
    'darkslategrey': '#2f4f4f',
    'darkturquoise': '#00ced1',
    'darkviolet': '#9400d3',
    'deeppink': '#ff1493',
    'deepskyblue': '#00bfff',
    'dimgray': '#696969',
    'dimgrey': '#696969',
    'dodgerblue': '#1e90ff',
    'firebrick': '#b22222',
    'floralwhite': '#fffaf0',
    'forestgreen': '#228b22',
    'fuchsia': '#ff00ff',
    'gainsboro': '#dcdcdc',
    'ghostwhite': '#f8f8ff',
    'gold': '#ffd700',
    'goldenrod': '#daa520',
    'gray': '#808080',
    'grey': '#808080',
    'green': '#008000',
    'greenyellow': '#adff2f',
    'honeydew': '#f0fff0',
    'hotpink': '#ff69b4',
    'indianred': '#cd5c5c',
    'indigo': '#4b0082',
    'ivory': '#fffff0',
    'khaki': '#f0e68c',
    'lavender': '#e6e6fa',
    'lavenderblush': '#fff0f5',
    'lawngreen': '#7cfc00',
    'lemonchiffon': '#fffacd',
    'lightblue': '#add8e6',
    'lightcoral': '#f08080',
    'lightcyan': '#e0ffff',
    'lightgoldenrodyellow': '#fafad2',
    'lightgray': '#d3d3d3',
    'lightgrey': '#d3d3d3',
    'lightgreen': '#90ee90',
    'lightpink': '#ffb6c1',
    'lightsalmon': '#ffa07a',
    'lightseagreen': '#20b2aa',
    'lightskyblue': '#87cefa',
    'lightslategray': '#778899',
    'lightslategrey': '#778899',
    'lightsteelblue': '#b0c4de',
    'lightyellow': '#ffffe0',
    'lime': '#00ff00',
    'limegreen': '#32cd32',
    'linen': '#faf0e6',
    'magenta': '#ff00ff',
    'maroon': '#800000',
    'mediumaquamarine': '#66cdaa',
    'mediumblue': '#0000cd',
    'mediumorchid': '#ba55d3',
    'mediumpurple': '#9370d8',
    'mediumseagreen': '#3cb371',
    'mediumslateblue': '#7b68ee',
    'mediumspringgreen': '#00fa9a',
    'mediumturquoise': '#48d1cc',
    'mediumvioletred': '#c71585',
    'midnightblue': '#191970',
    'mintcream': '#f5fffa',
    'mistyrose': '#ffe4e1',
    'moccasin': '#ffe4b5',
    'navajowhite': '#ffdead',
    'navy': '#000080',
    'oldlace': '#fdf5e6',
    'olive': '#808000',
    'olivedrab': '#6b8e23',
    'orange': '#ffa500',
    'orangered': '#ff4500',
    'orchid': '#da70d6',
    'palegoldenrod': '#eee8aa',
    'palegreen': '#98fb98',
    'paleturquoise': '#afeeee',
    'palevioletred': '#d87093',
    'papayawhip': '#ffefd5',
    'peachpuff': '#ffdab9',
    'peru': '#cd853f',
    'pink': '#ffc0cb',
    'plum': '#dda0dd',
    'powderblue': '#b0e0e6',
    'purple': '#800080',
    'red': '#ff0000',
    'rosybrown': '#bc8f8f',
    'royalblue': '#4169e1',
    'saddlebrown': '#8b4513',
    'salmon': '#fa8072',
    'sandybrown': '#f4a460',
    'seagreen': '#2e8b57',
    'seashell': '#fff5ee',
    'sienna': '#a0522d',
    'silver': '#c0c0c0',
    'skyblue': '#87ceeb',
    'slateblue': '#6a5acd',
    'slategray': '#708090',
    'slategrey': '#708090',
    'snow': '#fffafa',
    'springgreen': '#00ff7f',
    'steelblue': '#4682b4',
    'tan': '#d2b48c',
    'teal': '#008080',
    'thistle': '#d8bfd8',
    'tomato': '#ff6347',
    'turquoise': '#40e0d0',
    'violet': '#ee82ee',
    'wheat': '#f5deb3',
    'white': '#ffffff',
    'whitesmoke': '#f5f5f5',
    'yellow': '#ffff00',
    'yellowgreen': '#9acd32'
}


def flatten(l):
    return [item for sublist in l for item in sublist]


class GeoJsonMapLayer(MapLayer):

    source = StringProperty()
    geojson = ObjectProperty()
    initial_zoom = None
    first_time = True

    def __init__(self, **kwargs):
        super(GeoJsonMapLayer, self).__init__(**kwargs)
        with self.canvas:
            self.canvas_polygon = Canvas()
            self.canvas_line = Canvas()
        with self.canvas_polygon.before:
            PushMatrix()
            self.g_matrix = MatrixInstruction()
            self.g_scale = Scale()
            self.g_translate = Translate()
        with self.canvas_polygon:
            self.g_canvas_polygon = Canvas()
        with self.canvas_polygon.after:
            PopMatrix()

    def reposition(self):
        vx, vy = self.parent.delta_x, self.parent.delta_y
        pzoom = self.parent.zoom
        zoom = self.initial_zoom
        if zoom is None:
            self.initial_zoom = zoom = pzoom
        if zoom != pzoom:
            diff = 2 ** (pzoom - zoom)
            vx /= diff
            vy /= diff
            self.g_scale.x = self.g_scale.y = diff
        else:
            self.g_scale.x = self.g_scale.y = 1.
        self.g_translate.xy = vx, vy
        self.g_matrix.matrix = self.parent._scatter.transform

        if self.geojson:
            update = not self.first_time
            self.on_geojson(self, self.geojson, update=update)
            self.first_time = False

    def on_geojson(self, instance, geojson, update=False):
        if self.parent is None:
            return
        if not update:
            # print "Reload geojson (polygon)"
            self.g_canvas_polygon.clear()
            self._geojson_part(geojson, geotype="Polygon")
        # print "Reload geojson (LineString)"
        self.canvas_line.clear()
        self._geojson_part(geojson, geotype="LineString")

    def on_source(self, instance, value):
        if value.startswith("http://") or value.startswith("https://"):
            Downloader.instance().download(value, self._load_geojson_url)
        else:
            with open(value, "rb") as fd:
                geojson = json.load(fd)
            self.geojson = geojson

    def _load_geojson_url(self, url, r):
        self.geojson = r.json()

    def _geojson_part(self, part, geotype=None):
        tp = part["type"]
        if tp == "FeatureCollection":
            for feature in part["features"]:
                if geotype and feature["geometry"]["type"] != geotype:
                    continue
                self._geojson_part_f(feature)
        elif tp == "Feature":
            if geotype and part["geometry"]["type"] == geotype:
                self._geojson_part_f(part)
        else:
            # unhandled geojson part
            pass

    def _geojson_part_f(self, feature):
        properties = feature["properties"]
        geometry = feature["geometry"]
        graphics = self._geojson_part_geometry(geometry, properties)
        for g in graphics:
            tp = geometry["type"]
            if tp == "Polygon":
                self.g_canvas_polygon.add(g)
            else:
                self.canvas_line.add(g)

    def _geojson_part_geometry(self, geometry, properties):
        from kivy.graphics import Mesh, Line, Color
        from kivy.graphics.tesselator import Tesselator, WINDING_ODD, TYPE_POLYGONS
        from kivy.utils import get_color_from_hex
        from kivy.metrics import dp
        tp = geometry["type"]
        graphics = []
        if tp == "Polygon":
            tess = Tesselator()
            for c in geometry["coordinates"]:
                xy = list(self._lonlat_to_xy(c))
                xy = flatten(xy)
                tess.add_contour(xy)

            tess.tesselate(WINDING_ODD, TYPE_POLYGONS)

            color = self._get_color_from(properties.get("color", "FF000088"))
            graphics.append(Color(*color))
            for vertices, indices in tess.meshes:
                graphics.append(Mesh(vertices=vertices,
                                     indices=indices,
                                     mode="triangle_fan"))

        elif tp == "LineString":
            stroke = get_color_from_hex(properties.get("stroke", "#ffffff"))
            stroke_width = dp(properties.get("stroke-width"))
            xy = list(self._lonlat_to_xy(geometry["coordinates"]))
            xy = flatten(xy)
            graphics.append(Color(*stroke))
            graphics.append(Line(points=xy, width=stroke_width))

        return graphics

    def _lonlat_to_xy(self, lonlats):
        view = self.parent
        zoom = view.zoom
        for lon, lat in lonlats:
            p = view.get_window_xy_from(lat, lon, zoom)
            p = p[0] - self.parent.delta_x, p[1] - self.parent.delta_y
            p = self.parent._scatter.to_local(*p)
            yield p

    def _get_color_from(self, value):
        color = COLORS.get(value.lower(), value)
        color = get_color_from_hex(color)
        return color
