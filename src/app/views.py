from flask import render_template, g, request, jsonify, make_response
from SPARQLWrapper import SPARQLWrapper
import requests
import json
from app import app

ENDPOINT_URL = 'http://localhost:5820/guidelines/query'
UPDATE_URL = 'http://localhost:5820/guidelines/update'

REASONING_TYPE = 'SL'


### This is old style, but leaving for backwards compatibility with earlier versions of Stardog
QUERY_HEADERS = {
                    'Accept': 'application/sparql-results+json',
                    'SD-Connection-String': 'reasoning={}'.format(REASONING_TYPE)
                }
                
UPDATE_HEADERS = {
    'Content-Type': 'application/sparql-update',
    'SD-Connection-String': 'reasoning={}'.format(REASONING_TYPE)
}
                
PREFIXES = "PREFIX tmr4i: <http://guidelines.data2semantics.org/vocab/>\n"

@app.route("/")
def index():
    return render_template('base.html')
    
    
@app.route('/getinference')
def inference():
    query = PREFIXES + """
    INSERT
    { 
        _:iir   a  tmr4i:InternalRecommendationInteraction .
        _:iir   tmr4i:relates ?r1 .
        _:iir   tmr4i:relates ?r2 .
        ?r1 tmr4i:interactsInternallyWith ?r2 .
        ?r2 tmr4i:interactsInternallyWith ?r1 .
        tmr4i:interactsInternallyWith a owl:ObjectProperty .
    } 
    WHERE
    { 
         ?r1  a  tmr4i:Recommendation .
         ?r1  a  owl:NamedIndividual .
         ?r2  a  tmr4i:Recommendation .
         ?r2  a  owl:NamedIndividual .
         ?r1  tmr4i:partOf  ?g .
         ?r2  tmr4i:partOf  ?g .
         ?g  a  owl:NamedIndividual .
         ?r1  tmr4i:recommends ?t1 .
         ?r2  tmr4i:recommends ?t2 .
         ?t1 a owl:NamedIndividual .
         ?t2 a owl:NamedIndividual .
     
         { 
             ?t1    tmr4i:similarToTransition ?t2 .
         }
         UNION
         {
             ?t1    tmr4i:inverseToTransition ?t2 .
         }
         UNION
         {
             ?ca    a tmr4i:CareActionType .
             ?t1    tmr4i:promotedBy ?t1 .
             ?t2    tmr4i:promotedBy ?t2 .
         }
         FILTER (?r1 != ?r2 && ?t1 != ?t2)
    } """
    
    result = sparql_update(query)
    
    return jsonify({'status': result})

    
@app.route('/getguidelines')
def guidelines():
    query = PREFIXES + "SELECT DISTINCT ?gl WHERE {?rec tmr4i:partOf ?gl . }";
    
    guidelines = sparql(query, strip=True)

    return render_template('guidelines_list.html',guidelines = guidelines)
    

@app.route('/getrecommendations', methods=['GET'])
def recommendations():
    uri = request.args.get('uri', '')
    query = PREFIXES + """
    SELECT DISTINCT ?rec ?crec ?irec WHERE 
    { 
        ?rec tmr4i:partOf <""" + uri + """>  . 
        ?rec a owl:NamedIndividual .
        OPTIONAL {
            ?rec tmr4i:interactsInternallyWith ?crec .
            ?crec a owl:NamedIndividual .
        }
        OPTIONAL {
            ?rec a ?irec .
            ?irec a owl:Class .
            FILTER(?irec = tmr4i:InternallyInteractingRecommendation)
        }
    }"""
    
    recommendations = sparql(query, strip=True)
    
    print recommendations
    
    return render_template('recommendations_list.html', recommendations = recommendations)

@app.route('/gettransitions', methods=['GET'])
def transitions():
    uri = request.args.get('uri', '')
    pos_query = PREFIXES + """
    SELECT DISTINCT * WHERE {
        <""" + uri + """> tmr4i:recommendsToPursue ?transition .
        ?transition tmr4i:hasTransformableSituation ?transformable_situation .
      	?transition tmr4i:hasExpectedPostSituation ?post_situation .
        ?transition a owl:NamedIndividual .
        ?transformable_situation a owl:NamedIndividual .
        ?post_situation a owl:NamedIndividual .
        OPTIONAL {
            ?transition tmr4i:hasFilterCondition ?f_condition .
            ?f_condition a owl:NamedIndividual .
        }
        OPTIONAL {
            ?transition tmr4i:inverseToTransition ?inverse_transition .
            ?inverse_transition a owl:NamedIndividual .
        }
        OPTIONAL {
            ?transition tmr4i:similarToTransition ?similar_transition .
            ?similar_transition a owl:NamedIndividual .
        }
        BIND(IF (bound(?f_condition), ?f_condition, "none") as ?filter_condition)
    }
    """

    neg_query = PREFIXES + """
    SELECT DISTINCT * WHERE {
        <""" + uri + """> tmr4i:recommendsToAvoid ?transition .
        ?transition tmr4i:hasTransformableSituation ?transformable_situation .
      	?transition tmr4i:hasExpectedPostSituation ?post_situation .
        ?transition a owl:NamedIndividual .
        ?transformable_situation a owl:NamedIndividual .
        ?post_situation a owl:NamedIndividual .
        OPTIONAL {
            ?transition tmr4i:hasFilterCondition ?f_condition .
            ?f_condition a owl:NamedIndividual .
        }
        OPTIONAL {
            ?transition tmr4i:inverseToTransition ?inverse_transition .
            ?inverse_transition a owl:NamedIndividual .
        }
        OPTIONAL {
            ?transition tmr4i:similarToTransition ?similar_transition .
            ?similar_transition a owl:NamedIndividual .
        }
        BIND(IF (bound(?f_condition), ?f_condition, "none") as ?filter_condition)

    }
    """

    pos_transitions = sparql(pos_query, strip=True)
    neg_transitions = sparql(neg_query, strip=True)
    
    return render_template('transitions_list.html', pos_transitions = pos_transitions, neg_transitions = neg_transitions)

@app.route('/getcare_actions', methods=['GET'])
def care_actions():
    uri = request.args.get('uri','')
    query = PREFIXES + """
        SELECT DISTINCT * WHERE {
            <"""+uri+"""> tmr4i:promotedBy ?ca .
            ?ca a owl:NamedIndividual .
        }
    """
    care_actions = sparql(query, strip=True)
    
    return render_template('care_actions.html', care_actions = care_actions)
    

def sparql_update(query, endpoint_url = UPDATE_URL):
    
    print query 
    
    result = requests.post(endpoint_url,params={'reasoning': REASONING_TYPE}, data=query, headers=UPDATE_HEADERS)
    
    return result.content

def sparql(query, strip=False, endpoint_url = ENDPOINT_URL, strip_prefix = 'http://guidelines.data2semantics.org/vocab/'):
    """This method replaces the SPARQLWrapper sparql interface, since SPARQLWrapper cannot handle the Stardog-style query headers needed for inferencing"""
    print query
    
    result = requests.get(endpoint_url,params={'query': query, 'reasoning': REASONING_TYPE}, headers=QUERY_HEADERS)
    result_dict = json.loads(result.content)
    print result_dict
    
    if strip:
        new_results = []
        for r in result_dict['results']['bindings']:
            new_result = {}
            for k, v in r.items():
                print k, v
                if v['type'] == 'uri' :
                    new_result[k+'_label'] = {}
                    new_result[k+'_label']['type'] = 'literal'
                    new_result[k+'_label']['value'] = v['value'].replace(strip_prefix,'')
                else :
                    new_result[k+'_label'] = {}
                    new_result[k+'_label']['type'] = 'literal'
                    new_result[k+'_label']['value'] = v['value']
                    
                new_result[k] = v
                    
            new_results.append(new_result)
                   
        print new_results
        return new_results
    else :
        return result_dict['results']['bindings']
    
    