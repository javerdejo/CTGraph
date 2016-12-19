import xml.etree.ElementTree as ET
import sys
import utm
import math

osm_file = sys.argv[1] # 'map.osm'
graph_xml_name = sys.argv[2] # 'graph.xml'
weights_xml_name = sys.argv[3] # 'weights.xml'

nodes_ref_list = []
ways_dir = {}
intersections_list = []
lanes_dir = {}
oneway_dir = {}
nodes = {}
street_names_dir = {}
lanes_backward_dir = {}
lanes_forward_dir = {}
names_dir = {}
names_ref_dir = {}

graph_file = open(graph_xml_name, "w")
weights_file = open(weights_xml_name, "w")


tree = ET.parse(osm_file)
osm = tree.getroot()

for node in osm.iter('node'):
    id_node = node.get('id')
    lat = node.get('lat')
    lon = node.get('lon')
    nodes[id_node] = [lat, lon]
# end for

for way in osm.iter('way'):
    id_way = way.get('id')
    for tag in way.iter('tag'):
        if tag.get('k') == 'highway':
            if tag.get('v') in ['motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'unclassified', 'residential', 'service','motorway_link', 'trunk_link', 'primary_link', 'secondary_link', 'living_street']:   
                oneway_dir[id_way] = 0     
                for nd in way.iter('nd'):
                    ref = nd.get('ref')
                    nodes_ref_list.append(ref)
                    if id_way in ways_dir:
                        ways_dir[id_way].append(ref)
                    else:
                        ways_dir[id_way] = []
                        ways_dir[id_way].append(ref)
                # end for
        elif tag.get('k') == 'lanes':
            lanes_dir[id_way] = tag.get('v')
        elif tag.get('k') == 'oneway':
            if tag.get('v') == 'yes':
                oneway_dir[id_way] = 1
            else:
                oneway_dir[id_way] = -1
        elif tag.get('k') == 'lanes:backward':
            lanes_backward_dir[id_way] = tag.get('v')
        elif tag.get('k') == 'lanes:forward':
            lanes_forward_dir[id_way] = tag.get('v')
        elif tag.get('k') == 'name':
            names_dir[id_way] = tag.get('v').encode('utf-8')
        elif tag.get('k') == 'ref':
            names_ref_dir[id_way] = tag.get('v').encode('utf-8')

    # end for
# end for    
                
# file headers
weights_file.write('<weights>\n')
graph_file.write('<graph>\n')

# if a node is found more than once, then we have found an intersection
for ref_node in nodes_ref_list:
    if nodes_ref_list.count(ref_node) > 1:
        if not ref_node in intersections_list:
            intersections_list.append(ref_node)            
# end for

arcid = 1
graph_file.write('\t<arcs>\n')
# generate arcs
for way_id in ways_dir:
    temp = []
    for node_id in ways_dir[way_id]:
        if node_id in intersections_list:
            temp.append(node_id)
    # end for

    # if the street begins in a dead end (also add the node to the file)
    if not ways_dir[way_id][0] in temp:
        temp.insert(0,ways_dir[way_id][0])        
    # or ends in a dead end (also add the node to the file)
    if not ways_dir[way_id][-1] in temp:
        temp.append(ways_dir[way_id][-1])        

    # if oneway is -1, then reverse node order
    if oneway_dir[way_id] == -1:
        temp = temp[::-1]

    lanes = lanes_dir.get(way_id, '-1')
    lanes_back = lanes_backward_dir.get(way_id, lanes)
    lanes_forw = lanes_forward_dir.get(way_id, lanes)

    # way_id, node_id_from, node_id_to, one_way_ind, no_lanes, lanes_backward, lanes_forward, routable
    if len(temp) > 1:
        for i in range(len(temp)-1):
            graph_file.write('\t\t<arc arcid=\'' + str(arcid) + '\' from=\'' + str(temp[i]) + '\' to=\'' + str(temp[i+1]) + '\' logid=\'' + str(way_id) + '\' lanes=\'' + lanes_forw + '\'' + ' />\n')
            lat1, lon1 = nodes[temp[i]]
            easting1, northing1, zone1, letter1 = utm.from_latlon(float(lat1),float(lon1))
            lat2, lon2 = nodes[temp[i+1]]
            easting2, northing2, zone2, letter2 = utm.from_latlon(float(lat2),float(lon2))
            w = math.sqrt( math.pow(easting1-easting2,2) + math.pow(northing1-northing2,2) )
            weights_file.write('\t<weight arcid=\'' + str(arcid) + '\' value=\'' + str(w) + '\' type=\'distance\' />\n')
            if abs(oneway_dir[way_id]) == 0 :
                arcid = arcid + 1
                graph_file.write('\t\t<arc arcid=\'' + str(arcid) + '\' from=\'' + str(temp[i+1]) + '\' to=\'' + str(temp[i]) + '\' logid=\'' + str(way_id) + '\' lanes=\'' + lanes_back + '\'' + ' />\n')
                weights_file.write('\t<weight arcid=\'' + str(arcid) + '\' value=\'' + str(w) + '\' type=\'distance\' />\n')
            arcid = arcid + 1 
        # end for

# end for
graph_file.write('\t</arcs>\n')

# include nodes in graph file
graph_file.write('\t<nodes>\n')
for ref_node in intersections_list:
    lat, lon = nodes[ref_node]
    easting, northing, zone, letter = utm.from_latlon(float(lat),float(lon))
    graph_file.write('\t\t<node id=\'' + str(ref_node) + '\' lat=\'' + lat + '\' lon=\'' + lon + '\' northing=\'' + str(northing) + '\' easting=\'' + str(easting) + '\' zone=\'' + str(zone) + '\' letter=\'' +  letter + '\' />\n')
# end for
graph_file.write('\t</nodes>\n')


# close xml tags
weights_file.write('</weights>\n')
graph_file.write('</graph>\n')


graph_file.close()
weights_file.close()

