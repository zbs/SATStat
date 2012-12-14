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
import urllib

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

from gdata.spreadsheet.service import SpreadsheetsService
import gdata.spreadsheet.text_db
import gdata.docs
import gdata.docs.service
import gdata.spreadsheet.service

from tornado.options import define, options
from tornado.web import RequestHandler

define("port", default=8888, help="run on the given port", type=int)

### School Web Service implementation ###

type_to_extension = {"application/xml" : "xml", "text/html" : "html", \
                     "application/json" : "json"}

def respond_to_header(handler, redirect_uri, support_html=False):
    accept_format = handler.request.headers["Accept"]
    if not accept_format or accept_format == '*/*':
        accept_format = 'application/json'
        
    if 'text/html' in accept_format:
        handler.redirect(redirect_uri+".html", status=303)
    elif accept_format not in type_to_extension:
        handler.write_error(401, message="Content type %s not supported"%accept_format)
    elif accept_format == 'text/html' and not support_html:
        handler.write_error(401, message="HTML not supported for this use case")
    else:
        extension = type_to_extension[accept_format]
        handler.redirect(redirect_uri+".%s"%extension, status=303)

class SchoolService(tornado.web.Application):
    """The School Service Web Application"""
    def __init__(self, db):
        static_path = os.path.join(os.getcwd(), 'static')
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            debug=True,
            autoescape=None,
            static_path= static_path
        )
        handlers = [
            (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': static_path}),
            (r"/", HomeHandler),
            (r"/schools(\..+)?", SchoolListHandler),
            (r"/regions/(\w+)(\..+)?", RegionHandler),
            (r"/regions(\..+)?", BrowseHandler),
            (r"/schools/(\d+)(\..+)?", SchoolResourceHandler),
            (r"/about", AboutHandler),
            (r"/search(\..+)?", QueryHandler),
            (r".*", PageNotFoundHandler),
        ]
        
        tornado.web.Application.__init__(self, handlers, **settings)
        self.db = db
        
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

class PageNotFoundHandler(BaseHandler):
    def get(self):
        self.write("<h1>Page not found</h1>")

class RegionHandler(BaseHandler):
    def get(self, region_name, format):
        if format is None:
            respond_to_header(self, "/regions/%s"%region_name, True)
            return 
        
        region_name = region_name.replace("_", " ")
        if format == ".html":
            self.set_header("Content-Type", "text/html")
            self.render("region.html", result={"name":region_name})
        else:
            self.write_error(401, message="Format %s is not supported"%format)
            
class BrowseHandler(BaseHandler):
    def get(self, format):
        self.render("regions.html")
        
class AboutHandler(BaseHandler):
    def get(self):
        self.render("about.html")
        
class HomeHandler(BaseHandler):
    def get(self):
        self.render("graph.html")

class SchoolListHandler(BaseHandler):
    SUPPORTED_METHODS = ("GET", "POST")
    def get(self, format):
        if format is None:
            respond_to_header(self, "/schools")
            return 
        
        if format == ".html":
            self.set_header("Content-Type", "text/html")
            self.render("schools.html")
        else:
            Schools = self.db.list_Schools(self.base_uri)
            if format == ".xml":
                self.set_header("Content-Type", "application/xml")
                self.render("Schools.xml", results=Schools)
            elif format == ".json":
                self.write(dict(Schools=Schools))
            else:
                self.write_error(401, message="Unsupported format")
    
    def post(self, format):
        new_School = json.loads(self.request.body)
        new_School_id = self.db.create_School(new_School[1])
        self.set_status(201)
        self.set_header("Location", self.base_uri + "/schools/" + new_School_id)
        
class SchoolResourceHandler(BaseHandler):
    SUPPORTED_METHODS = ("GET")

    def get(self, School_id, format):
        school_resource = self.db.get_School(School_id, self.base_uri)
        if format is None:
            respond_to_header(self, "/schools/%s"%School_id, True)
        elif format == ".html":
            self.set_header("Content-Type", "text/html")
            self.render("school.html", result=school_resource)
        elif format == ".xml":
            self.set_header("Content-Type", "application/xml")
            self.render("school.xml", school=school_resource)
        elif format == ".json":
            self.write(school_resource) # Tornado handles JSON automatically
        else:
            self.write_error(401, message="Format %s is not supported"%format)

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
    def __init__(self):
        
        self.key = '0AqApqrIj0J-EdFRmV0RHQUFydk9mSzFMQ1hpNGE3aHc'
        self.client = SpreadsheetsService()
        
    
    def search(self, query):
        #        results = []
#        for actor in self.actors.values():
#            if actor.has_key('name'):
#               if re.search(query_string, actor['name'],
#                            re.IGNORECASE) is not None:
#                   print "found query string in actor name"
#                   results.append(dict(type="actor",
#                                 uri=base_uri + "/actors/" + actor['id']))
#        for School in self.Schools.values():
#            match = False
#            if School.has_key('title'):
#                if re.search(query_string, School['title'],
#                   re.IGNORECASE) is not None:
#                    match = True
#            if School.has_key('synopsis'):
#                if re.search(query_string, School['synopsis'],
#                   re.IGNORECASE) is not None:
#                    match = True
#            if match:
#                results.append(dict(type="School",
#                              uri=base_uri + "/Schools/" + School['id']))                
#        print "Found %d results for query %s" % (len(results), query_string)
        pass
    
    def find(self, query=None, base_uri=None):
        
        if not query:
            feed = self.client.GetListFeed(self.key, visibility='public', projection='values')
        else:
            feed = self.client.GetListFeed(self.key, query=query, visibility='public', projection='values')

        results = []
        for row_entry in feed.entry:
            results.append(gdata.spreadsheet.text_db.Record(row_entry=row_entry).content)
            
        return results

    def get_region(self, region_name, base_uri):
        query = gdata.spreadsheet.service.ListQuery()
        query.sq = "city = '%s'"%region_name
        
        schools = self.find(query=query)
        
        if not schools:
            return None
        
        def get_school_item(row):
            name = row['schoolname']
            nces_id = row['nces']
            uri = base_uri + "/schools/%s"%nces_id
            return {'name': name, 'uri': uri}
        
        entries = map(get_school_item, schools)
        not_numerical_keys = {'dbn', 'schoolname', 'nces', 'schooltype', 'address', \
                              'city', 'state', 'zipcode', 'latitude', 'longitude', \
                              'charterschool', 'magnetschool'}
        valid_keys = (set(schools[0].keys()) - not_numerical_keys)
        averages = {key:0 for key in valid_keys}
        
        def get_number(s):
            try:
                f = float(s)
                return f
            except ValueError:
                return 0.
        
        for key in valid_keys:
            averages[key] = sum([get_number(entry[key]) for entry in schools])
            
        averages = {'average%s'%key: averages[key] for key in averages}
        averages["schools"] = entries
        return averages
        
            
    
    # School CRUD operations
    def get_School(self, School_id, base_uri=None):
        query = gdata.spreadsheet.service.ListQuery()
        query.sq = "nces = %s"%School_id
        return self.find(query=query)[0]

    def list_Schools(self, base_uri):
        schools = self.find()
        
        def get_school_item(row):
            name = row['schoolname']
            nces_id = row['nces']
            uri = base_uri + "/schools/%s"%nces_id
            return {'name': name, 'uri': uri}
                    
        return {'schools': [get_school_item(row) for row in schools]}
### Script entry point ###

def main():
    tornado.options.parse_command_line()
    # Set up the database
    db = SchoolDatabase()
    # Set up the Web application, pass the database
    School_webservice = SchoolService(db)
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