import xml.etree.ElementTree as ET
import sys
import utm

osm_file = sys.argv[1] # 'map.osm'
streets_csv_name = sys.argv[2] # 'geo.csv'
nodes_csv_name = sys.argv[3] # 'nodes.csv'
named_streets_csv_name = sys.argv[4] # 'named.csv'

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

streets_file = open(streets_csv_name, "w")
nodes_file = open(nodes_csv_name, "w")
named_file = open(named_streets_csv_name, "w")

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
                

# if a node is found more than once, then we have found an intersection
# generate a file containing intersection nodes
nodes_file.write('node_id,lat_deg,lon_deg,northing,easting,zone_number,zone_letter\n')
for ref_node in nodes_ref_list:
    if nodes_ref_list.count(ref_node) > 1:
        if not ref_node in intersections_list:
            intersections_list.append(ref_node)
            lat, lon = nodes[ref_node]
            easting, northing, zone, letter = utm.from_latlon(float(lat),float(lon))
            # node_id, lat_deg, lon_deg, northing, easting, zone_number, zone_letter
            nodes_file.write( str(ref_node) + ',' + lat + ',' + lon + ',' + str(northing) + ',' + str(easting) + ',' + str(zone) + ',' +  letter + '\n')
# end for

# generate a file containing geo streets (defined as the path from intersection to intersection)
streets_file.write('way_id,node_id_from,node_id_to,one_way_ind,no_lanes,lanes_backward,lanes_forward,routable\n')
for way_id in ways_dir:
    temp = []
    for node_id in ways_dir[way_id]:
        if node_id in intersections_list:
            temp.append(node_id)
    # end for

    # if the street begins in a dead end (also add the node to the file)
    if not ways_dir[way_id][0] in temp:
        temp.insert(0,ways_dir[way_id][0])
        lat, lon = nodes[ways_dir[way_id][0]]
        easting, northing, zone, letter = utm.from_latlon(float(lat),float(lon))
        nodes_file.write( str(ways_dir[way_id][0]) + ',' + lat + ',' + lon + ',' + str(northing) + ',' + str(easting) + ',' + str(zone) + ',' +  letter + '\n')
    # or ends in a dead end (also add the node to the file)
    if not ways_dir[way_id][-1] in temp:
        temp.append(ways_dir[way_id][-1])
        lat, lon = nodes[ways_dir[way_id][-1]]
        easting, northing, zone, letter = utm.from_latlon(float(lat),float(lon))
        nodes_file.write( str(ways_dir[way_id][-1]) + ',' + lat + ',' + lon + ',' + str(northing) + ',' + str(easting) + ',' + str(zone) + ',' +  letter + '\n')

    # if oneway is -1, then reverse node order
    if oneway_dir[way_id] == -1:
        temp = temp[::-1]

    lanes = lanes_dir.get(way_id, '-1')
    lanes_back = lanes_backward_dir.get(way_id, '-1')
    lanes_forw = lanes_forward_dir.get(way_id, '-1')

    # way_id, node_id_from, node_id_to, one_way_ind, no_lanes, lanes_backward, lanes_forward, routable
    if len(temp) > 1:
        for i in range(len(temp)-1):
            streets_file.write(str(way_id) + ',' + str(temp[i]) + ',' + str(temp[i+1]) + ',' + str(abs(oneway_dir[way_id])) + ',' + lanes + ',' + lanes_back + ',' + lanes_forw + ',1\n')
        # end for

# end for

# generate a file containing named streets (ways)
named_file.write('way_id,name,ref_name\n')
for way_id in ways_dir:
    name = names_dir.get(way_id, 'NA') 
    name_ref = names_ref_dir.get(way_id, 'NA')
    # way_id, name, ref_name
    named_file.write(str(way_id) + ',' + name + ',' + name_ref + '\n')
# end for

streets_file.close()
nodes_file.close()
named_file.close()
