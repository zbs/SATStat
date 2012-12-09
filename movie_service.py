#!/usr/bin/env python
# encoding: utf-8
"""
School_service.py: a RESTful School data service

"""
import os
import codecs
import json
import re
import urlparse

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

from tornado.options import define, options
from tornado.web import RequestHandler

define("port", default=8888, help="run on the given port", type=int)
define("Schools", default="data/movies.csv", help="Schools data file")
define("actors", default="data/actors.csv", help="actors data file")
define("mappings", default="data/movie_actors.csv", help="key mapping file")

### School Web Service implementation ###

type_to_extension = {"application/xml" : "xml", "application/rdf+xml": "rdf", 
                     "text/turtle": "ttl", "text/html" : "html", "application/json" : "json"}

def respond_to_header(handler, redirect_uri, support_html=False):
    accept_format = handler.request.headers["Accept"]
    if not accept_format or accept_format == '*/*':
        accept_format = 'application/json'
    if accept_format not in type_to_extension:
        handler.write_error(401, message="Content type %s not supported"%accept_format)
    elif accept_format == 'text/html' and not support_html:
        handler.write_error(401, message="HTML not supported for this use case")
    else:
        extension = type_to_extension[accept_format]
        handler.redirect(redirect_uri+".%s"%extension, status=303)

class SchoolService(tornado.web.Application):
    """The School Service Web Application"""
    def __init__(self):
        handlers = [
            (r"/", HomeHandler),
            (r"/Schools(\..+)?", SchoolListHandler),
            (r"/Schools/(\d+)(\..+)?", SchoolResourceHandler),
            (r"/maps?", MapHandler),
            (r"/search(\..+)?", QueryHandler)
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            debug=True,
            autoescape=None,
        )
        tornado.web.Application.__init__(self, handlers, **settings)
#        self.db = db
        
class BaseHandler(tornado.web.RequestHandler):
    """Functions common to all handlers"""
    @property
    def db(self):
        return self.application.db
        
    @property
    def base_uri(self):
        """Returns the Web service's base URI (e.g., http://localhost:8888)"""
        protocol = self.request.protocol
        host = self.request.headers.get('Host')
        return protocol + "://" + host
        
    def write_error(self, status_code, **kwargs):
        """Attach human-readable msg to error messages"""
        self.finish("Error %d - %s" % (status_code, kwargs['message']))
    

class HomeHandler(BaseHandler):
    def get(self):
        self.write("<html><body><h1>INFO/CS 4302 Homework 6</h1></body></html>")

class SchoolListHandler(BaseHandler):
    SUPPORTED_METHODS = ("GET", "POST")
    def get(self, format):
        Schools = self.db.list_Schools(self.base_uri)
        if format is None:
            respond_to_header(self, "/Schools")
        elif format == ".xml":
            self.set_header("Content-Type", "application/xml")
            self.render("School_list.xml", Schools=Schools)
        elif format == ".json":
            self.write(dict(Schools=Schools))
    
    def post(self, format):
        new_School = json.loads(self.request.body)
        new_School_id = self.db.create_School(new_School[1])
        self.set_status(201)
        self.set_header("Location", self.base_uri + "/Schools/" + new_School_id)

class MapHandler(BaseHandler):
    SUPPORTED_METHODS = ("POST")
    
    def get(self, School_id, format):
        self.set_header("Content-Type", "text/html")
        self.render("map.html")
    
    def post(self   ):
        location_list = json.loads(self.request.body)["locations"]
        center = {"latitude": sum([x["latitude"] for x in location_list])/ float(len(location_list)), 
                  "longitude": sum([x["longitude"] for x in location_list])/ float(len(location_list))}
        location_data = {"center": center, "locations": location_list}
        self.set_header("Content-Type", "text/html")
        self.render("map.html", location_data=location_data)

class SchoolResourceHandler(BaseHandler):
    SUPPORTED_METHODS = ("PUT", "GET", "DELETE")

    def get(self, School_id, format):
        School_resource = self.db.get_School(School_id, self.base_uri)
        if format is None:
            respond_to_header(self, "/Schools/%s"%School_id, True)
        elif format == ".html":
            self.set_header("Content-Type", "text/html")
            self.render("School.html", School=School_resource)
        elif format == ".xml":
            self.set_header("Content-Type", "application/xml")
            self.render("School.xml", School=School_resource)
        elif format == ".rdf":
            self.set_header("Content-Type", "application/rdf+xml")
            self.render("School.rdf", School=School_resource)
        elif format == ".ttl":
            self.set_header("Content-Type", "text/turtle")
            self.render("School.ttl", School=School_resource)
        elif format == ".json":
            self.write(School_resource) # Tornado handles JSON automatically

    def put(self, School_id, format):
        if School_id in self.db.Schools:
            print "Updating School %s" % School_id
            new_School = json.loads(self.request.body)
            self.db.update_School(School_id, new_School[1])
    
    def delete(self, School_id, format):
        if School_id in self.db.Schools:
            print "Deleting School %s" % School_id
            self.db.delete_School(School_id)

class QueryHandler(BaseHandler):
    
    def get(self, format):
        query_string = urlparse.parse_qs(self.request.query)['q'][0]
        results = self.db.find(query_string, self.base_uri)
        if format is None:
            redirect_uri = "search.json?q=%s" % query_string
            self.redirect(redirect_uri)
        elif format == ".xml":
            self.set_header("Content-Type", "application/xml")
            self.render("search-results.xml", results = results)
        elif format == ".json":
            self.write(dict(results=results))

### A dummy in-memory database implementation ###

class SchoolDatabase(object):
    """A dummy in-memory database for handling School data."""
    def __init__(self, Schools_csv, actors_csv, mapping_csv):
        print "Loading data into memory...."
        mapping_data = self.read_from_csv(mapping_csv)
        School_data = self.read_from_csv(Schools_csv)
        actor_data = self.read_from_csv(actors_csv)
        self.Schools = {}
        for School in School_data:
            self.Schools[School['id']] = School
            actors = [actor['actor_id'] for actor in mapping_data
                            if actor['School_id'] == School['id']]
            self.Schools[School['id']]['actors'] = actors
        self.actors = {}
        for actor in actor_data:
            self.actors[actor['id']] = actor
            Schools = [School['School_id'] for School in mapping_data
                            if School['actor_id'] == actor['id']]
            self.actors[actor['id']]['Schools'] = Schools
        
    # Simple regex search over all entities
    
    def find(self, query_string, base_uri):
        """Find entities matching a given query string"""
        results = []
        for actor in self.actors.values():
            if actor.has_key('name'):
               if re.search(query_string, actor['name'],
                            re.IGNORECASE) is not None:
                   print "found query string in actor name"
                   results.append(dict(type="actor",
                                 uri=base_uri + "/actors/" + actor['id']))
        for School in self.Schools.values():
            match = False
            if School.has_key('title'):
                if re.search(query_string, School['title'],
                   re.IGNORECASE) is not None:
                    match = True
            if School.has_key('synopsis'):
                if re.search(query_string, School['synopsis'],
                   re.IGNORECASE) is not None:
                    match = True
            if match:
                results.append(dict(type="School",
                              uri=base_uri + "/Schools/" + School['id']))                
        print "Found %d results for query %s" % (len(results), query_string)
        return results
    
    # ACTOR CRUD operations
    
    def get_actor(self, actor_id, base_uri):
        """Returns data about an actor with IDs converted to URIs"""
        actor = self.actors[actor_id]
        actor_resource = {}
        actor_resource['uri'] = base_uri + "/actors/" + actor_id
        if actor.has_key('name'):
            actor_resource['name'] = actor['name']
        if actor.has_key('birth_date'):
            actor_resource['birth_date'] = actor['birth_date']
        if actor.has_key('Schools'):
            actor_resource['Schools'] = [(base_uri + "/Schools/" + School_id)
                                        for School_id in actor['Schools']] 
        return actor_resource

    def list_actors(self, base_uri, School_id = None):
        """Returns a list of actors with IDs converted to URIs"""
        if School_id is None:
            actors = self.actors.values()
        else:
            actors = [actor for actor in self.actors.values()
                            if School_id in actor['Schools']]
        actor_list = []
        for actor in actors:
            entry = {}
            entry['uri'] = base_uri + "/actors/" + actor['id']
            if actor.has_key('name'):
                entry['name'] = actor['name']
            actor_list.append(entry)
        return actor_list
    
    # School CRUD operations
    def get_School(self, School_id, base_uri):
        """Returns data about a School with IDs converted to URIs"""
        School = self.Schools[School_id]
        School_resource = {}
        School_resource['uri'] = base_uri + "/Schools/" + School_id
        if School.has_key('title'):
            School_resource['title'] = School['title']
        if School.has_key('synopsis'):
            School_resource['synopsis'] = School['synopsis']
        if School.has_key('actors'):
            School_resource['actors'] = [(base_uri + "/actors/" + actor_id)
                                        for actor_id in School['actors']] 
        return School_resource

    def list_Schools(self, base_uri):
        """Returns a list of Schools with IDs converted to URIs"""
        School_list = []
        for School in self.Schools.values():
            entry = {}
            entry['uri'] = base_uri + "/Schools/" + School['id']
            if School.has_key('title'):
                entry['title'] = School['title']
            School_list.append(entry)
        return School_list

    def create_School(self, School):
        """Creates a new School and returns the assigned ID"""
        max_id = sorted([int(School_id) for School_id in self.Schools])[-1]
        new_id = str(max_id + 1)
        self.Schools[new_id] = School
        return new_id

    def update_School(self, School_id, School):
        """Updates a School with a given id"""
        self.Schools[School_id] = School
    
    def delete_School(self, School_id):
        """Deletes a School and references to this School"""
        del self.Schools[School_id]
        for actor in self.actors.values():
            if School_id in actor['Schools']:
                print "Deleting School reference from actor %s" % actor['id']
                actor['Schools'].remove(School_id)
    
    # Data import
    
    def read_from_csv(self, csv_file):
        """Reads CSV entries into a list containing a set of dictionaries.
        CSV header row entries are taken as dictionary keys"""
        data = []
        with codecs.open(csv_file, 'r', encoding='utf-8') as csvfile:
            header = None
            for i, line in enumerate(csvfile):
                line_split = [x.strip() for x in line.split("|")]
                line_data = [x for x in line_split if len(x) > 0]
                if i == 0:
                    header = line_data
                else:
                    entry = {}
                    for i,datum in enumerate(line_data):
                        entry[header[i]] = datum
                    data.append(entry)
        print "Loaded %d entries from %s" % (len(data), csv_file)
        return data
                    
### Script entry point ###

def main():
    tornado.options.parse_command_line()
    # Set up the database
#    db = SchoolDatabase(options.Schools, options.actors, options.mappings)
    # Set up the Web application, pass the database
    School_webservice = SchoolService()
    # Set up HTTP server, pass Web application
    try:
        http_server = tornado.httpserver.HTTPServer(School_webservice)
        http_server.listen(options.port)
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        print "\nStopping service gracefull..."
    finally:
        tornado.ioloop.IOLoop.instance().stop()

if __name__ == "__main__":
    main()