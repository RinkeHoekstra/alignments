# from imp import load_source as load
# linkset = load("Linkset", "C:\Users\Al\PycharmProjects\Linkset\Linksets\Linkset.py")

import logging

import LensUtility as Lu
import Alignments.ErrorCodes as Ec
import Alignments.GenericMetadata as Gn
import Alignments.NameSpace as Ns
import Alignments.Query as Qry
import Alignments.Settings as St
import Alignments.UserActivities.UserRQ as Urq
from Alignments.Utility import write_to_file, update_specification

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
handler = logging.StreamHandler()
logger.addHandler(handler)

ERROR_CODE_11 = "DUE TO A SYSTEM ERROR, WE ARE UNABLE TO PROCESS YOUR REQUEST."


#################################################################
"""
    LENS BY UNION
"""
#################################################################

def run_checks(specs, query):

    print query


    # CHECK-1: CHECK WHETHER THE LENS EXIST BY ASKING ITS METADATA WHETHER IT IS COMPOSED OF THE SAME GRAPHS
    ask = Qry.sparql_xml_to_matrix(query)
    # print"ANSWER", ask


    # ASK IS NOT SUPPOSED TO BE NONE
    # CHECK-1-RESULT: PROBLEM CONNECTING WITH THE SERVER
    if ask is None:
        # print "IN 1"
        print Ec.ERROR_CODE_1
        return {St.message: Ec.ERROR_CODE_1, St.error_code: 1, St.result: None}

    # CHECK-1-RESULT: ASK HAS A RESULT, MEANING THE LENS EXIT UNDER THE SAME COMPOSITION OF GRAPHS
    elif ask[St.message] != "NO RESPONSE":
        # print "IN 2"
        if ask[St.result]:
            message = Ec.ERROR_CODE_7.replace("#", specs[St.lens]).replace("@", ask[St.result][1][0])
            print message
            return {St.message: message.replace("\n", "<br/>"), St.error_code: 1, St.result: specs[St.lens]}
        # ELSE
        # WITH THE UNSTATED ELSE, WE GET OUT AND PROCEED TO THE CREATION OF A NEW LENS
    else:
        # print "IN 3"
        print Ec.ERROR_CODE_1
        return {St.message: Ec.ERROR_CODE_1, St.error_code: 1, St.result: None}

    # print "GOT OUT!!!"
    # THE LENS <X> ALREADY EXISTS
    update_specification(specs)

    # CHECK-2: CHECK WHETHER THE ACTUAL LENS EXISTS UNDER THIS NAME
    check_02 = "\nASK {{ graph <{}> {{ ?S ?p ?o . }} }}".format(specs[St.lens])
    ask = Qry.boolean_endpoint_response(check_02)
    # print specs
    # print check_02
    # print ask

    # CHECK-2-RESULT: PROBLEM CONNECTING WITH THE SERVER
    if ask is None:
        # PROBLEM CONNECTING WITH THE SERVER
        print Ec.ERROR_CODE_1
        return {St.message: Ec.ERROR_CODE_1, St.error_code: 1, St.result: specs[St.lens]}

    # CHECK-2-RESULT: THE LINKSET ALREADY EXISTS
    if ask == "true":
        message = Ec.ERROR_CODE_6.replace("#", specs[St.lens])
        print message
        return {St.message: message.replace("\n", "<br/>"), St.error_code: 1, St.result: specs[St.lens]}


    return {St.message: "GOOD TO GO", St.error_code: 0, St.result: "GOOD TO GO"}


def union(specs, activated=False):

    if activated is False:
        # logger.warning("THE FUNCTION IS NOT ACTIVATED")
        print ("THE FUNCTION IS NOT ACTIVATED")
        return {St.message: "THE FUNCTION IS NOT ACTIVATED.", St.error_code: 1, St.result: None}

    print "\nEXECUTING UNION SPECS" \
          "\n======================================================" \
          "========================================================"

    """
    THE generate_lens_name FUNCTION RETURNS THE NAME OF THE UNION AND A
    QUERY THAT ALLOWS TO AS WHETHER THE LENS TO BE CREATED EXIST BY CHECKING
    WHETHER THERE EXISTS A LENS HAS THE SAME COMPOSITION IN TERMS GRAPHS USED FOR THE UNION
    """

    # SET THE NAME OF THE UNION-LENS
    info = Lu.generate_lens_name(specs[St.datasets])
    specs[St.lens] = "{}{}".format(Ns.lens, info["name"])

    # CHECK WHETHER THE LENS EXISTS
    check = run_checks(specs, info["query"])
    if check[St.result] != "GOOD TO GO":
        if check[St.message].__contains__("ALREADY EXISTS"):
            Urq.register_lens(specs, is_created=False)
        return check
    # print "AFTER CHECK"

    # PREPARATION FOR THE CREATION OF THE LENS
    specs[St.lens_target_triples] = ""
    specs[St.expectedTriples] = 0
    specs[St.insert_query] = ""
    lens = specs[St.lens]
    source = "{}{}".format(Ns.tmpgraph, "load00")
    message_2 = Ec.ERROR_CODE_8.replace("#", specs[St.lens])
    count = -1

    try:

        # GO THROUGH THE LINKSETS/LENSES IN THE LENS
        #   1-SUM UP THE EXPECTED NUMBER OF TRIPLES
        #   2-GENERATE THE TRIPLES REPRESENTATION OF GHE GRAPHS COMPOSING THIS LENS
        #   3-GENERATE THE INSERT QUERY FOR MOVING BOTH LINKSET AND SINGLETON GRAPHS TO THE UNION GRAPH
        for linkset in specs[St.datasets]:

            # print linkset
            count += 1

            # GET THE TOTAL NUMBER OF CORRESPONDENCE TRIPLES INSERTED
            curr_triples = Qry.get_triples(linkset)

            # print "Current triples: ", curr_triples
            if curr_triples is not None:
                # print "Current triples: ", curr_triples
                specs[St.expectedTriples] += int(curr_triples)
            else:
                # THE IS A PROBLEM WITH THE GRAPH FOR SEVERAL POSSIBLE REASONS
                return {St.message: message_2.replace("\n", "<br/>"), St.error_code: 1, St.result: None}

            # GENERATE TRIPLES OUT OF THE TARGETS
            specs[St.lens_target_triples] += "\n\t        void:target                         <{}> ;".format(linkset)

            # GET THE INSERT QUERY
            # BOTH THE LINKSET AND THE SINGLETONS ARE MOVED TO A SINGLE GRAPH
            partial_query = Qry.q_copy_graph(source, source, linkset)
            if count == 0:
                specs[St.insert_query] += partial_query
            else:
                specs[St.insert_query] += " ;\n{}".format(partial_query)

        # INTERSECTION MANIPULATION OVER THE UNION (SOURCE)
        insert_query = union_insert_q(lens, source, specs[St.lens_name])
        # print "manipulation:", manipulation
        specs[St.insert_query] += " ;\n{}".format(insert_query)

        # GENERATE THE LENS UNION
        if activated is True:

            # print data[St.insert_query]
            insert_ans = Qry.boolean_endpoint_response(specs[St.insert_query])

            specs[St.triples] = Qry.get_namedgraph_size(lens, isdistinct=False)
            if specs[St.triples] == "0":
                message = Ec.ERROR_CODE_9
                print message
                # return None
                return {St.message: message.replace("\n", "<br/>"), St.error_code: 1, St.result: None}

            # CHECK WHETHER THE RESULT CONTAINS DUPLICATES
            contains_duplicated = Qry. contains_duplicates(lens)
            print "contains_duplicated:", contains_duplicated

            # IF IT DOES, REMOVE THE DUPLICATES
            if contains_duplicated is True:
                # logger.warning("THE LENS CONTAINS DUPLICATES.")
                print "THE LENS CONTAINS DUPLICATES."
                Qry.remove_duplicates(lens)
                # logger.warning("THE DUPLICATES ARE NOW REMOVED.")
                print "THE DUPLICATES ARE NOW REMOVED."

            specs[St.triples] = Qry.get_namedgraph_size(lens, isdistinct=False)
            print "\t>>> INSERTED:  {}\n\t>>> INSERTED TRIPLES: {}".format(insert_ans, specs[St.triples])

            # LOAD THE METADATA
            inserted_correspondences = int(Qry.get_union_triples(lens))
            specs[St.removedDuplicates] = specs[St.expectedTriples] - inserted_correspondences
            metadata = Gn.union_meta(specs)
            meta_ans = Qry.boolean_endpoint_response(metadata)
            print "\t>>> Is the metadata generated and inserted?  {}".format(meta_ans)

        construct_response = Qry.get_constructed_graph(specs[St.lens])
        if construct_response is not None:
            print "\t>>> WRITING TO FILE"
            construct_response = construct_response.replace('{', "<{}>\n{{".format(specs[St.lens]), 1)
            write_to_file(graph_name=specs[St.lens_name], metadata=None, correspondences=construct_response)
        print "\tLens created as : ", specs[St.lens]
        print "\t*** JOB DONE! ***"

        # REGISTER THE LINKSET
        Urq.register_lens(specs, is_created=True)

        # return specs[St.lens]
        message = "THE LENS WAS CREATED!<br/>URI = {}".format(specs[St.lens])
        return {St.message: message, St.error_code: 0, St.result: specs[St.lens]}

    except Exception as err:
        # logger.warning(err)
        print "ERROR IN UNION LENS CREATION", err
        return {St.message: ERROR_CODE_11, St.error_code: 11, St.result: None}


def union_insert_q(lens, source, label):

    query = """
    PREFIX prov:<{0}>
    PREFIX tmpgraph:<{1}>
    PREFIX tmpvocab:<{5}>
    ###### CREATING THE INTERSECTION CORRESPONDENCES
    ###### WITH A TEMPORARY PREDICATE
    INSERT
    {{
      GRAPH tmpgraph:load01
      {{
        ?sCorr 		tmpvocab:predicate		?oCorr  .
      }}
    }}
    WHERE
    {{
      graph <{2}>
      {{
        ?sCorr		?singCorr 				?oCorr  .
        FILTER NOT EXISTS {{ ?x ?sCorr ?z }}
        #?singCorr	?singCorrPr 			?singCorrobj .
      }}
    }} ;

    ###### UPDATE tmpgraph:load01 WITH UNIQUE PREDICATES
    INSERT
    {{
      GRAPH tmpgraph:load02
      {{
        ?sCorr ?singPre ?oCorr .
      }}
    }}
    WHERE
    {{
      GRAPH tmpgraph:load01
      {{
        ?sCorr ?y ?oCorr .

        ### Create A SINGLETON URI"
        BIND( replace("{3}union_#", "#", STRAFTER(str(UUID()),"uuid:")) as ?pre )
        BIND(iri(?pre) as ?singPre)
      }}
    }} ;

    INSERT
    {{
        GRAPH <{4}>
        {{
            ?sCorr			?singPre 					?oCorr .
            ?singPre		prov:wasDerivedFrom 	    ?singCorr .
            ?singCorr		?singCorrPr 				?singCorrobj .
        }}
    }}
    WHERE
    {{
        GRAPH tmpgraph:load02
        {{
            ?sCorr			?singPre 					?oCorr .
        }}

        graph <{2}>
        {{
            ?sCorr				?singCorr 				?oCorr  .
            OPTIONAL {{ ?singCorr			?singCorrPr 			?singCorrobj .  }}
            FILTER NOT EXISTS {{ ?x ?sCorr ?z }}
        }}
    }} ;

    DROP SILENT GRAPH tmpgraph:load00 ;
    DROP SILENT GRAPH tmpgraph:load01 ;
    DROP SILENT GRAPH tmpgraph:load02
    """.format(Ns.prov, Ns.tmpgraph, source, Ns.alivocab, lens, Ns.tmpvocab  )
    return query

