from flask import Flask
from flask import Flask, render_template, request

import folium
from folium import Marker, Circle
import branca

import json
from rdflib import RDF, RDFS, Graph, Literal, Namespace, URIRef, BNode, OWL
from rdflib.namespace import XSD

import os

def create_graph():
    identity = Namespace('http://www.example.org/theophane_delbauffe/untitled-ontology#/')
    onto = Namespace('http://www.example.org/theophane_delbauffe/untitled-ontology#')

    # load data in a dictionary from json file
    with open('stations.json') as json_data:
        data_dict = json.load(json_data)

    # create the graph
    o = Graph(identifier=identity)
    g = o.parse(location='project_ontology.owl')
    g.bind('ex', onto)
    
    # load data in triplestore
    for i in range(len(data_dict)):
        s = 'http://www.example.org/theophane_delbauffe/untitled-ontology#'
        s += str(data_dict[i]['code_uic'])
        id = URIRef(s)
        g.add((URIRef(id), URIRef(RDF.type), URIRef(onto.Station)))
        g.add((id, identity.NamePOI, Literal(data_dict[i]['libelle'], datatype=XSD.string)))
        g.add((id, identity.Commune, Literal(data_dict[i]['commune'], datatype=XSD.string)))
        g.add((id, identity.Department, Literal(data_dict[i]['departemen'], datatype=XSD.string)))
        g.add((id, identity.stationType, Literal(data_dict[i]['station_type'], datatype=XSD.string)))
        g.add((id, identity.Latitude, Literal(data_dict[i]['y_wgs84'], datatype=XSD.float)))
        g.add((id, identity.Longitude, Literal(data_dict[i]['x_wgs84'], datatype=XSD.float)))

    # save turtle file
    file = open("stations.ttl", "wb")
    file.write(bytes(g.serialize(format="turtle"), "UTF-8"))
    file.close()
    return g

app = Flask(__name__)
g = create_graph()

def popup_html(row):
    Latitude = row["Latitude"]
    Longitude = row["Longitude"]
    Station_type = row["stationType"]
    Department = row["Department"]
    NamePOI = row["NamePOI"]               
    Commune = row["Commune"]

    left_col_color = "#4654e1"
    right_col_color = "#c7cbfad8"
    
    html = """<!DOCTYPE html>
              <html>
              <head>
                  <meta charset="utf8">
                  <h4 style="margin-bottom:10"; width="200px";><span style = "color:"""+left_col_color+"""; font-weight: bold; font-size: 32px">{}</h4>""".format(NamePOI) + """
              </head>
                  <table style="height: 126px; width: 400px;">
              <tbody>
              <tr>
              <td style="background-color: """+ left_col_color +""";"><span style="color:"""+right_col_color+""";">Latitude</span></td>
              <td style="width: 250px;background-color: """+ right_col_color +""";"><span style="color: """+left_col_color+"""; font-weight: bold">{}</td>""".format(Latitude) +"""
              </tr>
              <tr>
              <td style="background-color: """+ left_col_color +""";"><span style="color: """+right_col_color+""";">Longitude</span></td>
              <td style="width: 250px;background-color: """+ right_col_color +""";"><span style="color: """+left_col_color+"""; font-weight: bold">{}</td>""".format(Longitude) + """
              </tr>
              <tr>
              <td style="background-color: """+ left_col_color +""";"><span style="color: """+right_col_color+""";">Station type</span></td>
              <td style="width: 250px;background-color: """+ right_col_color +""";"><span style="color: """+left_col_color+"""; font-weight: bold">{}</td>""".format(Station_type) + """
              </tr>
              <tr>
              <td style="background-color: """+ left_col_color +""";"><span style="color: """+right_col_color+""";">Commune</span></td>
              <td style="width: 250px;background-color: """+ right_col_color +""";"><span style="color: """+left_col_color+"""; font-weight: bold">{}</td>""".format(Commune) + """
              </tr>
              <tr>
              <td style="background-color: """+ left_col_color +""";"><span style="color: """+right_col_color+""";">Department</span></td>
              <td style="width: 250px;background-color: """+ right_col_color +""";"><span style="color: """+left_col_color+"""; font-weight: bold">{}</td>""".format(Department) + """
              </tr>
              </tbody>
              </table>
              </html>

              """
    return html

def retrieve_data():
    query1 = g.query(
                    """SELECT ?latitude ?longitude ?stationType ?department ?namePOI ?commune
                WHERE {
                    ?station rdf:type ex:Station .
                    ?station ns1:Latitude ?latitude .
                    ?station ns1:Longitude ?longitude .
                    ?station ns1:stationType ?stationType .
                    ?station ns1:Department ?department .
                    ?station ns1:NamePOI ?namePOI .
                    ?station ns1:Commune ?commune .
                }LIMIT 100""")
    final_list = []
    for row in query1:
        d = {"Latitude":row[0].value, "Longitude":row[1].value, "stationType":row[2].value, "Department":row[3].value, "NamePOI":row[4].value, "Commune":row[5].value}
        final_list.append(d)
    return final_list

def check_map_exists():
    try:
        f = open('templates/maps/map.html', 'r')
        f.close()
        return True
    except FileNotFoundError:
        return False

def make_map():
    coords_paris = [48.856614, 2.3522219]
    if check_map_exists():
        os.remove('templates/maps/map.html')
    m = folium.Map(location=[coords_paris[0], coords_paris[1]],
               zoom_start=12,
               tiles="cartodbpositron",
               width='75%',
               height='75%')
    data = retrieve_data()

    for row in data:
        html = popup_html(row)
        iframe = branca.element.IFrame(html=html,width=510,height=280)
        popup = folium.Popup(folium.Html(html, script=True), max_width=500)
        try:
            Marker([row["Latitude"], row["Longitude"]], popup=popup, icon=folium.Icon(color="blue", icon='train', prefix='fa')).add_to(m)
        except:
            pass

    m.save('templates/maps/map.html')

@app.route('/')
def display_map():
    make_map()
    return render_template('index.html')


@app.route('/search', methods=['POST'])
def search():
    start_coords = (46.9540700, 142.7360300)
    folium_map = folium.Map(location=start_coords, zoom_start=14)
    return folium_map._repr_html_()

@app.route('/type', methods=['POST'])
def type():
    start_coords = (46.9540700, 142.7360300)
    folium_map = folium.Map(location=start_coords, zoom_start=14)
    return folium_map._repr_html_()

if __name__ == '__main__':
    app.run()
