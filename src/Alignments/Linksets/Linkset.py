# encoding=utf-8

# https://appear.in/risis-meeting
# from SparqlRequests import jrc_names
# from JRCNameLinker import links
# import SPARQLWrapper
# https://github.com/KRRVU/linksets
# https://www.sourcetreeapp.com/
# url = b"http://{}:{}/annex/{}/sparql/query?".format("localhost", "5820", "linkset")
# url = b"http://{}/annex/{}/sparql/query?".format("stardog.risis.d2s.labs.vu.nl", "risis")

import codecs
import datetime
import logging
import os

from kitchen.text.converters import to_unicode

import Alignments.ErrorCodes as Ec
import Alignments.Lenses.LensUtility as Lu
import Alignments.NameSpace as Ns
import Alignments.Query as Qry
import Alignments.Settings as St
import Alignments.UserActivities.UserRQ as Ura
from Alignments.CheckRDFFile import check_rdf_file

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
handler = logging.StreamHandler()
logger.addHandler(handler)

linksetpath = "E:\datasets\Linksets"
write_to_path = "C:\Users\Al\Dropbox\Linksets\ExactName"


#################################################################
"""
    LINKSETS
"""
#################################################################


def set_linkset_name(specs, inverse=False):

    if inverse is False:

        h_name = specs[St.mechanism] + \
                 specs[St.source][St.graph_name] + specs[St.source][St.aligns_name] + \
                 specs[St.target][St.graph_name] + specs[St.target][St.aligns_name]

        hashed = hash(h_name)

        append = str(hashed).replace("-", "N") if str(hashed).__contains__("-") else "P{}".format(hashed)

        specs[St.linkset_name] = "{}_{}_{}_{}_{}".format(
            specs[St.source][St.graph_name], specs[St.target][St.graph_name],
            specs[St.mechanism], specs[St.source][St.aligns_name], append)

        specs[St.linkset] = "{}{}".format(Ns.linkset, specs[St.linkset_name])

        return specs[St.linkset]

    else:

        h_name = specs[St.mechanism] + \
                 specs[St.target][St.graph_name] + specs[St.target][St.aligns_name] + \
                 specs[St.source][St.graph_name] + specs[St.source][St.aligns_name]

        hashed = hash(h_name)

        append = str(hashed).replace("-", "N") if str(hashed).__contains__("-") else "P{}".format(hashed)

        specs[St.linkset_name] = "{}_{}_{}_{}_{}".format(
            specs[St.target][St.graph_name], specs[St.source][St.graph_name],
            specs[St.mechanism], specs[St.target][St.aligns_name], append)

        specs[St.linkset] = "{}{}".format(Ns.linkset, specs[St.linkset_name])

        return specs[St.linkset]


def set_linkset_identity_name(specs, inverse=False):

    if inverse is False:

        h_name = specs[St.mechanism] + specs[St.source][St.graph_name] + specs[St.target][St.graph_name]

        hashed = hash(h_name)

        append = str(hashed).replace("-", "N") if str(hashed).__contains__("-") else "P{}".format(hashed)

        specs[St.linkset_name] = "{}_{}_{}_{}".format(
            specs[St.source][St.graph_name], specs[St.target][St.graph_name], specs[St.mechanism], append)

        specs[St.linkset] = "{}{}".format(Ns.linkset, specs[St.linkset_name])

        return specs[St.linkset]

    else:

        h_name = specs[St.mechanism] + specs[St.target][St.graph_name] + specs[St.source][St.graph_name]

        hashed = hash(h_name)

        append = str(hashed).replace("-", "N") if str(hashed).__contains__("-") else "P{}".format(hashed)

        specs[St.linkset_name] = "{}_{}_{}_{}".format(
            specs[St.target][St.graph_name], specs[St.source][St.graph_name], specs[St.mechanism], append)

        specs[St.linkset] = "{}{}".format(Ns.linkset, specs[St.linkset_name])

        return specs[St.linkset]


def set_subset_name(specs, inverse=False):

    if inverse is False:

        h_name = specs[St.mechanism] + \
                 specs[St.source][St.graph_name] + specs[St.source][St.link_old_name] + \
                 specs[St.target][St.graph_name]

        hashed = hash(h_name)

        append = str(hashed).replace("-", "N") if str(hashed).__contains__("-") else "P{}".format(hashed)

        specs[St.linkset_name] = "subset_{}_{}_{}_{}_{}".format(
            specs[St.source][St.graph_name], specs[St.target][St.graph_name],
            specs[St.mechanism], specs[St.source][St.link_old_name], append)

        specs[St.linkset] = "{}{}".format(Ns.linkset, specs[St.linkset_name])

        # print specs[St.linkset]

        return specs[St.linkset]


def set_refined_name(specs):
    specs[St.refined_name] = "refined_{}_{}_{}".format(
        specs[St.linkset_name], specs[St.mechanism], specs[St.source][St.aligns_name])
    specs[St.refined] = specs[St.linkset].replace(specs[St.linkset_name], specs[St.refined_name])


def run_checks(specs):

    heading = "\n======================================================" \
              "========================================================"\
              "\nRUNNING LINKSET SPECS CHECK" \
              "\n======================================================" \
              "========================================================"
    print heading

    ask = "ASK {{ <#> ?p ?o . }}"

    linkset = specs[St.refined] if St.refined in specs else specs[St.linkset]
    # print linkset

    """
    # CHECK WHETHER THE SOURCE & TARGET GRAPHS EXIST
    """
    g_exist_q = "ASK { GRAPH <@> {?s ?p ?o} }"
    src_g_exist = Qry.boolean_endpoint_response(g_exist_q.replace("@", specs[St.source][St.graph]))
    trg_g_exist = Qry.boolean_endpoint_response(g_exist_q.replace("@", specs[St.target][St.graph]))
    if (src_g_exist == "false") or (trg_g_exist == "false"):
        print Ec.ERROR_CODE_10
        return {St.message: Ec.ERROR_CODE_10, St.error_code: 10, St.result: None}

    """
    # CHECK THE TASK SPECIFIC PREDICATE COUNT
    """
    if specs[St.sameAsCount] is None:
        print Ec.ERROR_CODE_1
        return {St.message: Ec.ERROR_CODE_1, St.error_code: 1, St.result: None}

    """
    # CHECK WHETHER THE LINKSET WAS ALREADY CREATED AND ITS ALTERNATIVE NAME REPRESENTATION
    """

    # CHECK WHETHER THE CURRENT LINKSET NAME EXIST
    ask_1 = Qry.boolean_endpoint_response(ask.replace("#", linkset))
    if ask_1 == "true":

        print "ASK_1"
        message = Ec.ERROR_CODE_2.replace('#', linkset)

        if St.refined in specs:

            # GET LINKSET DERIVED FROM
            subjects_target = linkset_wasderivedfrom(linkset)
            # CHECK THE RESULT OF THE DIFFERENCE AND OUT PUT BOTH THE REFINED AND THE DIFFERENCE
            if subjects_target is not None:

                diff_lens_specs = {
                    St.researchQ_URI: specs[St.researchQ_URI],
                    # THE OBJECT IS THE LINKSET THE REFINED LINKSET WAS DERIVED FROM
                    St.subjectsTarget: subjects_target,
                    # THE TARGET IS THE REFINED LINKSET
                    St.objectsTarget: linkset
                }

                Lu.diff_lens_name(diff_lens_specs)
                message2 = Ec.ERROR_CODE_7.replace('#', diff_lens_specs[St.lens])
                refined = {St.message: message, St.error_code: 0, St.result: linkset}
                difference = {St.message: message2, St.error_code: 7, St.result: diff_lens_specs[St.lens]}

                # REGISTER THE ALIGNMENT
                if refined[St.message].__contains__("ALREADY EXISTS"):
                    Ura.register_alignment_mapping(specs, created=False)
                else:
                    Ura.register_alignment_mapping(specs, created=True)

                # REGISTER THE LENS
                Ura.register_lens(diff_lens_specs, is_created=False)

                print "\n>>> NOT GOOD TO GO, IT ALREADY EXISTS"
                return {St.message: "NOT GOOD TO GO", 'refined': refined, 'difference': difference}
        print message
        return {St.message: message.replace("\n", "<br/>"), St.error_code: 2, St.result: linkset}

    # CHECK WHETHER THE alternative LINKSET NAME EXIST
    elif  ask_1 == "false" and str(linkset).__contains__("subset") is False:

        print "ASK 2"
        if St.refined not in specs:

            # GENERATE ALTERNATIVE NAME. THIS DOS NOT APPLY JTO SUBSET BECAUSE WE ASSUME
            # A LINKSET BY SUBSET DOES NEEDS NOT THE TARGET ALIGNS TO BE SET AS IT IS OFTEN UNKNOWN
            counter_check = set_linkset_name(specs, inverse=True)

            # CHECK WHETHER THE CURRENT LINKSET EXIST UNDER A DIFFERENT NAME
            ask_2 = Qry.boolean_endpoint_response(ask.replace("#", counter_check))

            if ask_2 == "true":
                message = Ec.ERROR_CODE_3.replace('#', linkset).replace("@", counter_check)
                print "\n>>> NOT GOOD TO GO, IT ALREADY EXISTS UNDER THE NAME {}".format(counter_check)
                print message
                return {St.message: message.replace("\n", "<br/>"), St.error_code: 3, St.result: counter_check}

    print "NO PROBLEM"
    set_linkset_name(specs, inverse=False)
    print "\n>>> GOOD TO GO !!!"
    return {St.message: "GOOD TO GO", St.error_code: 0, St.result: "GOOD TO GO"}


def run_checks_id(specs):

    heading = "\n======================================================" \
              "========================================================"\
              "\nRUNNING LINKSET SPECS CHECK" \
              "\n======================================================" \
              "========================================================"
    print heading

    ask = "ASK {{ <#> ?p ?o . }}"

    linkset = specs[St.refined] if St.refined in specs else specs[St.linkset]
    # print linkset

    """
    # CHECK WHETHER THE SOURCE & TARGET GRAPHS EXIST
    """
    g_exist_q = "ASK { GRAPH <@> {?s ?p ?o} }"
    src_g_exist = Qry.boolean_endpoint_response(g_exist_q.replace("@", specs[St.source][St.graph]))
    trg_g_exist = Qry.boolean_endpoint_response(g_exist_q.replace("@", specs[St.target][St.graph]))
    if (src_g_exist == "false") or (trg_g_exist == "false"):
        print Ec.ERROR_CODE_10
        return {St.message: Ec.ERROR_CODE_10, St.error_code: 10, St.result: None}

    """
    # CHECK THE TASK SPECIFIC PREDICATE COUNT
    """
    if specs[St.sameAsCount] is None:
        print Ec.ERROR_CODE_1
        return {St.message: Ec.ERROR_CODE_1, St.error_code: 1, St.result: None}

    """
    # CHECK WHETHER THE LINKSET WAS ALREADY CREATED AND ITS ALTERNATIVE NAME REPRESENTATION
    """

    # CHECK WHETHER THE CURRENT LINKSET NAME EXIST
    ask_1 = Qry.boolean_endpoint_response(ask.replace("#", linkset))
    if ask_1 == "true":

        print "ASK_1"
        message = Ec.ERROR_CODE_2.replace('#', linkset)

        if St.refined in specs:

            # GET LINKSET DERIVED FROM
            subjects_target = linkset_wasderivedfrom(linkset)
            # CHECK THE RESULT OF THE DIFFERENCE AND OUT PUT BOTH THE REFINED AND THE DIFFERENCE
            if subjects_target is not None:

                diff_lens_specs = {
                    St.researchQ_URI: specs[St.researchQ_URI],
                    # THE OBJECT IS THE LINKSET THE REFINED LINKSET WAS DERIVED FROM
                    St.subjectsTarget: subjects_target,
                    # THE TARGET IS THE REFINED LINKSET
                    St.objectsTarget: linkset
                }

                Lu.diff_lens_name(diff_lens_specs)
                message2 = Ec.ERROR_CODE_7.replace('#', diff_lens_specs[St.lens])
                refined = {St.message: message, St.error_code: 0, St.result: linkset}
                difference = {St.message: message2, St.error_code: 7, St.result: diff_lens_specs[St.lens]}

                # REGISTER THE ALIGNMENT
                if refined[St.message].__contains__("ALREADY EXISTS"):
                    Ura.register_alignment_mapping(specs, created=False)
                else:
                    Ura.register_alignment_mapping(specs, created=True)

                # REGISTER THE LENS
                Ura.register_lens(diff_lens_specs, is_created=False)

                print "\n>>> NOT GOOD TO GO, IT ALREADY EXISTS"
                return {St.message: "NOT GOOD TO GO", 'refined': refined, 'difference': difference}
        print message
        return {St.message: message.replace("\n", "<br/>"), St.error_code: 2, St.result: linkset}

    # CHECK WHETHER THE alternative LINKSET NAME EXIST
    elif  ask_1 == "false" and str(linkset).__contains__("subset") is False:

        print "ASK 2"
        if St.refined not in specs:

            # GENERATE ALTERNATIVE NAME. THIS DOS NOT APPLY JTO SUBSET BECAUSE WE ASSUME
            # A LINKSET BY SUBSET DOES NEEDS NOT THE TARGET ALIGNS TO BE SET AS IT IS OFTEN UNKNOWN
            counter_check = set_linkset_identity_name(specs, inverse=True)

            # CHECK WHETHER THE CURRENT LINKSET EXIST UNDER A DIFFERENT NAME
            ask_2 = Qry.boolean_endpoint_response(ask.replace("#", counter_check))

            if ask_2 == "true":
                message = Ec.ERROR_CODE_3.replace('#', linkset).replace("@", counter_check)
                print "\n>>> NOT GOOD TO GO, IT ALREADY EXISTS UNDER THE NAME {}".format(counter_check)
                print message
                return {St.message: message.replace("\n", "<br/>"), St.error_code: 3, St.result: counter_check}

    print "NO PROBLEM"
    set_linkset_identity_name(specs, inverse=False)
    print "NAME: " + specs[St.linkset]
    print "\n>>> GOOD TO GO !!!"
    return {St.message: "GOOD TO GO", St.error_code: 0, St.result: "GOOD TO GO"}


def linkset_info(specs, same_as_count):
    info = "{}{}{}{}{}{}". \
        format("======================================================="
               "=======================================================\n",
               "Results for creating the linkset between {} and {}.\n".format(
                   specs[St.source][St.graph_name], specs[St.target][St.graph_name]),

               "\t   Linksets GRAPH            : linkset:{}\n".format(specs[St.linkset_name]),

               "\t   Metadata GRAPH            : lsMetadata:{}\n".format(specs[St.linkset_name]),

               "\t   Singleton Metadata GRAPH  : singMetadata:{}\n".format(specs[St.linkset_name]),

               "\t   LINKTYPE                  : alivocab:{}{}\n".format(specs[St.mechanism], same_as_count))
    return info


def refined_info(specs, same_as_count):

    info = "{}{}{}{}{}". \
        format("======================================================="
               "=======================================================\n",
               "Results for refining  linkset:{}.\n".format(specs[St.linkset_name]),

               "\t   Refined Linksets GRAPH    : linkset:{}\n".format(specs[St.refined_name]),

               "\t   Singleton GRAPH           : singMetadata:{}\n".format(specs[St.refined_name]),

               "\t   LINKTYPE                  : alivocab:{}{}\n".format(specs[St.mechanism], same_as_count))
    return info


def writelinkset(source, target, linkset_graph_name, outputs_path, metadata_triples):

    # print "CALL A CONSTRUCT ON: {}".format(linkset_graph_name)

    linkset_query = "\n{}\n{}\n{}\n{}\n\n{}\n{}\n\n".format(
        "PREFIX linkset: <{}>".format(Ns.linkset),
        "PREFIX {}: <{}>".format(source[0], source[2]),
        "PREFIX predicate: <{}>".format(Ns.alivocab),
        "PREFIX {}: <{}>".format(target[0], target[2]),
        "construct { ?x ?y ?z }",
        "where     {{ graph linkset:{} {{ ?x ?y ?z }} }}".format(linkset_graph_name),
    )

    # print linkset_query

    singleton_metadata_query = "\n{}\n{}\n{}\n{}\n\n{}\n{}\n{}\n\n".format(
        "PREFIX singMetadata:   <{}>".format(Ns.singletons),
        "PREFIX predicate:      <{}>".format(Ns.alivocab),
        "PREFIX rdf:            <{}>".format(Ns.rdf),
        "PREFIX {}:             <{}>".format(source[0], source[2]),
        "PREFIX {}:             <{}>".format(target[0], target[2]),
        "construct { ?x ?y ?z }",
        "where     {{ graph <{}{}> {{ ?x ?y ?z }} }}".format(Ns.singletons, linkset_graph_name),
    )
    # print singleton_metadata_query

    """
        1. RUN SPARQL CONSTRUCT QUERIES AGAINST ENDPOINT
    """
    linkset_construct = Qry.endpointconstruct(linkset_query)
    if linkset_construct is not None:
        linkset_construct = linkset_construct.replace('{', "linkset:{}\n{{".format(linkset_graph_name), 1)

    singleton_metadata_construct = Qry.endpointconstruct(singleton_metadata_query)
    if singleton_metadata_construct is not None:
        singleton_metadata_construct = singleton_metadata_construct.\
            replace('{', "singMetadata:{}\n{{".format(linkset_graph_name), 1)

    """
        2. FILE NAME SETTINGS
    """
    date = datetime.date.isoformat(datetime.date.today()).replace('-', '')
    dir_name = outputs_path  # os.path.dirname(f_path)
    linkset_file = "{}(Linksets)-{}.trig".format(linkset_graph_name, date)
    metadata_file = "{}(Metadata)-{}.trig".format(linkset_graph_name, date)
    singleton_metadata_file = "{}(SingletonMetadata)-{}.trig".format(linkset_graph_name, date)
    dir_name = dir_name.replace("\\", "/")
    linkset_output = "{}/{}".format(dir_name, linkset_file)
    metadata_output = "{}/{}".format(dir_name, metadata_file)
    singleton_metadata_output = "{}/{}".format(dir_name, singleton_metadata_file)
    try:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
    except OSError as err:
        print "\n\t[__init__ in RDF]", err
        return
    # print "output file is :\n\t{}".format(output_path)

    """
        3. WRITE LINKSET TO FILE
    """
    linkset_disc = codecs.open(linkset_output, "wb", "utf-8")
    if linkset_construct is not None:
        linkset_disc.write(linkset_construct)
    linkset_disc.close()

    """
        4. WRITE METADATA TO FILE
    """
    metadata_disc = codecs.open(metadata_output, "wb", "utf-8")
    metadata_disc.write(metadata_triples.replace("INSERT DATA", "") + "\n\n")
    metadata_disc.close()

    """
        5. WRITE SINGLETON METADATA TO FILE
    """
    sing_metadata_disc = codecs.open(singleton_metadata_output, "wb", "utf-8")
    if singleton_metadata_construct is not None:
        sing_metadata_disc.write(to_unicode(singleton_metadata_construct) + "\n\n")
    sing_metadata_disc.close()

    """
        6. CHECK THE WRITTEN FILES
    """
    check_rdf_file(linkset_output)
    check_rdf_file(metadata_output)


def linkset_wasderivedfrom(refined_linkset_uri):
    query = """
    select *
    {{
        <{}>
            <http://www.w3.org/ns/prov#wasDerivedFrom> ?wasDerivedFrom .
    }}
    """.format(refined_linkset_uri)
    # print query
    dictionary_result = Qry.sparql_xml_to_matrix(query)
    # print dictionary_result
    # print dictionary_result
    if dictionary_result:
        if dictionary_result[St.result]:
            return dictionary_result[St.result][1][0]
    return None


