
# coding: utf-8

# # Montpellier Open Street Map Data
# I've downloaded the .osm data for the map of the Montpellier area in France. I cleaned the data to fix invalid street, city, and postal code names and reformatted the data to store it in a tabular format **(Section 1)**. After downloading the data into .csv files, I uploaded them into a SQL database to investigate some different attributes of the data **(Section 2)**.
# 
# Querying the node tags allowed me to understand general features of the city, such as popular cuisine and tree species. **(Section 3)**.

# ## Section 1: Cleaning Montpellier Address Data
# 
# The .osm file for Montpellier is 199,267 KB so I chose to use cElementTree with the iterparse method to work with the .osm data. I created a smaller sample file to use when validating code functionality (SAMPLE_FILE).

# In[175]:

import xml.etree.cElementTree as ET  
from collections import defaultdict

OSM_FILE = r"C:\Users\schro\Desktop\Projects\Data Analysis Nanodegree\P3- Data Wrangling\Montpellier.osm"  
SAMPLE_FILE = "sample2.osm"

k = 100 # Parameter: take every k-th top level element

def get_element(osm_file, tags=('node', 'way', 'relation')):

    context = iter(ET.iterparse(osm_file, events=('start', 'end')))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


with open(SAMPLE_FILE, 'wb') as output:
    output.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    output.write('<osm>\n  ')

    # Write every kth top level element
    for i, element in enumerate(get_element(OSM_FILE)):
        if i % k == 0:
            output.write(ET.tostring(element, encoding='utf-8'))

    output.write('</osm>')


# Below, I've created a dictionary containing all tags in the XML dataset, and the number of each type. These tags refer to elements within the Open Street Map (OSM) data, as well as tags for each element. 
# 
# OSM XML is made up of three different elements: '
# 
# 1. Nodes - defined location made up of an ID and pair of coordinates
# 2. Ways - paths between nodes, ways to get places, linear features, boundaries
# 3. Relations - explains how elements work together, often an ordered list of nodes/ways

# In[152]:


osm_file = open(data, "r")
street_types = defaultdict(set)
i=0
for event, elem in ET.iterparse(osm_file, events=("start",)):
    if i<100000 and i>80100:
        if elem.tag=="node":
            #print elem.tag, elem.attrib
            for tag in elem.iter("tag"):
                if tag != None:
                    print "------",tag.tag, tag.attrib
        
    i+=1
osm_file.close()


# The function 'count_tags' counts the number of different elements and tags (used to describe features of elements) in the file. Output shown below.

# In[177]:


import xml.etree.cElementTree as ET
data=SAMPLE_FILE 
def count_tags(filename):
    tag_dic={}
    for event, elem in ET.iterparse(filename):
        tagi=elem.tag
        if tagi in tag_dic:
            tag_dic[tagi]=tag_dic[tagi]+1
        else:
            tag_dic[tagi]=1
    return tag_dic
            
count_tags(data)


# Each tag has a key describing the tag attribute, which is held as the 'value'. The function key_type is used to understand how many of the keys have problem characters, or colons (which may be used to nest information).

# In[178]:

import re

lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
lower_double_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')


def key_type(element, keys):
    if element.tag == "tag":
        keyy=element.attrib['k']
        if lower.search(keyy)==None:
            if lower_double_colon.search(keyy)==None:
                if lower_colon.search(keyy)==None:
                    if problemchars.search(keyy)==None:
                        keys["other"]+=1
                    else:
                        keys["problemchars"]+=1

                else: 
                    keys["lower_colon"]+=1
                    
            else:
                keys["lower_double_colon"]+=1
        else:
            keys["lower"]+=1        
    return keys

def process_map(data):
    keys = {"lower": 0, "lower_colon": 0, "lower_double_colon":0, "problemchars": 0, "other": 0}
    for _, element in ET.iterparse(data):
        keys = key_type(element, keys)

    return keys
process_map(data)


# #### The first cleaning task involved making the street names consistant.
# 
# The list of expected street names shows the words that I expected to find that describe different streets in Montpellier. By looking through a map of the city, I came up with some expected words such as 'rue' (translates to 'road'), 'avenue', 'boulevard', 'route', 'chemin' (translates to 'path'). In the French language, these words tend to come at the beginning of the road title (e.g. Rue Ferdinand Fabre).
# 
# The functions below take all of the street name fields and inspect them to understand if the street names are one of the expected words. If not, common abbreviations are corrected. For phrases that include the building name or number before the street name, every part of the address before the street name is removed. The functions can be used to edit the street names before adding them into the SQL database.

# One thing that became clear when looking through the sources of this data, was that the french accents were incoded as a special value. The UCF-8 characters are recorded as ASCII strings. I decided to leave the encoded text, but have accounted for it throughout the cleaning procedure. For example, the word u"All\xe9e", the UCF-8 encoding for allée, was added to the list of expected roads (translating to alley in French).

# In[281]:

import re

#create dictionary of things to change faulty street names to
mapping = { "av.": "Avenue",
            "ave": "Avenue",
            "Ave.":"Avenue",
            "R.":"Rue",
            "r.":"Rue",
            "blvd":"Boulevard",
            "blvd.":"Boulevard"
            }
#checks if element is in 'street' format for attribute
def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")

def update_name(name, mapping):
    updated_name_list=[]
    name_list=name.split()
    updated_names=name
    
    #first check if road name begins in middle of phrase
    for road in expected:
        if road in name_list:
            i=0
            for name in name_list:
                if name==road:
                    updated_name_list=name_list[i:]
                    updated_names=' '.join(updated_name_list)
                    break
                else:
                    i+=1
            
    #if not, check if first word can be mapped to a different word

    if name_list[0] in mapping.keys():
            name_list[0] = mapping[name_list[0]]
            updated_names=' '.join(name_list)
    return updated_names
    
#builds set of nonconforming street names
def audit_street_type(street_types_list, street_name):
    expected = {"Rue", "Avenue", "Boulevard", "Route", "Chemin", "Place", "Impasse",u"All\xe9e", 'Voie','Esplanade'}

#add upper and lowercase versions of the words to the list
    for x in expected.copy():
        expected.add(x.lower())
        expected.add(x.upper())
    
    street_type=street_name.split()[0]
    if street_type not in expected: 
            street_types_list[street_type].add(street_name) #adds street to list for reference
            #calls function to fix street name if possible
            updated_street_name=update_name(street_name,mapping)
    else:
        updated_street_name=street_name
    return updated_street_name
        
#parses through file to audit street names
#this function is not used in the main function, but only when a file must be opened and parsed from scratch
def updated_street_name(osmfile):
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    tag.attrib['v']=audit_street_type(street_types, tag.attrib['v'])
    osm_file.close()
    return street_types

updated_street_name(SAMPLE_FILE)


# #### Using the same method as above, I investigated the city, country, and postal code of each of these tags.
# 
# All country codes were properly labelled "FR" for France.
# 
# For the postal codes, I expected to see the four codes attributed to the city of Montpellier: "34000","34070","34080","34090"
# 
# Besides these codes, I list of postal codes for surrounding communes was returned ['34130', '34170', '34006', '34920', '34790', '34970', '34880', '34990', '34830']. This makes sense because in pulling the OSM data for Montpellier, I selected a rectangular region. This would have included communes outside of the city of Montpellier.
# 
# #### For this reason, I decided to assess the validity of the data by filtering the postal codes only by the département of Hérault and postal code length (5 characters). 
# In French postal codes, the first two numbers refer to the département (34 in this case). All postal codes in this dataset began with the digits '34', but some were longer than 5 characters (e.g. '34064 Montpellier Cedex 2'). For all postal codes greater than 5 characters, I used a function to return only the first 5 characters of the postal code.
# 

# In[312]:

import re
def investigate_zip(zip_value,code_list):
    new_code=zip_value
    if len(zip_value)>5: #check for postcodes with text appended 
        code_list.add(tag.attrib['v']) #add to list for reference
        new_code=new_code[:5]
    if zip_value[:2] !='34': #check for non-Herault codes
        new_code='error' #entry to be discluded later
        code_list.add(tag.attrib['v'])
    return new_code
    
#parses through file to audit zip codes in osm file
def audit_zip(osmfile):
    code_a_list=set() #to reference bad zips
    osm_file = open(osmfile, "r")
    new_code=""
    for event, elem in ET.iterparse(osm_file, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if tag.attrib['k'] == "addr:postcode":
                    #fix errors in postcode
                    new_code=tag.attrib['v']
                    investigate_zip(new_code,code_a_list)
                        
    osm_file.close()
audit_zip(SAMPLE_FILE)
    


# In order to fix city data, I looked at the different cities in the dataset, and added valid communes to the list of valid cities. For common typos, or areas within a hamlet, I setup a dictionary that could be used to fix the names or assign the appropriate hamlet.

# In[306]:

import re

def update_name_city(name,other_cities):
    
    updated_names=name #keep invalid names in dataset
    expected_codes = {"Montpellier",'MONTPELLIER',u'Lav\xe9rune',u'Le Cr\xe8s', 'montpellier', 'Grabels', 'Mauguio', 
                  'Lattes','LATTES', 'Jacou', 'Castelnau-le-Lez','juvignac', 'Juvignac',
                  u'Saint-Cl\xe9ment-de-Rivi\xe8re','Montferrier-sur-Lez',u'P\xe9rols','Clapiers',u'Saint-Jean-de-V\xe9das'}


#create dictionary of things to change faulty street names to
    mapping_city = { "Castelnau le Lez": "Castelnau-le-Lez",
                "Montpelier": "Montpellier",
                "Saint-Jean-de-Vedas":u'Saint-Jean-de-V\xe9das',
                "Montpelle":"Montpellier",
                'Castelnau le lez':"Castelnau-le-Lez",
                'Castelnau le Les':"Castelnau-le-Lez",
                 u'Saint Cl\xe9ment de riviere':u'Saint-Cl\xe9ment-de-Rivi\xe8re',
                'Maurin':'Lattes'
                }
    if name not in expected_codes:
        other_cities.add(name)
        print other_cities
        if name in mapping_city.keys():
            updated_names = mapping_city[name]
    return updated_names


# ## Section 2. Parsing data into SQL Database
# 
# In order to put this data into an SQL database, I will parse each element in the XML file, putting them into a tabular format that can be written to a .csv file. I'm using a schema and validation library to check the data before writing the data structures to new .csv files.
# 
# 

# In[319]:

#!/usr/bin/env python



import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET

import cerberus

import schema

OSM_PATH = data
code_list = set() #to reference invalid postcodes
other_cities=set() #to reference invalid cities

#locations to save output files
NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SCHEMA = schema.schema

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']


def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements

    def attach_attrib(fields):
        dictionary={}
        for x in fields:
            dictionary[x]=element.attrib[x]
        return dictionary
        
    def subnodes(mainn):
        final_list=[]
        for minitag in element.iter("tag"):
            dic={}
            #skip values with missing values
            if minitag.attrib['v'] == '' or minitag.attrib['v'] == None or minitag.attrib['k'] == '' or minitag.attrib['k'] == None:
                print 'found a missing value'
                continue
            
            if PROBLEMCHARS.search(minitag.attrib["k"])==None:
                
                #first,fix streetname
                if minitag.attrib['k'] == "addr:street":
                    #change road name to fixed name 
                    minitag.attrib['v']=audit_street_type(street_types, minitag.attrib['v'])
                    
                if minitag.attrib['k'] == "addr:postcode":
                    #fix postcodes
                    minitag.attrib['v']=investigate_zip(minitag.attrib['v'],code_list)
                    #for invalid postcodes, or from areas outside of the Herault region, do not include entry
                    if minitag.attrib['v']=='error':
                        continue
                if minitag.attrib['k'] == "addr:city":
                    #fix cities
                    minitag.attrib['v']=update_name_city(minitag.attrib['v'],other_cities)
                
                    
                dic["id"]=element.attrib["id"]
                if ":" in minitag.attrib["k"]:
                    splitkey=minitag.attrib["k"]
                    splitkey=splitkey.split(":",1)
                    dic["key"]=splitkey[1]
                    dic["type"]=splitkey[0]
                else:
                    dic["key"]=minitag.attrib["k"]
                    dic["type"]="regular"
                dic['value']=minitag.attrib['v']
            
            
                final_list.append(dic)
            #print dic
        return final_list
    
    #add large id as first tag
    if element.tag == 'node':
        node_attribs=attach_attrib(NODE_FIELDS)
        tags=subnodes(element)
        return {'node': node_attribs, 'node_tags': tags}
    elif element.tag == 'way':
        way_attribs=attach_attrib(WAY_FIELDS)
        tags=subnodes(element)
        
        way_nodes=[]
        i=0
        for minitag in element.iter("nd"):
            #skip values with missing values
            if minitag.attrib['ref'] == '' or minitag.attrib['ref'] == None:
                continue
            dic={}
            dic["id"]=element.attrib["id"]
            dic["node_id"]=minitag.attrib["ref"]
            dic['position']=i
            way_nodes.append(dic)
            i+=1
        
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}


# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)
        
        raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file,          codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file,          codecs.open(WAYS_PATH, 'w') as ways_file,          codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file,          codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])


    print code_list
process_map(OSM_FILE, validate=True)


# Once the .csv files were written, I imported them into a sql database using sqlite3. I chose to use python to specify the data types and include the program in the same workflow. The processed used to create the database files and tables is shown below. It was repeated for each of the five tables.
# 
# Final database files:
# 
# nodes.db : 64,273 KB
# nodes_tags.db : 4,340 KB
# ways.db : 16,087 KB
# ways_tags.db : 45,493 KB
# ways_nodes.db : 22,903 KB
# 
# montpellier.db: 122,303 KB
# 
# During this process, I also counted the number of unique nodes and ways in the dataset. There's a total of 854,439 nodes (see count query below) and 140,286 ways. It makes sense that there are more nodes, as each way is made up of a collection of nodes.
# 

# In[20]:

import sqlite3
import csv
from pprint import pprint

sqlite_file_m= "montpellier.db"
    # name of the sqlite database file

def upload_to_sql(file_path,sqlite_file):
    # Connect to the database
    conn = sqlite3.connect(sqlite_file)
    conn.text_factory = str

    # Get a cursor object
    cur = conn.cursor()

    #cur.execute('DROP TABLE IF EXISTS ways') #drop tables if it already exists when making a new one
    conn.commit() #commit the changes

    # Read in the csv file as a dictionary, format the
    # data as a list of tuples:
    with open(file_path,'rb') as fin:
        dr = csv.DictReader(fin) # comma is default delimiter
        to_db = [(i['id'], i['node_id'],i['position']) for i in dr]

    # insert the formatted data
    cur.execute('''CREATE TABLE way_nodes(id INTEGER, node_id INTEGER, position INTEGER)''')
    cur.executemany("INSERT INTO way_nodes(id, node_id, position) VALUES (?, ?, ?);", to_db)
    # commit the changes
    conn.commit()

    #check data was inserted correctly with right format
    cur.execute('SELECT COUNT(*) FROM way_nodes')
    all_rows = cur.fetchall()
    print all_rows

    conn.close() #close connection
    print 'done'
    return


upload_to_sql(WAY_NODES_PATH,sqlite_file_m)


# ## Section 3. User Contribution Analysis
# 
# Below is the code used to count how many users contributed to the Montpellier OSM data. There was a total of 714 entries that had distinct user IDs.
#
# In[96]:


import pandas as pd
sqlite_file = r"C:\Users\schro\Desktop\Projects\Data Analysis Nanodegree\P3- Data Wrangling\CSV_Exports\montpellier.db"    # name of the sqlite database file


# Connecting to the database file
conn = sqlite3.connect(sqlite_file)
c = conn.cursor()

#select uid from nodes and ways, union matches pairs without including duplicates
c.execute('SELECT COUNT(*) FROM (SELECT uid FROM nodes UNION SELECT uid FROM ways);')
all_rows = c.fetchall()
pprint(all_rows)

#select user entry data
c.execute('SELECT user,COUNT(*) as num FROM (SELECT user FROM nodes UNION ALL SELECT user FROM ways) e GROUP BY e.user ORDER BY num DESC;')
all_rows = c.fetchall()

#look at user entry statistics
user_counts=pd.DataFrame(all_rows)
print user_counts[1].describe()
# Closing the connection to the database file
conn.close()


# ## Landmarks in Montpellier
# 
# I began by running a SQL query to understand the different tags used to describe different nodes, pulling the 300 most popular entries to browse. I looked at the most popular values for tags that interested me. 
# 
# 
# In[184]:


import pandas as pd
sqlite_file = "montpellier.db"    # name of the sqlite database file


# Connecting to the database file
conn = sqlite3.connect(sqlite_file)
c = conn.cursor()

#investigate tag types
c.execute('SELECT key, COUNT(*) FROM node_tags GROUP BY key ORDER BY COUNT(*) DESC LIMIT 10;')
all_rows = c.fetchall()
pprint(all_rows)
print("\n")

c.execute('SELECT value, COUNT(*) as num FROM node_tags WHERE key="cuisine" GROUP BY value ORDER BY num DESC LIMIT 10;')
all_rows = c.fetchall()
pprint(all_rows)
print("\n")

c.execute('SELECT value, COUNT(*) as num FROM node_tags WHERE key="shop" GROUP BY value ORDER BY num DESC LIMIT 10;')
all_rows = c.fetchall()
pprint(all_rows)
print("\n")


c.execute('SELECT value, COUNT(*) as num FROM node_tags WHERE key="species" GROUP BY value ORDER BY num DESC LIMIT 5;')
all_rows = c.fetchall()
pprint(all_rows)
print("\n")

# Closing the connection to the database file
conn.close()



