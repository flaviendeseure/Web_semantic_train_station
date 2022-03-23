# librairies requiered for flask
from flask import Flask
from flask import Flask, render_template, request, redirect

#librairies requiered for display the map on the website
import folium
from folium import Marker
import branca

#librairies requiered for creating graph and turttle file
import json
from rdflib import RDF, Graph, Literal, Namespace, URIRef
from rdflib.namespace import XSD

import os

# function to create the graph
def create_graph(): 
    # Pick up the ontology file
    identity = Namespace('http://www.example.org/theophane_delbauffe/untitled-ontology#/')
    onto = Namespace('http://www.example.org/theophane_delbauffe/untitled-ontology#') 

    # load data in a dictionary from json file
    with open('ontology files/stations.json') as json_data:
        data_dict = json.load(json_data)

    # create the graph
    o = Graph(identifier=identity)
    g = o.parse(location='ontology files/project_ontology.owl')
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
    file = open("ontology files/stations.ttl", "wb")
    file.write(bytes(g.serialize(format="turtle"), "UTF-8"))
    file.close()
    return g

#create the application flask and add the route
app = Flask(__name__)
#creation of a graph
g = create_graph()

#function to create the popup_html for the popup to display the information of the station on the map
def popup_html(row):
    #variables from the dataset 
    Latitude = row["Latitude"]
    Longitude = row["Longitude"]
    Station_type = row["stationType"]
    Department = row["Department"]
    NamePOI = row["NamePOI"]               
    Commune = row["Commune"]

    #color of the table inside the popup
    left_col_color = "#4654e1"
    right_col_color = "#c7cbfad8"
    
    #create the html for the popup
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

#function to retrieve data from the graph with queries
def retrieve_data(limit=100):
    #query to retrieve all the information of the stations inside the graph
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
                }LIMIT """+ f"{limit}")#here we put the limit to 100 because we want to display only 100 stations on the map for performance reasons

    final_list = []
    #for each row of the query we create a dictionary with the information of the station
    for row in query1:
        d = {"Latitude":row[0].value, "Longitude":row[1].value, "stationType":row[2].value, "Department":row[3].value, "NamePOI":row[4].value, "Commune":row[5].value}
        final_list.append(d)
    
    return final_list #return the list of dictionaries

#function to check if a map exist on the server
def check_map_exists():
    try: #try to open the potential existing file
        f = open('templates/maps/map.html', 'r')
        f.close()
        return True
    except FileNotFoundError:
        return False

#create a map with the stations on it
def make_map(limit=100):
    #coordinates of Paris to arrive directly on Paris
    coords_paris = [48.856614, 2.3522219] 

    #ckecking if the map already exists if so, we delete it
    if check_map_exists():
        os.remove('templates/maps/map.html')

    #create a folium map with the coordinates of Paris 
    # and the zoom level of the map
    # title correspond to the type of map     
    m = folium.Map(location=[coords_paris[0], coords_paris[1]],
               zoom_start=12,
               width='75%',
               height='75%')
    data = retrieve_data(limit)

    #for each station in the list of dictionaries we create a marker on the map with the coordinates of the station
    for row in data:
        html = popup_html(row)
        iframe = branca.element.IFrame(html=html,width=510,height=280)
        popup = folium.Popup(folium.Html(html, script=True), max_width=500)
        try:
            Marker([row["Latitude"], row["Longitude"]], popup=popup, icon=folium.Icon(color="blue", icon='train', prefix='fa')).add_to(m)
        except:
            pass
    m.save('templates/maps/map.html')
    return m

def retrieve_data_search(name):
    #query to retrieve all the information of the stations inside the graph
    query1 = g.query(
                    """SELECT ?latitude ?longitude
                WHERE {
                    ?station rdf:type ex:Station .
                    ?station ns1:Latitude ?latitude .
                    ?station ns1:Longitude ?longitude .
                    ?station ns1:NamePOI """ + '"' + name + '"' + """ .
                }""")#here we put the limit to 100 because we want to display only 100 stations on the map for performance reasons

    final_list = []
    #for each row of the query we create a dictionary with the information of the station
    for row in query1:
        d = {"Latitude":row[0].value, "Longitude":row[1].value}
        final_list.append(d)
    
    return final_list #return the list of dictionaries

def search_map(name):   
    try:
        #ckecking if the map already exists if so, we delete it
        if check_map_exists():
            os.remove('templates/maps/map.html')
        coords = retrieve_data_search(name)[0]
        m = folium.Map(location=[coords[0], coords[1]],
                zoom_start=14,
                width='75%',
                height='75%')

        data = retrieve_data(name)

        #for each station in the list of dictionaries we create a marker on the map with the coordinates of the station
        for row in data:
            html = popup_html(row)
            iframe = branca.element.IFrame(html=html,width=510,height=280)
            popup = folium.Popup(folium.Html(html, script=True), max_width=500)
            try:
                Marker([row["Latitude"], row["Longitude"]], popup=popup, icon=folium.Icon(color="blue", icon='train', prefix='fa')).add_to(m)
            except:
                pass
        m.save('templates/maps/map.html')
        return m

    except:
        print("No station found")
        return False

@app.route('/')
def display_map():
    make_map()
    return render_template('index.html')

@app.route('/limit', methods=['POST'])
def limit():
    limit = request.form['dropdown']
    folium_map = make_map(int(limit))
    return folium_map._repr_html_()

@app.route('/search', methods=['POST'])
def search():
    name = request.form['q']
    folium_map = search_map(name)
    if not folium_map:
        return render_template('index.html')
    return folium_map._repr_html_()

@app.route('/type', methods=['POST'])
def type():
    start_coords = (46.9540700, 142.7360300)
    folium_map = folium.Map(location=start_coords, zoom_start=14)
    return folium_map._repr_html_()

if __name__ == '__main__':
    app.run()
