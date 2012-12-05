# INFO/CS 4302 Homework 8 submission

Name: Zach Silversmith
Netid: zbs7

## SPARQL Queries

1.
SELECT ?label WHERE {
?subject rdf:type <http://dbpedia.org/ontology/Film>.
?subject dbpedia2:director <http://dbpedia.org/resource/Alfred_Hitchcock>.
?subject rdfs:label ?label.
FILTER(lang(?label) = "en").
}

2. 
SELECT DISTINCT  ?abstract ?abstract2{
?subject <http://www.w3.org/1999/02/22-rdf-syntax-ns#type>	<http://dbpedia.org/class/yago/1980sHorrorFilms> .
?subject <http://dbpedia.org/ontology/abstract>?abstract.
filter(lang(?abstract)="en")
optional {?subject <http://dbpedia.org/ontology/abstract> ?abstract2.
          filter(lang(?abstract2)="es")}
} Limit 10

3.
SELECT DISTINCT  ?name ?birthdate{
?subject <http://www.w3.org/1999/02/22-rdf-syntax-ns#type>	<http://dbpedia.org/class/yago/FilmsDirectedByStanleyKuBrick> .
?subject <http://dbpedia.org/property/starring>	?actor .
?actor <http://dbpedia.org/property/name> ?name .
filter(lang(?name)="en")
optional {
 ?actor <http://dbpedia.org/ontology/birthDate>	?birthdate.
}
}

## Commands showing published linked data

curl -L -H "Accept: text/html" 127.0.0.1:8888/actors/1
curl -L -H "Accept: text/html" 127.0.0.1:8888/movies/1