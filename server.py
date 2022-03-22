from flask import Flask
from flask import Flask, render_template, request
import folium
import os

app = Flask(__name__)

def check_map_exists():
    try:
        f = open('templates/maps/map.html', 'r')
        f.close()
        return True
    except FileNotFoundError:
        return False

def make_chicago_map():
    if check_map_exists():
        os.remove('templates/maps/map.html')
    folium_map = folium.Map(location=[41.88, -87.62],
                            zoom_start=13,
                            tiles="cartodbpositron",
                            width='75%',
                            height='75%')
    folium_map.save('templates/maps/map.html')

@app.route('/')
def hello_world():
    make_chicago_map()
    return render_template('index.html')

"""
@app.route('/')
def index():
    start_coords = (46.9540700, 142.7360300)
    folium_map = folium.Map(location=start_coords, zoom_start=14)
    return folium_map._repr_html_()
"""

if __name__ == '__main__':
    app.run()

